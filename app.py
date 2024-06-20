import logging

from fastapi import Request, status
from fastapi.responses import RedirectResponse

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
app = gr.mount_gradio_app(app, cp, path="/chat")#, auth=("admin", "admin")
host = os.getenv("SERVER_HOST")
port = int(os.getenv("SERVER_PORT"))


@app.get('/')
async def index():
    return RedirectResponse("http://" + host + ":" + str(port) + "/home", status_code=status.HTTP_303_SEE_OTHER)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host=host, port=port)
