class BlankLawNameException(Exception):
    def __init__(self):
        super().__init__("Law name is empty")


class LawNotFoundException(Exception):
    def __init__(self, lawname: str):
        super().__init__(f"找不到名為 \"{lawname}\" 的法條")
