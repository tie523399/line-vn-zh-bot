# main.py
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from googletrans import Translator
import os

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
translator = Translator()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    input_text = event.message.text
    detected = translator.detect(input_text)
    src_lang = detected.lang

    if src_lang == 'vi':
        dest_lang = 'zh-tw'
    elif src_lang in ['zh-cn', 'zh-tw']:
        dest_lang = 'vi'
    else:
        dest_lang = 'vi'

    translated = translator.translate(input_text, src=src_lang, dest=dest_lang)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated.text)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
