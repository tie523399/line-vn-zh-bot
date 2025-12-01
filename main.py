# main.py
from flask import Flask, request, abort, send_file, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioSendMessage, FollowEvent
from googletrans import Translator
from gtts import gTTS
import os
import io
import uuid
import threading
from datetime import datetime, timedelta

# 嘗試導入 pydub 用於格式轉換
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
translator = Translator()

# 音訊快取和鎖
audio_cache = {}
cache_lock = threading.Lock()
app_base_url = None
url_lock = threading.Lock()
_last_cleanup_time = None
_cleanup_lock = threading.Lock()

def cleanup_old_audio():
    """清理超過 24 小時的舊音訊檔案"""
    global _last_cleanup_time
    current_time = datetime.now()
    with _cleanup_lock:
        if _last_cleanup_time and (current_time - _last_cleanup_time) < timedelta(minutes=10):
            return
        _last_cleanup_time = current_time
    with cache_lock:
        keys_to_delete = [k for k, v in audio_cache.items() 
                         if len(v) >= 2 and current_time - v[1] > timedelta(hours=24)]
        for k in keys_to_delete:
            del audio_cache[k]

def get_base_url():
    """獲取應用基礎 URL"""
    global app_base_url
    base_url = os.getenv('BASE_URL', '') or os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
    if base_url and not base_url.startswith('http'):
        base_url = f"https://{base_url}"
    if base_url:
        with url_lock:
            app_base_url = base_url
        return base_url
    with url_lock:
        return app_base_url or ''

@app.route("/callback", methods=['POST'])
def callback():
    global app_base_url
    signature = request.headers.get('X-Line-Signature', '')
    if not signature:
        abort(400)
    body = request.get_data(as_text=True)
    base_url = os.getenv('BASE_URL', '') or request.url_root.rstrip('/')
    with url_lock:
        app_base_url = base_url
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@app.route("/", methods=['GET'])
def health_check():
    """健康檢查端點，顯示 HTML 頁面（用於分享預覽）和 JSON API"""
    # 檢查是否請求 JSON 格式
    if request.headers.get('Accept', '').find('application/json') != -1:
        return {
            "status": "ok",
            "service": "LINE Bot Translation Service",
            "description": "免費越南語-繁體中文翻譯機器人，支援語音播放",
            "features": [
                "自動翻譯越南語 ↔ 繁體中文",
                "簡體中文 → 越南語",
                "文字轉語音播放"
            ],
            "usage": "加好友關注即可免費使用，直接輸入文字即可翻譯",
            "contact": {
                "id": "0002738",
                "phone": "0963858005",
                "services": [
                    "網站開發",
                    "程序開發",
                    "機器人開發",
                    "AI 程序開發",
                    "廣告服務"
                ]
            },
            "endpoints": {
                "health": "/",
                "webhook": "/callback",
                "audio": "/audio/<audio_id>"
            }
        }
    
    # 返回 HTML 頁面（用於分享預覽）
    base_url = get_base_url() or request.url_root.rstrip('/')
    return render_template('index.html', base_url=base_url)

@app.route("/audio/<audio_id>", methods=['GET'])
def serve_audio(audio_id):
    """提供音訊檔案的下載端點"""
    audio_data = None
    audio_format = 'mp3'
    with cache_lock:
        if audio_id in audio_cache:
            entry = audio_cache[audio_id]
            if len(entry) >= 1:
                audio_data = bytes(entry[0])
                audio_format = entry[2] if len(entry) >= 3 else 'mp3'
    if not audio_data:
        abort(404)
    mimetype = 'audio/mp4' if audio_format == 'm4a' else 'audio/mpeg'
    filename = f'audio.{audio_format}'
    response = send_file(io.BytesIO(audio_data), mimetype=mimetype, as_attachment=False)
    response.headers.update({
        'Content-Type': mimetype,
        'Content-Length': str(len(audio_data)),
        'Accept-Ranges': 'bytes',
        'Cache-Control': 'public, max-age=3600',
        'Access-Control-Allow-Origin': '*',
        'Content-Disposition': f'inline; filename="{filename}"'
    })
    return response

def generate_audio(text, lang, format_type='m4a'):
    """生成語音檔案並返回 (音訊資料, 實際使用的文字長度, 格式類型)"""
    if len(text) > 5000:
        text = text[:5000] + "..."
    actual_length = len(text)
    if not text or not text.strip():
        raise ValueError("No text to send to TTS API")
    tts = gTTS(text=text, lang=lang, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_data = audio_buffer.getvalue()
    if not audio_data:
        raise ValueError("生成的音訊資料為空")
    if format_type == 'm4a' and PYDUB_AVAILABLE:
        try:
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
            m4a_buffer = io.BytesIO()
            # 使用 'ipod' 格式（ffmpeg 支持），這會生成 M4A/AAC 格式
            audio_segment.export(m4a_buffer, format="ipod", codec="aac", bitrate="64k")
            audio_data = m4a_buffer.getvalue()
            print(f"音訊已轉換為 M4A，大小: {len(audio_data)} bytes")
        except Exception as e:
            print(f"M4A 轉換失敗，使用 MP3: {e}")
            format_type = 'mp3'
    return (audio_data, actual_length, format_type)

def get_tts_lang(lang_code):
    """將語言代碼轉換為 gTTS 支援的語言代碼"""
    lang_map = {'vi': 'vi', 'zh-tw': 'zh-tw', 'zh-cn': 'zh-cn', 'zh': 'zh-tw'}
    return lang_map.get(lang_code, 'vi')

def save_audio_to_cache(audio_data, audio_format='m4a'):
    """將音訊資料儲存到快取並返回 ID"""
    audio_id = str(uuid.uuid4())
    with cache_lock:
        audio_cache[audio_id] = (audio_data, datetime.now(), audio_format)
    cleanup_old_audio()
    return audio_id

@handler.add(FollowEvent)
def handle_follow(event):
    """處理用戶加入好友事件 - 發送歡迎訊息"""
    greeting_text = """🎉 歡迎使用免費翻譯機器人！

✅ 加好友關注即可免費使用
✅ 無需付費，無需註冊
✅ 隨時隨地使用

📚 使用教學：

【個人聊天使用】
1️⃣ 直接輸入文字
   輸入任何越南語或中文文字

2️⃣ 自動翻譯
   我會自動檢測語言並翻譯

3️⃣ 語音播放
   翻譯結果會自動轉換為語音 🔊

【群組使用】
1️⃣ 將我加入群組
   • 點擊群組右上角「...」
   • 選擇「邀請」
   • 搜尋並選擇我加入群組

2️⃣ 在群組中使用
   • 直接在群組中輸入要翻譯的文字
   • 我會自動回覆翻譯結果和語音

3️⃣ 群組設定
   • 確保我有發送訊息的權限
   • 可以 @我 來提醒我回應

🌍 支援語言：
   🇻🇳 越南語 ↔ 🇹🇼 繁體中文
   🇨🇳 簡體中文 → 🇻🇳 越南語

💡 使用範例：
   • 輸入「Xin chào」→ 翻譯成「你好」
   • 輸入「你好」→ 翻譯成「Xin chào」

現在就試試看吧！直接輸入文字即可開始使用 🚀

━━━━━━━━━━━━━━━━━━━━
💼 專業服務諮詢

如需以下服務，歡迎聯繫我：
• 🌐 網站開發
• 💻 程序開發
• 🤖 機器人開發
• 🤖 AI 程序開發
• 📢 廣告服務

📞 聯繫方式：
   ID: 0002738
   電話: 0963858005

隨時為您提供專業服務！"""
    
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=greeting_text)
        )
    except Exception as e:
        print(f"發送歡迎訊息錯誤: {e}")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        input_text = event.message.text
        if not input_text or not input_text.strip():
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入要翻譯的文字"))
            return
        detected = translator.detect(input_text)
        src_lang = detected.lang
        dest_lang = 'zh-tw' if src_lang == 'vi' else 'vi' if src_lang in ['zh-cn', 'zh-tw'] else 'vi'
        translated = translator.translate(input_text, src=src_lang, dest=dest_lang)
        translated_text = translated.text
        if not translated_text or not translated_text.strip():
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="翻譯失敗，請稍後再試"))
            return
        messages = [TextSendMessage(text=translated_text)]
        try:
            tts_lang = get_tts_lang(dest_lang)
            audio_data, actual_text_length, audio_format = generate_audio(translated_text, tts_lang, 'm4a')
            audio_id = save_audio_to_cache(audio_data, audio_format)
            base_url = get_base_url() or os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
            if not base_url:
                raise ValueError("BASE_URL 未設定")
            if not base_url.startswith('http'):
                base_url = f"https://{base_url}"
            elif base_url.startswith('http://'):
                base_url = base_url.replace('http://', 'https://', 1)
            audio_url = f"{base_url.rstrip('/')}/audio/{audio_id}"
            duration = max(1000, int(actual_text_length * 125))
            audio_message = AudioSendMessage(original_content_url=audio_url, duration=duration)
            messages.append(audio_message)
            print(f"語音已生成: {audio_url}, {duration}ms, {len(audio_data)} bytes, {audio_format}")
        except Exception as e:
            print(f"語音生成錯誤: {e}")
        line_bot_api.reply_message(event.reply_token, messages)
    except Exception as e:
        print(f"處理訊息錯誤: {e}")
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="發生錯誤，請稍後再試"))
        except:
            pass

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
