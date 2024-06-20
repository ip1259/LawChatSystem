from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import DocArrayHnswSearch
from enum import Enum
from pydantic.v1 import BaseModel, Field
import logging

logging.basicConfig(level=logging.DEBUG)


class SupportModel(Enum):
    BGE_M3 = "BAAI/bge-m3"


class LawRetrievers:
    def __init__(self):
        self.CUR_RETRIEVER = None

    def set_retriever_by_model(self, model: SupportModel, device: str, k: int = 100):
        match model:
            case SupportModel.BGE_M3:
                self.bge_m3_retriever(device, k)

    def bge_m3_retriever(self, device, k):
        logging.debug("retriever start")
        bge_embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-m3", model_kwargs={'device': device})
        vectordb = DocArrayHnswSearch.from_params(embedding=bge_embeddings,
                                                  work_dir='LawData/embeddings/B0000001',
                                                  n_dim=1024,
                                                  max_elements=4096)
        _retriever = vectordb.as_retriever(search_kwargs={'k': k})
        self.CUR_RETRIEVER = _retriever
        logging.debug("retriever end")

    def invoke(self, user_input: str):
        logging.debug("invoke start")
        try:
            contents = ""
            for d in self.CUR_RETRIEVER.invoke(user_input):
                contents = contents + d.page_content + "\n\n"
            logging.debug("invoke end")
            return contents

        except Exception as e:
            print(e, "You may not set model yet.")
