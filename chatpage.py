import gradio as gr
import AIProcessor
import json
import os


def chatpage_app():
    with gr.Blocks() as chat_page:
        chatbot = gr.Chatbot()
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])

        def respond(message, chat_history):
            history = AIProcessor.gemini_chat(message)
            chat_history.append(history[-1])
            # print(chat_history)
            return "", chat_history

        clear.click(AIProcessor.clean_chatbot)
        msg.submit(respond, [msg, chatbot], [msg, chatbot])