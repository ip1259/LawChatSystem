import os
import google.generativeai as genai

KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=KEY)
gen_model = genai.GenerativeModel('gemini-pro')
chat = gen_model.start_chat(history=[])

chat.send_message("你好嗎?")
response = chat.last
print(response)
print(type(chat.history[0]))
print(chat.history)
