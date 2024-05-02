import random
import time

import pandas as pd
import gradio as gr
import AIProcessor
import json
import os


def register(username, password):
    """
  註冊帳號

  Args:
    username: 使用者名稱
    password: 密碼

  Returns:
    是否註冊成功
  """
    # 檢查 users.json 檔案是否存在
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)

    # 檢查使用者名稱是否已存在
    with open("users.json", "r") as f:
        users = json.load(f)
        if username in users:
            return False
        if username == "" or password == "":
            return False

    # 新增帳戶資料
    users[username] = password

    # 儲存帳戶資料
    with open("users.json", "w") as f:
        json.dump(users, f)

    return True


def login(username, password):
    """
  登入帳號

  Args:
    username: 使用者名稱
    password: 密碼

  Returns:
    是否登入成功
  """

    # 檢查 users.json 檔案是否存在
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)

    # 檢查帳戶資料是否存在
    with open("users.json", "r") as f:
        users = json.load(f)
        if username not in users:
            return False

    # 檢查密碼是否正確
    return users[username] == password


def submit(q_str):
    related_articles = AIProcessor.find_related_laws(q_str)
    return AIProcessor.gemini_answer(q_str, related_articles)


def main():
    # with gr.Blocks() as demo:
    #     chatbot = gr.Chatbot()
    #     msg = gr.Textbox()
    #     clear = gr.ClearButton([msg, chatbot])
    #
    #     def respond(message, chat_history):
    #         history = AIProcessor.gemini_chat(message)
    #         chat_history.append(history[-1])
    #         # print(chat_history)
    #         return "", chat_history
    #
    #     clear.click(AIProcessor.clean_chatbot)
    #     msg.submit(respond, [msg, chatbot], [msg, chatbot])
    with gr.Blocks() as main_page:
        tb_username = gr.Textbox(label="帳號", show_label=True)
        tb_password = gr.Textbox(label="密碼", type="password", show_label=True)
        btn_register = gr.Button("註冊")
        btn_login = gr.Button("登入")
        lb_info = gr.Label(label="訊息", show_label=True, value="")

        def login_click(_tb_username, _tb_password):
            if login(_tb_username, _tb_password):
                return [gr.update(visible=True), gr.update(visible=False), gr.update()]
            else:
                lb_info.value = "登入失敗"
                lb_info.render()
                return [gr.update(), gr.update(),  gr.Label(label="訊息", show_label=True, value="登入失敗")]

        def register_click(_tb_username, _tb_password):
            if register(_tb_username, _tb_password):
                return {
                    lb_info: gr.Label(_tb_username + "註冊成功", label="訊息", show_label=True, visible=True)}
            else:
                return {
                    lb_info: gr.Label(_tb_username + "註冊失敗:帳戶已存在", label="訊息", show_label=True,
                                      visible=True)}

        btn_register.click(register_click, inputs=[tb_username, tb_password], outputs=[lb_info])

    with gr.Blocks() as chat_page:
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])
        btn_logout = gr.Button(value="登出")

        def logout(_chatbot):
            AIProcessor.clean_chatbot()
            _chatbot = []
            return [gr.update(visible=False), gr.update(visible=True), _chatbot]

        def respond(message, chat_history):
            history = AIProcessor.gemini_chat(message)
            chat_history.append(history[-1])
            # print(chat_history)
            return "", chat_history

        clear.click(AIProcessor.clean_chatbot)
        msg.submit(respond, [msg, chatbot], [msg, chatbot])

    with gr.Blocks() as demo:
        with gr.Group() as view_main:
            main_page.render()
        with gr.Group(visible=False) as view_chat:
            chat_page.render()

        btn_login.click(login_click, inputs=[tb_username, tb_password], outputs=[view_chat, view_main, lb_info])
        btn_logout.click(logout, inputs=chatbot, outputs=[view_chat, view_main, chatbot])

    demo.launch(share=True)


def test():
    qstr = "假設我的姑姑過世，關於遺產分配順序有甚麼規定?"
    related_articles = AIProcessor.find_related_laws(qstr)
    if related_articles is not None:
        print("相關法條數:", len(related_articles))
    print(AIProcessor.gemini_chat(qstr, related_articles))


def test_gradio():
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])

        def clear_click():
            print("Hello")

        clear.click(clear_click)

        def respond(message, chat_history):
            bot_message = random.choice(["How are you?", "I love you", "I'm very hungry"])
            chat_history.append((message, bot_message))
            time.sleep(2)
            print(chat_history)
            return "", chat_history

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
    demo.launch()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    main()
    # test()
    # test_gradio()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
