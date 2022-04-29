from config import *
import requests
from bs4 import BeautifulSoup
import pandas as pd


def f_10(rollno, appno):
    while (True):
        try:
            s = requests.Session()
            srow = []
            payload = {'rollno': rollno, 'appno': appno, 'B3': 'Submit'}
            r = s.post(X_URL, data=payload, headers=X_HEADERS)
            soup = BeautifulSoup(r.content, 'html.parser')
            tables = soup.find_all("table")

            _class = tables[5].find("strong")
            if '10' in str(_class):
                Class = 10
            elif '12' in str(_class):
                Class = 12
            Session = str(_class)[-13:-9]
            srow.append(Class)
            srow.append(Session)

            for i in range(0, 6):
                td = tables[6].find_all("tr")[1].find_all("font")[i].string
                if i > 3:
                    srow.append(int(td))
                    continue
                srow.append(td)

            for i in range(0, 3):
                td = tables[8].find_all("tr")[i].find_all(
                    "strong")[1].string[1:]
                srow.append(td)

            Result = tables[9].find_all("font")[2].string[1:]
            if 'first' in Result.lower():
                res_ = 'प्रथम'
            elif 'second' in Result.lower():
                res_ = 'द्वितीय'
            elif 'third' in Result.lower():
                res_ = 'तृतीय'
            elif 'supplementary' in Result.lower():
                res_ = 'पूरक'
            elif 'failed' in Result.lower():
                res_ = 'उनुत्तीर्ण'
            srow.append(res_)

            for i in range(1, 13, 2):
                SUB = tables[10].find_all("tr")[i].find_all("td")[1].string[1:]
                TOTALM = tables[10].find_all("tr")[i].find_all("td")[4].string
                REMARK = tables[10].find_all("tr")[i + 1].find_all(
                    "td")[1].find("font").string
                if REMARK == 'DISTN':
                    REMARK = SUB
                else:
                    REMARK = None
                srow.append(SUB)
                srow.append(TOTALM)
                srow.append(REMARK)

            grand_total = tables[10].find_all("strong")[6].string[-7:]
            srow.append(grand_total)

            percentage = format(eval(grand_total)*100, ".2f")
            srow.append(percentage)

            break
        except Exception as e:
            print("refetch:", e)
            if 'list index out of range' in str(e) or 'zeros' in str(e):
                relst = []
                for i in range(0, len(FIELD_NAMES)):
                    relst.append(None)
                return relst

    return srow


def f_12(rollno, appno):
    while (True):
        try:
            s = requests.Session()
            srow = []
            payload = {'rollno': rollno, 'appno': appno, 'B3': 'Submit'}
            r = s.post(XII_URL, data=payload, headers=XII_HEADERS)
            soup = BeautifulSoup(r.content, 'html.parser')
            tables = soup.find_all("table")

            _class = tables[5].find("strong")
            if '10' in str(_class):
                Class = 10
            elif '12' in str(_class):
                Class = 12
            Session = str(_class)[-13:-9]
            srow.append(Class)
            srow.append(Session)

            for i in range(0, 6):
                td = tables[6].find_all("tr")[1].find_all("font")[i].string
                if i > 3:
                    srow.append(int(td))
                    continue
                srow.append(td)

            for i in range(0, 3):
                td = tables[8].find_all("tr")[i].find_all(
                    "strong")[1].string[1:]
                srow.append(td)

            Result = tables[9].find_all("strong")[0].string[10:]
            if 'first' in Result.lower():
                res_ = 'प्रथम'
            elif 'second' in Result.lower():
                res_ = 'द्वितीय'
            elif 'third' in Result.lower():
                res_ = 'तृतीय'
            elif 'supplementary' in Result.lower():
                res_ = 'पूरक'
            elif 'failed' in Result.lower():
                res_ = 'उनुत्तीर्ण'
            else:
                res_ = None
            srow.append(res_)

            for i in range(1, 6):
                SUB = str(tables[10].find_all("tr")[
                          i].find_all("td")[1].string[1:])
                TOTALM = tables[10].find_all("tr")[i].find_all("td")[4].string
                REMARK = tables[10].find_all("tr")[i].find_all("td")[
                    5].string[1:]
                if REMARK == 'DISTN':
                    REMARK = SUB
                else:
                    REMARK = None
                srow.append(SUB)
                srow.append(TOTALM)
                srow.append(REMARK)

            # Subject 6
            for i in range(0, 3):
                srow.append(None)

            grand_total = tables[10].find_all("strong")[6].string[-7:]
            srow.append(grand_total)

            percentage = format(eval(grand_total)*100, ".2f")
            srow.append(percentage)

            break
        except Exception as e:
            print("refetch:", e)
            if 'list index out of range' in str(e):
                relst = []
                for i in range(0, len(FIELD_NAMES)):
                    relst.append(None)
                return relst

    return srow


def fetch_all(path, f_):
    try:
        df = pd.read_excel(path)
        scrap = pd.DataFrame(columns=FIELD_NAMES)
        res_cred = df.iloc[:, [11, 14]]

        for i, rollno, appno in res_cred.itertuples():
            srow = f_(rollno, appno)
            new_row = pd.DataFrame([srow], columns=FIELD_NAMES)
            scrap = pd.concat([scrap, new_row], ignore_index=True)
            print('fetched:', i)
        print("excel sheet fetched")
        resultFrame = pd.merge(df, scrap, left_index=True, right_index=True)
        resultFrame.to_excel(path[:-5]+"_results.xlsx", index=False)

        return True
    except Exception as e:
        return False
