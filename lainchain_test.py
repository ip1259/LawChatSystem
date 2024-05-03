from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch

bge_embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-m3", model_kwargs={'device': 'cuda'})
