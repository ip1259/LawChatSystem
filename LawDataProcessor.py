import datetime
import json
import joblib
from typing import TextIO, Union
import LawDataExceptionHandler


class Article:
    """條文物件，主要會以List的方式用在法律物件內"""

    def __init__(self, article_law_name: str = "", article_num: str = "", article_content: str = "",
                 article_embedding: list[float] = None):
        self.article_law_name = article_law_name
        self.article_number = article_num
        self.article_content = article_content
        self.article_embedding = article_embedding

    def dict(self):
        return {"ArticleNumber": self.article_number,
                "ArticleContent": self.article_content,
                "ArticleEmbedding": self.article_embedding}

    def get_article_title(self, law_name: str):
        return law_name + " " + self.article_number


class LawData:
    """用於儲存及處理法律資料"""

    def __init__(self):
        self.law_name = ""
        self.law_level = ""
        self.law_modified_date = datetime.date(2000, 1, 1)
        self.law_effective_date = datetime.date(2000, 1, 1)
        self.law_articles: list[Article] = []

    def dict(self) -> dict:
        articles = []
        for article in self.law_articles:
            articles.append(article.dict())
        modDate = ""
        effectiveDate = ""
        if self.law_modified_date is not None:
            modDate = self.law_modified_date.strftime("%Y%m%d")
        if self.law_effective_date is not None:
            effectiveDate = self.law_effective_date.strftime("%Y%m%d")
        return {"LawName": self.law_name,
                "LawLevel": self.law_level,
                "LawModifiedDate": modDate,
                "LawEffectiveDate": effectiveDate,
                "LawArticles": articles}

    def get_law_name(self):
        return self.law_name

    def get_table_of_articles(self):
        result = ""
        for a in self.law_articles:
            if a.article_number == "":
                result += a.article_content + "\n"
        return result

    def get_article_by_num(self, num: str):
        num = num.replace('N', "")
        for a in self.law_articles:
            if num in a.article_number:
                return a
        return None

    def get_articles_by_chapters(self, chapters: list[list[str]]):
        """

        :param chapters: 由清單元素組成，每一清單元素包含4個字串元素，分別代表 編 章 節 款
        :return: 輸出一個由article組成的清單，代表包含在編 章 節 款中的法條
        """
        result = []
        cur_chp = ["", "", "", ""]
        for a in self.law_articles:
            if a.article_number == "":
                if "編 " in a.article_content:
                    cur_chp[0] = a.article_content.replace(" ", "").split("編")[1]
                    cur_chp[1] = ""
                    cur_chp[2] = ""
                    cur_chp[3] = ""
                elif "章 " in a.article_content:
                    cur_chp[1] = a.article_content.replace(" ", "").split("章")[1]
                    cur_chp[2] = ""
                    cur_chp[3] = ""
                elif "節 " in a.article_content:
                    cur_chp[2] = a.article_content.replace(" ", "").split("節")[1]
                    cur_chp[3] = ""
                elif "款 " in a.article_content:
                    cur_chp[3] = a.article_content.replace(" ", "").split("款")[1]
            else:
                if cur_chp in chapters:
                    result.append(a)
                elif [cur_chp[0], cur_chp[1], cur_chp[2], ""] in chapters:
                    result.append(a)
                elif [cur_chp[0], cur_chp[1], "", ""] in chapters:
                    result.append(a)
                elif [cur_chp[0], "", "", ""] in chapters:
                    result.append(a)
        return result


def analyze_chapter(chp_str: str):
    chp_str = chp_str.replace("C", "")
    result = ["", "", "", ""]
    chp_lst = chp_str.split(',')
    for e in chp_lst:
        if "編" in e.split()[0]:
            result[0] = e.split()[-1]
        elif "章" in e.split()[0]:
            result[1] = e.split()[-1]
        elif "節" in e.split()[0]:
            result[2] = e.split()[-1]
        elif "款" in e.split()[0]:
            result[3] = e.split()[-1]
    return result


def save_law_data(lawdata: LawData):
    if lawdata.law_name != "":
        joblib.dump(lawdata, filename="LawData/" + lawdata.law_name + ".ld")
    else:
        raise LawDataExceptionHandler.BlankLawNameException


def load_law_data(lawname: str):
    return joblib.load(filename="LawData/" + lawname + ".ld")


def load_laws_from_gov_api():
    import requests, zipfile, io
    r = requests.get("https://law.moj.gov.tw/api/Ch/Law/JSON")
    with zipfile.ZipFile(io.BytesIO(r.content)).open("ChLaw.json") as laws:
        return json.load(laws)['Laws']


def find_law_from_gov_api(law_name: str = ""):
    if law_name != "":
        laws = load_laws_from_gov_api()
        for law in laws:
            if law['LawName'] == law_name:
                return law
        raise LawDataExceptionHandler.LawNotFindException(law_name)
    else:
        raise LawDataExceptionHandler.BlankLawNameException
