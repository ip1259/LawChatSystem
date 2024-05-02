import datetime
import json
from typing import TextIO, Union


class Article:
    """條文物件，主要會以List的方式用在法律物件內"""

    def __init__(self, article_law_name: str = "", article_num: str = "", article_content: str = "", article_embedding: list[float] = None):
        self.article_law_name = article_law_name
        self.article_number = article_num
        self.article_content = article_content
        self.article_embedding = article_embedding

    def dump_to_json(self) -> Union[str, None]:
        return json.dumps(self.dict(), indent=4, ensure_ascii=False)

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

    def get_law_json_data(self, law_json_file: TextIO = None, law_name=""):
        """Get Law Data from json file"""
        temp = json.load(law_json_file)
        try:  # 代表讀取的是全部的法條
            for law in temp['Laws']:
                if law['LawName'] == law_name:
                    self.law_name = law['LawName']
                    self.law_level = law['LawLevel']
                    try:
                        self.law_modified_date = datetime.datetime.strptime(law['LawModifiedDate'], "%Y%m%d")
                    except:
                        self.law_modified_date = None
                    try:
                        self.law_effective_date = datetime.datetime.strptime(law['LawEffectiveDate'], "%Y%m%d")
                    except:
                        self.law_effective_date = None
                    for article in law['LawArticles']:
                        if article['ArticleType'] == "A":
                            self.law_articles.append(Article(article_law_name=law_name,
                                                             article_num=article['ArticleNo'],
                                                             article_content=article['ArticleContent']))
                        elif article['ArticleType'] == "C":
                            self.law_articles.append(Article(article_law_name=law_name,
                                                             article_num=article['ArticleNo'],
                                                             article_content=article['ArticleContent']))
        except KeyError as ke:  # 代表讀取的是嵌入過的法條檔
            law = temp
            if law['LawName'] == law_name:
                self.law_name = law['LawName']
                self.law_level = law['LawLevel']
                try:
                    self.law_modified_date = datetime.datetime.strptime(law['LawModifiedDate'], "%Y%m%d")
                except:
                    self.law_modified_date = None
                try:
                    self.law_effective_date = datetime.datetime.strptime(law['LawEffectiveDate'], "%Y%m%d")
                except:
                    self.law_effective_date = None
                for article in law['LawArticles']:
                    self.law_articles.append(Article(law_name,
                                                     article['ArticleNumber'],
                                                     article['ArticleContent'],
                                                     article['ArticleEmbedding']
                                                     )
                                             )

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

    def dump_to_json(self) -> Union[str, None]:
        return json.dumps(self.dict(), indent=4, ensure_ascii=False)

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


def load_data(law_name: str) -> Union[LawData, None]:
    try:
        with open("LawData/" + str(law_name) + ".json", 'r', encoding="utf-8") as f:
            tmp = LawData()
            tmp.get_law_json_data(f, law_name)
            return tmp
    except FileNotFoundError as e_noFile:
        try:
            with open("LawData/ChLaw.json", 'r', encoding="utf-8-sig") as f:
                tmp = LawData()
                tmp.get_law_json_data(f, law_name)
                from AIProcessor import embedding_all_articles
                embedding_all_articles(tmp)
                return tmp
        except Exception as e:
            print(e)
            return None


def save_data(data: LawData):
    with open("LawData/" + str(data.law_name + ".json"), 'w', encoding="utf-8") as fp:
        json.dump(data.dict(), fp, ensure_ascii=False, indent=4)
