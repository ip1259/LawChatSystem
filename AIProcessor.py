import logging
import os
import time
from dotenv import load_dotenv
from functools import wraps
import google.generativeai as genai
from Retrievers import SupportModel, LawRetrievers
import LawDataProcessor
from LawDataProcessor import Article, LawData
import numpy as np
import pandas as pd

load_dotenv()

RETRY_TIMES = 5
KEY = os.getenv('GOOGLE_API_KEY')
chat_model = genai.GenerativeModel('gemini-1.0-pro')
retriever = None


def retry_function(func):
    @wraps(func)
    def warp_func(*args, **kargs):
        global RETRY_TIMES
        for _ in range(RETRY_TIMES):
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


def get_prompt(user_inputs: list[str]):
    user_input = ""
    for s in user_inputs:
        user_input += s + "\n"
    _retriever = LawRetrievers()
    _retriever.set_retriever_by_model(SupportModel.BGE_M3, 'cuda', k=10)
    schema = ('角色:你是一個法律顧問\n'
              '任務:從以下內容回答問題並"""詳細說明"""，說明應避免專業詞彙，以"""通俗的詞彙""","""舉例方式"""說明，並於最後附上"""法源依據"""及"""AI免責聲明"""\n'
              '回答風格:聊天的回應風格,回答內容應該更白話一點,有豐富的內容')
    contents = _retriever.invoke(user_input)
    result = schema + "\n" + contents + "\nQuestion:" + user_inputs[-1]
    print(result)
    return result


@retry_function
def gemini_response(messages, temp):
    response = chat_model.generate_content(
        messages,
        generation_config=genai.types.GenerationConfig(temperature=temp)
    )
    return response


def gemini_chat(user_input: str, history: list[tuple[str, str]], temp=0.6):
    messages = []
    user_inputs = []
    for input_text, response_text in history:
        user_inputs.append(input_text)
        messages.append({'role': 'user', 'parts': [input_text]})
        messages.append({'role': 'model', 'parts': [response_text]})

    user_inputs.append(user_input)
    messages.append({'role': 'user', 'parts': [get_prompt(user_inputs)]})

    response = gemini_response(messages, temp)
    logging.debug(response.text)
    history.append((user_input, response.text))
    return history


def clean_chatbot():
    pass
