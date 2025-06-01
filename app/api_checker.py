
NAME = '抗生素'
CODE = '456'
DRUGKIND = '殺菌藥'
TYPE = '自費藥'

API_001_PROMPT_001 = (F"這是我幫助使用者查詢到的結果：\n"
                      F"藥品 {NAME} (藥品碼：{CODE}) 屬於 {DRUGKIND} 類，為 {TYPE}。\n"
                      F"請生成出讓使用者確認是否符合需求的問句。")
print(API_001_PROMPT_001)
# API_001_PROMPT_002 =
# API_001_PROMPT_003 =

# respond = openai.respond(
#     prompt = PROMPT
# )
#
# print(respond)