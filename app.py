import homepage
import chatpage
from fastapi import FastAPI
import gradio as gr
import uvicorn
import dotenv
import os

hp = homepage.homepage_app()
cp = chatpage.chatpage_app()
dotenv.load_dotenv()

app = FastAPI()
app = gr.mount_gradio_app(app, hp, path="/home")
app = gr.mount_gradio_app(app, cp, path="/chat", auth=("admin", "admin"))
host = os.getenv("SERVER_HOST")
port = int(os.getenv("SERVER_PORT"))

uvicorn.run(app, host=host, port=port)
