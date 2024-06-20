import LawDataProcessor
from LawDataProcessor import LawData

claw = LawData.from_dict(LawDataProcessor.find_law_from_gov_api("民法"))
# claw = LawData.from_law_name("民法")
LawDataProcessor.save_law_data(claw)
# for a in claw.get_all_articles():
#     print(a, "\n")
print(claw.get_table_of_articles())
# claw_2 = LawDataProcessor.load_law_data("刑法")
# print(claw_2.dict())
