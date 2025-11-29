#!/usr/bin/env python3
"""
自動測試和調試腳本
測試 LINE Bot 的所有功能

使用方法:
    python test_bot.py                    # 測試本地服務 (http://localhost:8080)
    python test_bot.py --url https://...  # 測試遠程服務
    BASE_URL=https://... python test_bot.py  # 使用環境變數
"""
import os
import sys
import requests
import time
import argparse
from googletrans import Translator
from gtts import gTTS
import io

# 測試配置
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')
TEST_TEXTS = {
    'vi': 'Xin chào, đây là một tin nhắn thử nghiệm.',
    'zh-tw': '你好，這是一條測試訊息。',
    'zh-cn': '你好，这是一条测试消息。'
}

class Colors:
    """終端顏色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def test_health_check():
    """測試健康檢查端點"""
    print_info("測試健康檢查端點...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"健康檢查通過: {data}")
            return True
        else:
            print_error(f"健康檢查失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print_error(f"健康檢查錯誤: {e}")
        return False

def test_translation():
    """測試翻譯功能"""
    print_info("測試翻譯功能...")
    translator = Translator()
    try:
        for lang, text in TEST_TEXTS.items():
            detected = translator.detect(text)
            if lang == 'vi':
                dest = 'zh-tw'
            elif lang in ['zh-tw', 'zh-cn']:
                dest = 'vi'
            else:
                dest = 'vi'
            
            translated = translator.translate(text, src=detected.lang, dest=dest)
            print_success(f"{lang} → {dest}: {text[:30]}... → {translated.text[:30]}...")
        return True
    except Exception as e:
        print_error(f"翻譯測試失敗: {e}")
        return False

def test_tts_generation():
    """測試 TTS 生成功能"""
    print_info("測試 TTS 生成功能...")
    try:
        test_text = "測試語音生成"
        tts = gTTS(text=test_text, lang='zh-tw', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_data = audio_buffer.getvalue()
        
        if audio_data and len(audio_data) > 0:
            print_success(f"TTS 生成成功: {len(audio_data)} bytes")
            return True
        else:
            print_error("TTS 生成失敗: 音訊資料為空")
            return False
    except Exception as e:
        print_error(f"TTS 測試失敗: {e}")
        return False

def test_m4a_conversion():
    """測試 M4A 轉換功能"""
    print_info("測試 M4A 轉換功能...")
    try:
        from pydub import AudioSegment
        test_text = "測試 M4A 轉換"
        tts = gTTS(text=test_text, lang='zh-tw', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        mp3_data = audio_buffer.getvalue()
        
        # 轉換為 M4A
        audio_segment = AudioSegment.from_mp3(io.BytesIO(mp3_data))
        m4a_buffer = io.BytesIO()
        audio_segment.export(m4a_buffer, format="ipod", codec="aac", bitrate="64k")
        m4a_data = m4a_buffer.getvalue()
        
        if m4a_data and len(m4a_data) > 0:
            print_success(f"M4A 轉換成功: {len(m4a_data)} bytes")
            return True
        else:
            print_error("M4A 轉換失敗: 音訊資料為空")
            return False
    except ImportError:
        print_warning("pydub 未安裝，跳過 M4A 轉換測試")
        return None
    except Exception as e:
        print_error(f"M4A 轉換測試失敗: {e}")
        return False

def test_audio_endpoint():
    """測試音訊端點（需要先有音訊在快取中）"""
    print_info("測試音訊端點...")
    print_warning("此測試需要應用運行並有音訊在快取中")
    # 這個測試需要實際的 audio_id，所以跳過
    return None

def test_environment_variables():
    """測試環境變數"""
    print_info("檢查環境變數...")
    required_vars = ['LINE_CHANNEL_ACCESS_TOKEN', 'LINE_CHANNEL_SECRET']
    optional_vars = ['BASE_URL', 'PORT', 'RAILWAY_PUBLIC_DOMAIN']
    
    all_ok = True
    for var in required_vars:
        if os.getenv(var):
            print_success(f"{var}: 已設定")
        else:
            print_error(f"{var}: 未設定（必需）")
            all_ok = False
    
    for var in optional_vars:
        if os.getenv(var):
            print_success(f"{var}: {os.getenv(var)}")
        else:
            print_warning(f"{var}: 未設定（可選）")
    
    return all_ok

def run_all_tests():
    """運行所有測試"""
    print("=" * 60)
    print("LINE Bot 自動測試和調試")
    print("=" * 60)
    print()
    
    results = {}
    
    # 環境變數檢查
    print("【1/6】環境變數檢查")
    results['env'] = test_environment_variables()
    print()
    
    # 健康檢查
    print("【2/6】健康檢查測試")
    results['health'] = test_health_check()
    print()
    
    # 翻譯測試
    print("【3/6】翻譯功能測試")
    results['translation'] = test_translation()
    print()
    
    # TTS 測試
    print("【4/6】TTS 生成測試")
    results['tts'] = test_tts_generation()
    print()
    
    # M4A 轉換測試
    print("【5/6】M4A 轉換測試")
    results['m4a'] = test_m4a_conversion()
    print()
    
    # 音訊端點測試（跳過）
    print("【6/6】音訊端點測試")
    results['audio'] = test_audio_endpoint()
    print()
    
    # 總結
    print("=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name}: 通過")
        elif result is False:
            print_error(f"{test_name}: 失敗")
        else:
            print_warning(f"{test_name}: 跳過")
    
    print()
    print(f"總計: {total} 項測試")
    print_success(f"通過: {passed}")
    if failed > 0:
        print_error(f"失敗: {failed}")
    if skipped > 0:
        print_warning(f"跳過: {skipped}")
    
    return failed == 0

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='LINE Bot 自動測試和調試工具')
    parser.add_argument('--url', type=str, help='測試的服務 URL (例如: http://localhost:8080)')
    parser.add_argument('--skip-env', action='store_true', help='跳過環境變數檢查')
    args = parser.parse_args()
    
    global BASE_URL
    if args.url:
        BASE_URL = args.url
    
    print_info(f"測試目標: {BASE_URL}")
    print()
    
    success = run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

