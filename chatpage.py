from typing import Any, Callable

import gradio as gr
from fastapi import FastAPI

import AIProcessor
import json
import os


def chatpage_app():
    with gr.Blocks() as chat_page:
        chatbot = gr.Chatbot(layout="bubble", bubble_full_width=False)
        msg = gr.Textbox()
        clear = gr.ClearButton([msg, chatbot])

        def respond(message, chat_history):
            chat_history = AIProcessor.gemini_chat(message, chat_history)
            return "", chat_history

        clear.click(AIProcessor.clean_chatbot)
        msg.submit(respond, [msg, chatbot], [msg, chatbot])

    return chat_page
