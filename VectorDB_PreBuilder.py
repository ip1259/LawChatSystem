from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import DocArrayHnswSearch
from LawDataProcessor import LawData
import LawDataProcessor

bge_embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-m3", model_kwargs={'device': 'cuda'})


def buildDB(law_name: str):
    try:
        claw = LawData.from_law_name(law_name)
        print(f"已從 {law_name}.ld 中載入資料")
    except:
        print(f"找不到 {law_name}.ld ，將嘗試從全國法規資料庫中查詢")
        claw = LawData.from_dict(LawDataProcessor.find_law_from_gov_api(law_name))

    if claw.is_abandoned():
        print(f"{claw.law_name} 已廢棄")
        return

    vectordb = None
    if not claw.law_embeddings:
        print("尚未執行過嵌入作業")
        vectordb = DocArrayHnswSearch.from_texts(texts=claw.get_all_articles(ignore_removed_article=True),
                                                 embedding=bge_embeddings,
                                                 work_dir='LawData/embeddings',
                                                 n_dim=1024)
        claw.set_embeddings(True)
        print("嵌入完成")
    else:
        print("已執行過嵌入作業")
        vectordb = DocArrayHnswSearch.from_params(embedding=bge_embeddings,
                                                  work_dir='LawData/embeddings',
                                                  n_dim=1024)


def add_one_by_one():
    while True:
        law_name = input("請輸入要建立的法律名稱:\n")
        buildDB(law_name)
        if law_name.lower() == 'quit':
            break


def add_by_list(law_list: list):
    for law in law_list:
        buildDB(law)


if __name__ == "__main__":
    LAW_LIST = ["民法", "民法總則施行法", "民法債編施行法", "民法物權編施行法", "民法親屬編施行法", "民法繼承編施行法", "涉外民事法律適用法", "民事訴訟法", "民事訴訟法施行法",
                "民事訴訟費用法", "強制執行法", "管收條例", "破產法", "破產法施行法", "非訟事件法", "公證法", "提存法", "民刑事訴訟卷宗滅失案件處理法", "消費者債務清理條例"]
    add_by_list(LAW_LIST)
