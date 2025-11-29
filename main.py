# main.py
from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioSendMessage
from googletrans import Translator
from gtts import gTTS
import os
import io
import uuid
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
translator = Translator()

# 用於儲存臨時音訊檔案的記憶體字典（實際部署時可改用 Redis 等）
audio_cache = {}
cache_lock = threading.Lock()

# 儲存應用基礎 URL（線程安全）
app_base_url = None
url_lock = threading.Lock()

# 清理過期音訊檔案的函數
_last_cleanup_time = None
_cleanup_lock = threading.Lock()  # 用於保護 _last_cleanup_time 的鎖

def cleanup_old_audio():
    """清理超過 1 小時的舊音訊檔案（每 10 分鐘執行一次）"""
    global _last_cleanup_time
    current_time = datetime.now()
    
    # 在鎖內檢查和更新時間戳，確保線程安全
    with _cleanup_lock:
        # 每 10 分鐘才執行一次清理，避免頻繁操作
        if _last_cleanup_time and (current_time - _last_cleanup_time) < timedelta(minutes=10):
            return
        
        # 更新時間戳（在鎖內，確保原子性）
        _last_cleanup_time = current_time
    
    # 在 cache_lock 內執行實際清理操作
    with cache_lock:
        keys_to_delete = [
            key for key, (_, timestamp) in audio_cache.items()
            if current_time - timestamp > timedelta(hours=1)
        ]
        for key in keys_to_delete:
            del audio_cache[key]

def get_base_url():
    """獲取應用基礎 URL（線程安全）"""
    global app_base_url
    
    # 優先使用環境變數
    base_url = os.getenv('BASE_URL', '')
    if base_url:
        with url_lock:
            app_base_url = base_url
        return base_url
    
    # 如果環境變數未設定，嘗試從 Railway 環境變數獲取
    railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
    if railway_domain:
        base_url = f"https://{railway_domain}"
        with url_lock:
            app_base_url = base_url
        return base_url
    
    # 使用已儲存的 URL
    with url_lock:
        if app_base_url:
            return app_base_url
    
    # 如果都沒有，返回空字串（會在 handle_message 中處理）
    return ''

@app.route("/callback", methods=['POST'])
def callback():
    global app_base_url
    signature = request.headers.get('X-Line-Signature', '')
    if not signature:
        abort(400)
    
    body = request.get_data(as_text=True)
    
    # 更新應用基礎 URL（從環境變數或請求中獲取）
    base_url = os.getenv('BASE_URL', '')
    if not base_url:
        # 從請求中構建基礎 URL
        base_url = request.url_root.rstrip('/')
    
    with url_lock:
        app_base_url = base_url

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@app.route("/audio/<audio_id>", methods=['GET'])
def serve_audio(audio_id):
    """提供音訊檔案的下載端點"""
    # 在鎖內複製音訊數據，確保在 send_file 異步傳輸時數據不會被清理
    audio_data = None
    with cache_lock:
        if audio_id in audio_cache:
            audio_data, _ = audio_cache[audio_id]
            # 複製數據到新的 bytes 對象，避免在鎖外訪問時數據被修改
            audio_data = bytes(audio_data)
    
    if audio_data:
        audio_buffer = io.BytesIO(audio_data)
        audio_buffer.seek(0)
        response = send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False
        )
        # 添加必要的 headers 確保 LINE Bot 可以正確訪問
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['Content-Length'] = str(len(audio_data))
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
    abort(404)

def generate_audio(text, lang):
    """生成語音檔案並返回 (音訊資料, 實際使用的文字長度)"""
    # 檢查文字長度（gTTS 限制約 5000 字元）
    original_length = len(text)
    if original_length > 5000:
        text = text[:5000] + "..."
        actual_length = len(text)  # 實際使用的文字長度（包含 "...")
    else:
        actual_length = original_length
    
    # 檢查空文字
    if not text or not text.strip():
        raise ValueError("文字內容為空")
    
    tts = gTTS(text=text, lang=lang, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return (audio_buffer.getvalue(), actual_length)

def get_tts_lang(lang_code):
    """將語言代碼轉換為 gTTS 支援的語言代碼"""
    lang_map = {
        'vi': 'vi',
        'zh-tw': 'zh-tw',
        'zh-cn': 'zh-cn',
        'zh': 'zh-tw'
    }
    return lang_map.get(lang_code, 'vi')

def save_audio_to_cache(audio_data):
    """將音訊資料儲存到快取並返回 ID"""
    audio_id = str(uuid.uuid4())
    with cache_lock:
        audio_cache[audio_id] = (audio_data, datetime.now())
    cleanup_old_audio()
    return audio_id

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        input_text = event.message.text
        
        # 檢查空訊息
        if not input_text or not input_text.strip():
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入要翻譯的文字")
            )
            return
        
        # 語言檢測和翻譯
        detected = translator.detect(input_text)
        src_lang = detected.lang

        if src_lang == 'vi':
            dest_lang = 'zh-tw'
        elif src_lang in ['zh-cn', 'zh-tw']:
            dest_lang = 'vi'
        else:
            dest_lang = 'vi'

        translated = translator.translate(input_text, src=src_lang, dest=dest_lang)
        translated_text = translated.text
        
        # 檢查翻譯結果
        if not translated_text or not translated_text.strip():
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="翻譯失敗，請稍後再試")
            )
            return
        
        # 準備回覆訊息（文字 + 語音）
        messages = [
            TextSendMessage(text=translated_text)
        ]
        
        # 生成語音
        try:
            tts_lang = get_tts_lang(dest_lang)
            audio_data, actual_text_length = generate_audio(translated_text, tts_lang)
            
            # 儲存音訊到快取
            audio_id = save_audio_to_cache(audio_data)
            
            # 獲取音訊 URL
            base_url = get_base_url()
            
            # 如果還是沒有 base_url，嘗試從環境變數獲取
            if not base_url:
                railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
                if railway_domain:
                    base_url = f"https://{railway_domain}"
                else:
                    # 如果都沒有，跳過語音功能
                    raise ValueError("BASE_URL 未設定，無法生成語音 URL")
            
            # 構建完整的音訊 URL（必須是 HTTPS，LINE Bot 要求）
            if not base_url.startswith('http'):
                base_url = f"https://{base_url}"
            elif base_url.startswith('http://'):
                # 將 HTTP 轉換為 HTTPS（LINE Bot 要求 HTTPS）
                base_url = base_url.replace('http://', 'https://', 1)
            
            audio_url = f"{base_url.rstrip('/')}/audio/{audio_id}"
            
            # 計算音訊長度（使用實際使用的文字長度，確保與音訊檔案匹配）
            # gTTS 語速約每秒 5-10 字元，使用更準確的估算：中文和越南語約每秒 8 字元
            duration = max(1000, int(actual_text_length * 125))  # 每個字元約 125 毫秒
            
            # 添加語音訊息（使用 AudioSendMessage 發送音訊給用戶）
            # LINE Bot 要求音訊 URL 必須可公開訪問且使用 HTTPS
            # 注意：音訊檔案必須是 MP3 或 M4A 格式，且大小不超過 10MB
            audio_message = AudioSendMessage(
                original_content_url=audio_url,
                duration=duration
            )
            messages.append(audio_message)
            
            # 調試日誌
            print(f"語音訊息已生成: URL={audio_url}, Duration={duration}ms, Size={len(audio_data)} bytes")
            
        except Exception as e:
            # 如果語音生成失敗，只發送文字（不影響主要功能）
            error_msg = str(e)
            # 只在開發環境輸出詳細錯誤
            if os.getenv('FLASK_ENV') == 'development':
                import traceback
                print(f"語音生成錯誤: {error_msg}")
                traceback.print_exc()
            else:
                print(f"語音生成錯誤: {error_msg}")
        
        # 發送訊息
        line_bot_api.reply_message(
            event.reply_token,
            messages
        )
        
    except Exception as e:
        # 處理整體錯誤
        error_msg = str(e)
        print(f"處理訊息錯誤: {error_msg}")
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="發生錯誤，請稍後再試")
            )
        except:
            pass  # 如果連回覆都失敗，就忽略

# 生產環境使用 gunicorn，開發環境可以直接運行
if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    # 僅在開發環境使用 Flask 內建伺服器
    app.run(host='0.0.0.0', port=port, debug=False)
