import os
import time
from dotenv import load_dotenv
from functools import wraps
import google.generativeai as genai
import LawDataProcessor
from LawDataProcessor import Article, LawData
import numpy as np
import pandas as pd

load_dotenv()

KEY = os.getenv('GOOGLE_API_KEY')
chat_model = genai.GenerativeModel('gemini-1.0-pro')


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


def gemini_chat(message: str):
    pass


def clean_chatbot():
    pass
