import datetime
import json
import logging
import os

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
        self.law_URL = ""
        self.law_pcode = ""
        self.law_isLawAbandon = False
        self.law_modified_date = datetime.date(2000, 1, 1)
        self.law_effective_date = datetime.date(2000, 1, 1)
        self.law_articles: list[Article] = []
        self.law_embeddings = False

    @classmethod
    def from_dict(cls, law_dict: dict):
        result = cls()
        result.law_name = law_dict['LawName']
        result.law_level = law_dict['LawLevel']
        result.law_URL = law_dict['LawURL']
        result.law_pcode = str(law_dict['LawURL']).split('=')[1]
        result.law_isLawAbandon = "廢" in law_dict['LawAbandonNote']
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
        logging.debug(type(result))
        logging.debug(LawData)
        if not isinstance(type(result), type(LawData)):
            raise TypeError
        return result

    @classmethod
    def from_law_name(cls, law_name: str):
        result = None
        try:
            result = cls.from_file("LawData/" + law_name + ".ld")
        except FileNotFoundError as e:
            logging.debug(e)
            logging.debug("正在建立" + e.filename)
            result = cls.from_dict(find_law_from_gov_api(law_name))
            save_law_data(result)
        return result

    def set_embeddings(self, embeddings: bool):
        self.law_embeddings = embeddings
        save_law_data(self)

    def is_abandoned(self):
        return self.law_isLawAbandon

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

    def get_all_articles(self, ignore_removed_article: bool = False, group_by_chapter: bool = False, str_mode: bool = False, max_arts_in_group: int = 10):
        """

        :param ignore_removed_article: if True 取得的回傳值不包含已刪除的條文
        :param group_by_chapter: if True 取得的回傳值以章節群組
        :param str_mode: 只在 group_by_chapter 為True值時有效，if True 取得的回傳值為字串組成一維陣列，if False 取得的回傳值為二維陣列，由章節名稱及章節下法條清單組成
        :return:
        """
        result = []
        if not group_by_chapter:
            for a in self.law_articles:
                if a.article_type == "A":
                    if not ignore_removed_article:
                        tmp = a.get_article_title() + " " + a.article_content
                        result.append(tmp)
                    elif "（刪除）" not in a.article_content:
                        tmp = a.get_article_title() + " " + a.article_content
                        result.append(tmp)
        else:
            temp = []
            part = ""
            chapter = ""
            section = ""
            sub_section = ""
            title = ""
            for a in self.law_articles:
                if a.article_type == "C":
                    if "編" in a.article_content:
                        part = a.article_content.replace(" ", "")
                        chapter = ""
                        section = ""
                        sub_section = ""
                    elif "章" in a.article_content:
                        chapter = a.article_content.replace(" ", "")
                        section = ""
                        sub_section = ""
                    elif "節" in a.article_content:
                        section = a.article_content.replace(" ", "")
                        sub_section = ""
                    elif "款" in a.article_content:
                        sub_section = a.article_content.replace(" ", "")

                    if len(temp) > 1 and title == "":
                        if str_mode:
                            temp_str = ""
                            for i in temp:
                                temp_str += i + "\n"
                            temp_str = temp_str.rstrip()
                            result.append(temp_str)
                        else:
                            result.append(temp)
                        temp = []
                    title = part + " " + chapter + " " + section + " " + sub_section
                    title = title.rstrip()
                elif a.article_type == "A":
                    if len(temp)-1 >= max_arts_in_group:
                        title = temp[0]
                        if str_mode:
                            temp_str = ""
                            for i in temp:
                                temp_str += i + "\n"
                            temp_str = temp_str.rstrip()
                            result.append(temp_str)
                        else:
                            result.append(temp)
                        temp = []

                    if title != "":
                        temp.append(title)
                        title = ""
                    if not ignore_removed_article:
                        temp.append(a.get_article_title() + " " + a.article_content)
                    elif "（刪除）" not in a.article_content:
                        temp.append(a.get_article_title() + " " + a.article_content)

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
    try:
        r = requests.get("https://law.moj.gov.tw/api/Ch/Law/JSON")
        with zipfile.ZipFile(io.BytesIO(r.content)).open("ChLaw.json") as laws:
            return json.load(laws)['Laws']
    except zipfile.BadZipfile as e:
        logging.warning(e)
        logging.debug("Try to load from another URL")
        try:
            r = requests.get("https://law.moj.gov.tw/api/data/chlaw.json.zip")
            with zipfile.ZipFile(io.BytesIO(r.content)).open("ChLaw.json") as laws:
                return json.load(laws)['Laws']
        except zipfile.BadZipfile as e:
            logging.warning(e)
            logging.debug('Try to load From Local File')
            with zipfile.ZipFile('ChLaw.json.zip').open("ChLaw.json") as laws:
                return json.load(laws)['Laws']


LAWS = load_laws_from_gov_api()


def update_preloaded_laws():
    global LAWS
    LAWS = load_laws_from_gov_api()


def find_law_from_gov_api(law_name: str = ""):
    global LAWS
    if law_name != "":
        laws = LAWS
        for law in laws:
            if law['LawName'] == law_name:
                return law
        raise LawDataExceptionHandler.LawNotFoundException(law_name)
    else:
        raise LawDataExceptionHandler.BlankLawNameException


def update_law_data():
    update_preloaded_laws()
    global LAWS
    ld_files = os.listdir("LawData")
    try:
        os.remove("LawData/embeddings/docs_sqlite.db")
        os.remove("LawData/embeddings/embedding.bin")
    except FileNotFoundError as e:
        logging.debug(e)

    import VectorDB_PreBuilder
    for i in ld_files:
        if ".ld" in i:
            law_name = i.split(".")[0]
            logging.debug("Remove: " + "LawData/" + i)
            os.remove("LawData/" + i)
            LawData.from_law_name(law_name)
            VectorDB_PreBuilder.build_vectordb_aio(law_name)


if __name__ == "__main__":
    update_law_data()
