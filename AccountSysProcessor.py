import joblib
from google.ai.generativelanguage_v1 import Content as ChatContent
import os


class User:
    def __init__(self, _id: str = "", pswd: str = ""):
        _userid = _id
        _paswd = pswd
        _admit = False
        _chatHistory: list[list[ChatContent]] | None = None

    def get_pswd(self):
        return self._paswd

    @staticmethod
    def load_user(_id: str, pswd: str):
        if not os.path.exists(f"./Users/{_id}.account"):
            return False, f"使用者{_id}不存在"
        else:
            tmpUser: User = joblib.load(f"./Users/{_id}.account")
            if tmpUser.get_pswd() == pswd:
                return True, tmpUser
            else:
                return False, f"密碼不正確"

    @staticmethod
    def dump_user(user):
        joblib.dump(user,f"./Users/{user._userid}.account")

    @staticmethod
    def signup

