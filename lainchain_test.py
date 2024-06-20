from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import DocArrayHnswSearch
from LawDataProcessor import LawData


law = LawData.from_law_name("民法")
bge_embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-m3", model_kwargs={'device': 'cuda'})
vectordb = DocArrayHnswSearch.from_params(embedding=bge_embeddings,
                                          work_dir='LawData/embeddings/' + law.law_pcode,
                                          n_dim=1024,
                                          max_elements=4096)
bge_retriever = vectordb.as_retriever(search_kwargs={'k': 200})
for d in bge_retriever.invoke("民法第八十三條"):
    print(d.page_content, '\n')

# for d, f in vectordb.similarity_search_with_relevance_scores("繼承的順序", k=100, score_threshold=0.55):
#     print(d, f)
