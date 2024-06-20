from Retrievers import SupportModel, LawRetrievers

retriever = LawRetrievers()
retriever.set_retriever_by_model(SupportModel.BGE_M3, 'cuda', k=5)
user_input = "請問民法第83條是?"
schema = "角色:你是一個法律顧問，只從以下內容回答問題"
contents = retriever.invoke(user_input)
# print(contents)
result = schema + "\n" + contents + "\nQuestion:" + user_input
print(result)
