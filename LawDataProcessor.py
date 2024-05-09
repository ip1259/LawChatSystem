import datetime
import json
import joblib
from typing import TextIO, Union, Type
import LawDataExceptionHandler
from langchain_community.vectorstores import DocArrayInMemorySearch


class Article:
    """條文物件，主要會以List的方式用在法律物件內"""

    def __init__(self):
        self.article_law_name = ""
        self.article_number = ""
        self.article_type = ""
        self.article_content = ""

    @classmethod
    def from_dict(cls, law_name: str, article_dict: dict):
        result = cls()
        result.article_law_name = law_name
        result.article_number = str(article_dict['ArticleNo']).replace(" ", "")
        result.article_type = article_dict['ArticleType']
        result.article_content = article_dict['ArticleContent']
        return result

    def dict(self):
        return {"LawName": self.article_law_name,
                "ArticleNumber": self.article_number,
                "ArticleType": self.article_type,
                "ArticleContent": self.article_content}

    def get_article_title(self):
        return self.article_law_name + self.article_number


class LawData:
    """用於儲存及處理法律資料"""

    def __init__(self):
        self.law_name = ""
        self.law_level = ""
        self.law_modified_date = datetime.date(2000, 1, 1)
        self.law_effective_date = datetime.date(2000, 1, 1)
        self.law_articles: list[Article] = []
        self.law_embeddings = None

    @classmethod
    def from_dict(cls, law_dict: dict):
        result = cls()
        result.law_name = law_dict['LawName']
        result.law_level = law_dict['LawLevel']
        if law_dict['LawModifiedDate'] != "":
            result.law_modified_date = datetime.date(year=int(law_dict['LawModifiedDate'][0:4]),
                                                     month=int(law_dict['LawModifiedDate'][4:6]),
                                                     day=int(law_dict['LawModifiedDate'][6:]))
        else:
            result.law_modified_date = datetime.date(2000, 1, 1)
        if law_dict['LawEffectiveDate'] != "" and int(
                law_dict['LawEffectiveDate'][0:4]) <= datetime.date.today().year:
            result.law_effective_date = datetime.date(year=int(law_dict['LawEffectiveDate'][0:4]),
                                                      month=int(law_dict['LawEffectiveDate'][4:6]),
                                                      day=int(law_dict['LawEffectiveDate'][6:]))
        else:
            result.law_effective_date = datetime.date(2000, 1, 1)
        result.law_articles = []
        for a in law_dict['LawArticles']:
            tmp_article = Article.from_dict(result.law_name, article_dict=a)
            result.law_articles.append(tmp_article)
        result.law_embeddings = None
        return result

    @classmethod
    def from_file(cls, path: str):
        result = joblib.load(path)
        if not isinstance(result, LawData):
            raise TypeError
        return result

    @classmethod
    def from_law_name(cls, law_name: str):
        result = cls.from_file("LawData/" + law_name + ".ld")
        return result

    def set_embeddings(self, embeddings: DocArrayInMemorySearch):
        self.law_embeddings = embeddings
        save_law_data(self)

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

    def get_all_articles(self):
        result = []
        for a in self.law_articles:
            if a.article_type == "A":
                tmp = a.get_article_title() + " " + a.article_content
                result.append(tmp)
        return result

    def get_law_name(self):
        return self.law_name

    def get_table_of_articles(self):
        result = ""
        for a in self.law_articles:
            if a.article_type == "C":
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
        raise LawDataExceptionHandler.LawNotFoundException(law_name)
    else:
        raise LawDataExceptionHandler.BlankLawNameException
