#!/usr/bin/env python3
"""
設定 LINE Bot 介紹訊息和個人資料
"""
import os
import sys
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError

def set_bot_profile():
    """設定 Bot 的個人資料（名稱、介紹）"""
    channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not channel_access_token:
        print("錯誤: 請設定 LINE_CHANNEL_ACCESS_TOKEN 環境變數")
        return False
    
    line_bot_api = LineBotApi(channel_access_token)
    
    # Bot 個人資料設定
    # 注意：這些設定需要 LINE Developers Console 中的權限
    # 如果沒有權限，請在 LINE Developers Console 中手動設定
    
    print("=" * 60)
    print("LINE Bot 個人資料設定")
    print("=" * 60)
    print()
    
    try:
        # 獲取當前 Bot 資訊
        profile = line_bot_api.get_bot_info()
        print(f"當前 Bot 名稱: {profile.display_name}")
        print(f"當前 Bot ID: {profile.user_id}")
        print()
        
        print("注意: Bot 的個人資料（名稱、頭像、介紹）需要在 LINE Developers Console 中設定")
        print("網址: https://developers.line.biz/console/")
        print()
        print("設定步驟:")
        print("1. 登入 LINE Developers Console")
        print("2. 選擇您的 Channel")
        print("3. 進入 'Messaging API' 頁面")
        print("4. 在 'Bot basic information' 區塊中設定:")
        print("   - Bot name (Bot 名稱)")
        print("   - Bot icon (Bot 頭像)")
        print("   - Description (Bot 介紹)")
        print()
        
        return True
        
    except LineBotApiError as e:
        print(f"API 錯誤: {e.status_code} - {e.message}")
        return False
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def set_greeting_message():
    """設定歡迎訊息（Greeting Message）"""
    channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
    if not channel_access_token:
        print("錯誤: 請設定 LINE_CHANNEL_ACCESS_TOKEN 環境變數")
        return False
    
    line_bot_api = LineBotApi(channel_access_token)
    
    # 歡迎訊息內容
    greeting_text = """你好！我是越南語-繁體中文翻譯機器人 🤖

我可以幫你：
• 自動翻譯越南語 ↔ 繁體中文
• 將翻譯結果轉換為語音播放 🔊

使用方法：
直接輸入要翻譯的文字，我會自動檢測語言並翻譯！

支援的語言：
🇻🇳 越南語
🇹🇼 繁體中文
🇨🇳 簡體中文

試試看吧！"""
    
    print("=" * 60)
    print("設定歡迎訊息")
    print("=" * 60)
    print()
    
    try:
        # 設定歡迎訊息
        line_bot_api.set_webhook_endpoint("")  # 先清空（如果需要）
        
        # 注意：LINE Bot API v2 中，歡迎訊息需要通過 Rich Menu 或 Webhook 來實現
        # 或者可以在 LINE Developers Console 中設定
        
        print("歡迎訊息內容:")
        print("-" * 60)
        print(greeting_text)
        print("-" * 60)
        print()
        print("設定方法:")
        print("1. 在 LINE Developers Console 中設定")
        print("   網址: https://developers.line.biz/console/")
        print("   路徑: Messaging API > Greeting messages")
        print()
        print("2. 或使用以下 Python 代碼（需要適當的權限）:")
        print()
        print("""
from linebot.models import TextSendMessage

# 當用戶加入好友時發送歡迎訊息
@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=greeting_text)
    )
""")
        print()
        
        return True
        
    except LineBotApiError as e:
        print(f"API 錯誤: {e.status_code} - {e.message}")
        return False
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def add_follow_event_handler():
    """在 main.py 中添加 Follow 事件處理器"""
    print("=" * 60)
    print("添加 Follow 事件處理器")
    print("=" * 60)
    print()
    
    greeting_code = '''
@handler.add(FollowEvent)
def handle_follow(event):
    """處理用戶加入好友事件"""
    greeting_text = """你好！我是越南語-繁體中文翻譯機器人 🤖

我可以幫你：
• 自動翻譯越南語 ↔ 繁體中文
• 將翻譯結果轉換為語音播放 🔊

使用方法：
直接輸入要翻譯的文字，我會自動檢測語言並翻譯！

支援的語言：
🇻🇳 越南語
🇹🇼 繁體中文
🇨🇳 簡體中文

試試看吧！"""
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=greeting_text)
    )
'''
    
    print("要在 main.py 中添加歡迎訊息功能，請添加以下代碼:")
    print("-" * 60)
    print(greeting_code)
    print("-" * 60)
    print()
    print("需要修改的地方:")
    print("1. 在導入部分添加: from linebot.models import FollowEvent")
    print("2. 在 handle_message 函數後添加上述 handle_follow 函數")
    print()
    
    return greeting_code

def main():
    """主函數"""
    print("LINE Bot 介紹訊息設定工具")
    print("=" * 60)
    print()
    
    # 1. 顯示 Bot 資訊
    print("【1/3】檢查 Bot 資訊")
    set_bot_profile()
    print()
    
    # 2. 顯示歡迎訊息設定方法
    print("【2/3】歡迎訊息設定")
    set_greeting_message()
    print()
    
    # 3. 提供代碼範例
    print("【3/3】代碼範例")
    add_follow_event_handler()
    print()
    
    print("=" * 60)
    print("完成！")
    print("=" * 60)
    print()
    print("提示:")
    print("- 個人資料和介紹訊息可以在 LINE Developers Console 中設定")
    print("- 歡迎訊息可以通過 FollowEvent 處理器自動發送")
    print("- 或者使用 Rich Menu 來提供更好的用戶體驗")

if __name__ == "__main__":
    main()

