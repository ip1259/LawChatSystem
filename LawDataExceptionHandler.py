class BlankLawDataException(Exception):
    def __init__(self):
        super().__init__("Law name is empty")