import gradio as gr


def force_lightmode(app):
    app.load(
        None,
        None,
        js="""
        () => {
        const params = new URLSearchParams(window.location.search);
        if (!params.has('__theme')) {
            params.set('__theme', 'light');
            window.location.search = params.toString();
        }
        }""",
    )


theme = gr.themes.Soft(
    primary_hue="sky",
    secondary_hue="teal",
).set(
    body_background_fill='*neutral_50',
    body_background_fill_dark='*neutral_500',
    block_background_fill='*background_fill_primary',
    block_background_fill_dark='*background_fill_primary'
)

title = "網站首頁"


def homepage_app():
    with gr.Blocks(theme=theme) as demo:
        demo.title = title
        with gr.Row():
            with gr.Column(scale=11):
                gr.Image(value="img/homepage_title.png", container=False, show_download_button=False, min_width=64,
                         width=480,
                         height=100)
            with gr.Column(scale=1, min_width=20):
                gr.Button(value="登入", elem_id="login-button")
        with gr.Row():
            with gr.Column(scale=2, min_width=0):
                pass
            with gr.Column(scale=4):
                with gr.Row():
                    gr.Image(value="img/homepage.jpg", container=False, show_download_button=False, width="40vw")
            with gr.Column(scale=2):
                gr.Markdown(
                    """
                    ## 民法小助手：您的AI法律顧問
                    
                    ### 介紹民法小助手
                    
                    民法小助手是一款AI驅動的民法諮詢聊天機器人，可提供易於理解的法律資訊來幫助您保護您的權益。
                    
                    ### 獲取您的法律問題答案
                    
                    向民法小助手提出有關民法的任何問題，它將使用其自然語言處理功能來理解您的查詢並從政府民法資料庫中為您提供相關資訊。
                    
                    ### 基於聊天的對話
                    
                    民法小助手以對話方式響應您的查詢，使其易於參與並理解提供的法律資訊。
                    
                    ### 免責聲明
                    
                    民法小助手不提供法律建議，其響應不應被視為法律建議。 始終諮詢合格的法律專業人士以獲取法律建議。
                    """
                )
            with gr.Column(scale=2, min_width=0):
                pass
        force_lightmode(demo)
    return demo


homepage_app().launch(auth=("admin", "admin"), server_port=28080)
