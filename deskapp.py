import os
import sys
import time
from datetime import datetime
import logging
import tempfile
import socketserver
import subprocess as sps
from inspect import isfunction
from threading import Lock, Thread


logging.basicConfig(level=logging.INFO,
                    format='flaskwebgui - [%(levelname)s] - %(message)s')


def find_chrome_win():

    # using edge by default since it's build on chromium
    edge_path = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if os.path.exists(edge_path):
        return edge_path

    import winreg as reg
    reg_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe'

    chrome_path = None
    last_exception = None

    for install_type in reg.HKEY_CURRENT_USER, reg.HKEY_LOCAL_MACHINE:
        try:
            reg_key = reg.OpenKey(install_type, reg_path, 0, reg.KEY_READ)
            chrome_path = reg.QueryValue(reg_key, None)
            reg_key.Close()
        except WindowsError as e:
            last_exception = e
        else:
            if chrome_path and len(chrome_path) > 0:
                break

    # Only log some debug info if we failed completely to find chrome
    if not chrome_path:
        logging.exception(last_exception)
        logging.error("Failed to detect chrome location from registry")
    else:
        logging.info(f"Chrome path detected as: {chrome_path}")

    return chrome_path


def get_default_chrome_path():
    if sys.platform in ['win32', 'win64']:
        return find_chrome_win()


current_timestamp = None


class FlaskUI:

    def __init__(self,
                 app,
                 start_server='flask',
                 host='127.0.0.1',
                 port=None,
                 width=800,
                 height=600,
                 maximized=False,
                 fullscreen=False,
                 browser_path=None,
                 socketio=None,
                 on_exit=None,
                 idle_interval=5,
                 close_server_on_exit=True
                 ) -> None:

        self.app = app
        self.start_server = str(start_server).lower()
        self.host = host
        self.port = port
        self.width = str(width)
        self.height = str(height)
        self.fullscreen = fullscreen
        self.maximized = maximized
        self.browser_path = browser_path if browser_path else get_default_chrome_path()
        self.socketio = socketio
        self.on_exit = on_exit
        self.idle_interval = idle_interval
        self.close_server_on_exit = close_server_on_exit

        self.set_url()

        self.webserver_dispacher = {
            "flask": self.start_flask,
            "flask-socketio": self.start_flask_socketio,
            "django": self.start_django,
            "fastapi": self.start_fastapi
        }

        self.supported_frameworks = list(self.webserver_dispacher.keys())

        if self.close_server_on_exit:
            self.lock = Lock()

    def update_timestamp(self):
        self.lock.acquire()
        global current_timestamp
        current_timestamp = datetime.now()
        self.lock.release()

    def run(self):
        """ 
        Starts 3 threads one for webframework server and one for browser gui 
        """

        if self.close_server_on_exit:
            self.update_timestamp()

        t_start_webserver = Thread(target=self.start_webserver)
        t_open_chromium = Thread(target=self.open_chromium)
        t_stop_webserver = Thread(target=self.stop_webserver)

        threads = [t_start_webserver, t_open_chromium, t_stop_webserver]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def set_url(self):

        if self.port is None:
            with socketserver.TCPServer(("localhost", 0), None) as s:
                free_port = s.server_address[1]
            self.port = free_port

        self.localhost = f"http://{self.host}:{self.port}"

    def start_webserver(self):

        if isfunction(self.start_server):
            self.start_server()

        if self.start_server not in self.supported_frameworks:
            raise Exception(
                f"'start_server'({self.start_server}) not in {','.join(self.supported_frameworks)} and also not a function which starts the webframework")

        self.webserver_dispacher[self.start_server]()

    def add_flask_middleware(self):

        @self.app.after_request
        def keep_alive_after_request(response):
            self.keep_server_running()
            return response

        @self.app.route("/flaskwebgui-keep-server-alive")
        def keep_alive_pooling():
            self.keep_server_running()
            return "ok"

    def start_flask(self):

        if self.close_server_on_exit:
            self.add_flask_middleware()

        try:
            import waitress
            waitress.serve(self.app, host=self.host, port=self.port)
        except:
            self.app.run(host=self.host, port=self.port)

    def start_flask_socketio(self):

        if self.close_server_on_exit:
            self.add_flask_middleware()

        self.socketio.run(self.app, host=self.host,
                          port=self.port, debug=False)

    def start_django(self):
        try:
            import waitress
            waitress.serve(self.app, host=self.host, port=self.port)
        except:
            try:  # linux and mac
                os.system(f"python3 manage.py runserver {self.port}")
            except:  # windows
                os.system(f"python manage.py runserver {self.port}")

    def add_fastapi_middleware(self):

        @self.app.middleware("http")
        async def keep_alive_after_request(request, call_next):
            response = await call_next(request)
            self.keep_server_running()
            return response

        @self.app.route("/flaskwebgui-keep-server-alive")
        async def keep_alive_pooling():
            self.keep_server_running()
            return "ok"

    def start_fastapi(self):
        pass

    def open_chromium(self):
        """
            Open the browser selected (by default it looks for chrome)
            # https://peter.sh/experiments/chromium-command-line-switches/
        """

        logging.info(f"Opening browser at {self.localhost}")

        temp_profile_dir = os.path.join(tempfile.gettempdir(), "flaskwebgui")

        if self.browser_path:
            launch_options = None
            if self.fullscreen:
                launch_options = ["--start-fullscreen"]
            elif self.maximized:
                launch_options = ["--start-maximized"]
            else:
                launch_options = [f"--window-size={self.width},{self.height}"]

            options = [
                self.browser_path,
                f"--user-data-dir={temp_profile_dir}",
                "--new-window",
                "--no-first-run",
                # "--window-position=0,0"
            ] + launch_options + [f'--app={self.localhost}']

            sps.Popen(options, stdout=sps.PIPE,
                      stderr=sps.PIPE, stdin=sps.PIPE)

        else:
            import webbrowser
            webbrowser.open_new(self.localhost)

    def stop_webserver(self):
        if self.close_server_on_exit is False:
            return

        # TODO add middleware for Django
        if self.start_server == 'django':
            logging.info("Middleware not implemented (yet) for Django.")
            return

        while True:

            self.lock.acquire()
            global current_timestamp
            delta_seconds = (datetime.now() -
                             current_timestamp).total_seconds()
            self.lock.release()

            # print("Idle:", delta_seconds)
            if delta_seconds > self.idle_interval:
                logging.info("App To be closed")
                break

            time.sleep(self.idle_interval)

        if isfunction(self.on_exit):
            logging.info(f"Executing {self.on_exit.__name__} function...")
            self.on_exit()

        logging.info("Closing connections...")
        os.kill(os.getpid(), 9)

    def keep_server_running(self):
        self.update_timestamp()
        return "Ok"
