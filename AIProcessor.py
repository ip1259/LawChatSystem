import os
from dotenv import load_dotenv
from google.api_core.exceptions import InternalServerError
import time
from functools import wraps

import LawDataProcessor
from LawDataProcessor import load_data, save_data, Article
from LawDataProcessor import LawData
import numpy as np
import pandas as pd
import google.generativeai as genai
import google.ai.generativelanguage as glm

load_dotenv()

KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=KEY)
emb_model = 'models/embedding-001'
gen_model = genai.GenerativeModel('gemini-1.0-pro')
chat = gen_model.start_chat(history=[])
chat_started = False
cur_related_articles = None
retry_counter = 0


def retry_function(func):
    @wraps(func)
    def warp_func(*args, **kargs):
        for _ in range(3):
            try:
                func_result = func(*args, **kargs)
            except Exception as e:
                print("Retry [function: {}], {}".format(
                       func.__name__, e))
                time.sleep(1)
            else:
                return func_result
        else:
            raise Exception("Retry timeout")
    return warp_func


def embedding_all_articles(law_df: LawData):
    global emb_model
    for article in law_df.law_articles:
        article.article_embedding = genai.embed_content(model=emb_model,
                                                        content=article.article_content,
                                                        task_type="retrieval_document",
                                                        title=article.get_article_title(law_df.get_law_name())
                                                        )['embedding']
    save_data(law_df)


def get_dot_product(qstr, label_str, q_embedding=None):
    if q_embedding is None:
        query_embedding = genai.embed_content(model=emb_model,
                                              content=qstr,
                                              task_type="retrieval_query")["embedding"]
    else:
        query_embedding = q_embedding
    lb_embedding = genai.embed_content(model=emb_model,
                                       content=label_str,
                                       task_type="retrieval_query")["embedding"]
    return np.dot(query_embedding, lb_embedding)


def get_pd_dataframe_with_dot_products(query, dataframe: LawData):
    """
  Compute the distances between the query and each document in the dataframe
  using the dot product.
  """
    query_embedding = genai.embed_content(model=emb_model,
                                          content=query,
                                          task_type="retrieval_query")
    data_embeddings = []
    _temp = pd.DataFrame({'article_names': [],
                          'article_contents': []})
    for e in dataframe.law_articles:
        data_embeddings.append(e.article_embedding)
        new_row = [e.get_article_title(dataframe.get_law_name()), e.article_content]
        _temp.loc[len(_temp)] = new_row
    dot_products = np.dot(np.stack(data_embeddings), query_embedding["embedding"])
    _temp = _temp.assign(dot_products=dot_products.tolist())
    _temp.sort_values('dot_products', ascending=False, inplace=True)
    return _temp  # Return pd DataFrame of Law Data With dot Products


def find_related_articles(dataframe, threshold: float = 0.7, max_rows=100):
    """
    回傳最相關的條文
    :param dataframe: A PD DataFrame from func get_pd_dataframe_with_dot_products
    :param threshold: 閾值應屆於0到1之間，表示代表相關度的點積值最低應高於此值，預設為0.7
    :param max_rows:指定資料數最多幾條，預設為100
    :return: 回傳PD dataframe，
    """
    result = dataframe.loc[dataframe['dot_products'] >= threshold]
    if len(result) >= max_rows:
        result = result[:max_rows]
        result.reset_index(inplace=True)
        # result.sort_values('article_names', inplace=True)
    return result


def find_most_related_label(qstr, labels: list[str]):
    """
    WSP
    :param qstr:
    :param labels:
    :return:
    """
    if len(labels) == 0:
        return None
    max_dot = -1
    related_label = ""
    q_embedding = genai.embed_content(model=emb_model,
                                      content=qstr,
                                      task_type="retrieval_query")["embedding"]
    for s in labels:
        dot = get_dot_product("", s, q_embedding)
        if dot is not None and dot > max_dot:
            max_dot = dot
            related_label = s
    return related_label


def gemini_answer(q_str, articles: list[Article]):
    data_str = ""
    response = None
    if articles is not None and len(articles) != 0:
        for a in articles:
            data_str += a.article_law_name + a.article_number + " " + a.article_content + "\n"
        prompt = (
                "重要:以中文回答\n你是一個的法律顧問，你會從提示中給予的法律條文資料作為回答的參考來源，進行擬人化的回答，回答內容應盡可能豐富，並且易於理解，並以舉例方式說明\n法律條文資料:" + data_str
                + "\n問題:" + q_str)
        response = gen_model.generate_content(prompt,
                                              generation_config=genai.types.GenerationConfig(
                                                  temperature=0.8),
                                              )
    else:
        prompt = "重要:以中文回答\n生成一個委婉地、擬人化的、真實的語句，表達以下意思:您的問題或許不在民法的範疇內所以我無法回答。"
        response = gen_model.generate_content(prompt,
                                              generation_config=genai.types.GenerationConfig(
                                                  temperature=0.9)
                                              )

    return response.text.replace('•', '  *').replace(".", ". ")


def civil_code_analyze(qstr, table):
    prompt = "問題:\n" + qstr + "\n以上問題是否是民法相關?\n輸出格式:是/否"
    is_law_q = gen_model.generate_content(prompt,
                                          generation_config=genai.types.GenerationConfig(
                                              temperature=0.0)
                                          ).text
    # print(is_law_q)
    if "是" in is_law_q:
        prompt = "問題:\n" + qstr + "\n以上問題中是否是指定第幾條法條的問題?\n輸出格式:是/否"
        ask_specific_article = gen_model.generate_content(prompt,
                                                          generation_config=genai.types.GenerationConfig(
                                                              temperature=0.0)
                                                          ).text
        # print(ask_specific_article)
        if "是" in ask_specific_article:
            prompt = "問題:\n" + qstr + "\n以上問題的指定法條是幾號?\n範例輸入:民法第123-1號及145號 範例輸出:N123-1\nN145"
            article_num = gen_model.generate_content(prompt,
                                                     generation_config=genai.types.GenerationConfig(
                                                         temperature=0.0)
                                                     ).text
            print("[civil_code_analyze]:" + article_num)
            return article_num
        else:
            prompt = "目錄:\n" + table + "\n" + "以下問題的答案最可能出現在那幾編\n" + qstr + (
                "\n輸出格式:C第X編 XXX\nC第X編 XXX")
            response = gen_model.generate_content(prompt,
                                                  generation_config=genai.types.GenerationConfig(
                                                      temperature=0.0)
                                                  )
        print("[civil_code_analyze]:" + response.text)
        return response.text
    else:
        return None


def find_related_laws(qstr):
    civil_code = load_data("民法")
    cc_result = civil_code_analyze(qstr, civil_code.get_table_of_articles())
    if cc_result is None:
        return None
    if "C" in cc_result:
        chapters = [["總則", "", "", ""]]
        chp_lst = cc_result.splitlines()
        for c in chp_lst:
            if c[0] != "總則":
                chapters.append(LawDataProcessor.analyze_chapter(c))
        related_articles = civil_code.get_articles_by_chapters(chapters)
        tmp = []
        for c in chapters:
            tmp.append(c[0])
        tmp = set(tmp)

        for t in tmp:
            other_law = ""
            if t == "總則":
                other_law = load_data("民法總則施行法")
            else:
                other_law = load_data("民法" + t + "編施行法")
            for a in other_law.law_articles:
                related_articles.append(a)
        return related_articles
    elif "N" in cc_result:
        articles = []
        arc_lst = cc_result.splitlines()
        for a in arc_lst:
            articles.append(civil_code.get_article_by_num(a))
        return articles


def clean_chatbot():
    global chat
    chat = gen_model.start_chat(history=[])
    global chat_started
    chat_started = False


@retry_function
def start_chat(qstr):
    articles = find_related_laws(qstr)
    global chat
    chat = gen_model.start_chat(history=[])
    prompt = ("這是系統資訊，會描述在接下來的對話中你所扮演的角色以及回答的規則\n"
              + "角色:你是一個法律顧問，但只回答民法相關問題\n"
              + "規則1.從<法律條文資料>作為回答\n"
              + "規則2.以中文回答\n"
              + "規則3.回答內容應豐富，並且易於理解，較少的專業詞彙\n"
              + "規則4.以舉例方式說明\n"
              + "規則5.如果法律條文為無資料，且使用者問題與民法無關請委婉地拒絕回答\n"
              + "規則6.回答範圍只限於<法律條文資料>的條文資料，超出<法律條文資料>的範圍，請回答<建議重新開始新的聊天讓系統重新搜索適合的法條>\n"
              + "規則7.回答後給予警示<因法律條文僅參考民法，可能有所謬誤，請斟酌參考>\n"
              + "規則8.回答禁止延伸到其他法律\n"
              + "\n<法律條文資料>:")
    data_str = ""
    if articles is not None and len(articles) != 0:
        for a in articles:
            data_str += a.article_law_name + a.article_number + " " + a.article_content + "\n"
    else:
        data_str = "無資料"

    print(data_str)
    prompt += data_str
    print("[Tokens count]:" + str(gen_model.count_tokens(prompt)))
    response = chat.send_message(prompt,
                                 generation_config=genai.types.GenerationConfig(
                                     temperature=0.9))
    global chat_started
    chat_started = True
    global cur_related_articles
    cur_related_articles = articles
    return response.text


def gemini_chat(qstr):
    if not chat_started:
        start_chat(qstr)
    global chat
    try:
        chat.send_message(qstr,
                          generation_config=genai.types.GenerationConfig(
                              temperature=0.8))
    except InternalServerError as ise:
        print(ise.message)
        time.sleep(3)
        return gemini_chat(qstr)
    history = []
    indx = 0
    tmp = ["", ""]
    for message in chat.history:
        # print(message.role, message.parts[0].text)
        if indx % 2 == 0:
            tmp[0] = message.parts[0].text
        else:
            tmp[1] = message.parts[0].text
            history.append((tmp[0], tmp[1]))
        indx += 1
    global cur_related_articles
    if cur_related_articles is None:
        clean_chatbot()
    return history[1:]
