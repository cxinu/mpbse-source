import os
import base64
from threading import Thread
from werkzeug.utils import secure_filename
from flask import Flask, redirect, render_template, request, send_file, url_for, flash
from deskapp import FlaskUI

from single import f_10, f_12, fetch_all

app = Flask(__name__)
app.secret_key = "abcdfu"

app.config['UPLOAD_FILE'] = (os.path.join(os.getenv('APPDATA'), 'Tensile'))
if not os.path.exists(os.path.join(os.getenv('APPDATA'), 'Tensile')):
    os.mkdir(os.path.join(os.getenv('APPDATA'), 'Tensile'))

ui = FlaskUI(app, idle_interval=7)


@app.route('/d')
@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("index.html")

# ----------- upload for Excel ----------- #

@app.route('/upload', methods=["POST"])
def upload_excel():
    if request.method == "POST":
        if request.files:
            xlsx = request.files["excel"]

            if xlsx.filename == "":
                flash("No File Selected - Please Select File")
                return redirect(url_for('index'))

            if ".xlsx" not in xlsx.filename:
                flash("Invaild File Format - Upload a vaild Excel File")
                return redirect(url_for('index'))

            savepath = os.path.join(app.config['UPLOAD_FILE'],
                                    secure_filename(xlsx.filename))
            xlsx.save(savepath)
            if request.form["grade"] == '0':
                cond = fetch_all(path=savepath, f_=f_10)
                if not cond:
                    flash("Invaild Excel sheet - Make sure Roll No. (12 colm.) & Application No. (colm. 15)")
                    return redirect(url_for('index'))
            elif request.form["grade"] == '1':
                cond = fetch_all(path=savepath, f_=f_12)
                if not cond:
                    flash("Invaild Excel sheet - Make sure Roll No. (12 colm.) & Application No. (colm. 15)")
                    return redirect(url_for('index'))
            os.remove(savepath)

            sample_string_bytes = savepath.encode("ascii")
            base64_bytes = base64.b64encode(sample_string_bytes)
            url_enc = base64_bytes.decode("ascii")

    return render_template("d.html", url_enc=url_enc)


@app.route('/d/<url_enc>', methods=["GET", "POST"])
def download_excel(url_enc):
    base64_bytes = url_enc.encode("ascii")
    sample_string_bytes = base64.b64decode(base64_bytes)
    savepath = sample_string_bytes.decode("ascii")

    prod_result = savepath[:-5]+"_results.xlsx"
    print("donwload_excel(savepath):", prod_result)

    def clear_():
        import time
        time.sleep(10)
        try:
            os.remove(prod_result)
        except Exception as err:
            print(err)

    Thread(target=clear_).start()
    return send_file(prod_result, as_attachment=True)


# # ----------- upload for PDF ----------- #

# @app.route('/pdf', methods=["POST"])
# def upload_pdf():
#     if request.method == "POST":
#         if request.files:
#             xlsx = request.files["pdf_"]

#             if xlsx.filename == "":
#                 flash("No File Selected - Please Select File")
#                 return redirect(url_for('index'))

#             if ".xlsx" not in xlsx.filename:
#                 flash("Invaild File Format - Upload a vaild Excel File")
#                 return redirect(url_for('index'))

#             savepath = os.path.join(app.config['UPLOAD_FILE'],
#                                     secure_filename(xlsx.filename))
#             xlsx.save(savepath)

#             # <------------- opration ------------> #

#             os.remove(savepath)

#             sample_string_bytes = savepath.encode("ascii")
#             base64_bytes = base64.b64encode(sample_string_bytes)
#             url_enc = base64_bytes.decode("ascii")

#     return render_template("pdf.html", url_enc=url_enc)



if __name__ == "__main__":
    ui.run()
    # app.run(debug=True)
