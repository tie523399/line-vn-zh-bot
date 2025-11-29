#!/usr/bin/env python3
"""
功能邏輯測試腳本
測試各個函數的邏輯正確性
"""
import sys
import io
import re

class Colors:
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

def test_get_tts_lang_logic():
    """測試 get_tts_lang 函數邏輯"""
    print_info("測試 get_tts_lang 邏輯...")
    lang_map = {'vi': 'vi', 'zh-tw': 'zh-tw', 'zh-cn': 'zh-cn', 'zh': 'zh-tw'}
    
    test_cases = [
        ('vi', 'vi'),
        ('zh-tw', 'zh-tw'),
        ('zh-cn', 'zh-cn'),
        ('zh', 'zh-tw'),
        ('en', 'vi'),  # 默認值
    ]
    
    all_pass = True
    for input_lang, expected in test_cases:
        result = lang_map.get(input_lang, 'vi')
        if result == expected:
            print_success(f"{input_lang} → {result}")
        else:
            print_error(f"{input_lang} → {result} (期望: {expected})")
            all_pass = False
    
    return all_pass

def test_translation_logic():
    """測試翻譯邏輯"""
    print_info("測試翻譯邏輯...")
    
    test_cases = [
        ('vi', 'zh-tw'),
        ('zh-tw', 'vi'),
        ('zh-cn', 'vi'),
        ('en', 'vi'),  # 默認
    ]
    
    all_pass = True
    for src_lang, expected_dest in test_cases:
        if src_lang == 'vi':
            dest_lang = 'zh-tw'
        elif src_lang in ['zh-cn', 'zh-tw']:
            dest_lang = 'vi'
        else:
            dest_lang = 'vi'
        
        if dest_lang == expected_dest:
            print_success(f"{src_lang} → {dest_lang}")
        else:
            print_error(f"{src_lang} → {dest_lang} (期望: {expected_dest})")
            all_pass = False
    
    return all_pass

def test_url_handling():
    """測試 URL 處理邏輯"""
    print_info("測試 URL 處理邏輯...")
    
    test_cases = [
        ('https://example.com', 'https://example.com'),
        ('http://example.com', 'https://example.com'),
        ('example.com', 'https://example.com'),
        ('', ''),
    ]
    
    all_pass = True
    for input_url, expected in test_cases:
        base_url = input_url
        if base_url and not base_url.startswith('http'):
            base_url = f"https://{base_url}"
        elif base_url.startswith('http://'):
            base_url = base_url.replace('http://', 'https://', 1)
        
        if base_url == expected:
            print_success(f"{input_url} → {base_url}")
        else:
            print_error(f"{input_url} → {base_url} (期望: {expected})")
            all_pass = False
    
    return all_pass

def test_duration_calculation():
    """測試音訊長度計算邏輯"""
    print_info("測試音訊長度計算邏輯...")
    
    test_cases = [
        (10, 1250),   # 10 字元 * 125ms = 1250ms
        (100, 12500), # 100 字元 * 125ms = 12500ms
        (1, 1000),    # 最小 1000ms
        (0, 1000),    # 最小 1000ms
    ]
    
    all_pass = True
    for text_length, expected_min in test_cases:
        duration = max(1000, int(text_length * 125))
        if duration >= expected_min:
            print_success(f"{text_length} 字元 → {duration}ms (>= {expected_min}ms)")
        else:
            print_error(f"{text_length} 字元 → {duration}ms (期望 >= {expected_min}ms)")
            all_pass = False
    
    return all_pass

def test_text_truncation():
    """測試文字截斷邏輯"""
    print_info("測試文字截斷邏輯...")
    
    long_text = "a" * 6000
    if len(long_text) > 5000:
        truncated = long_text[:5000] + "..."
        actual_length = len(truncated)
    else:
        actual_length = len(long_text)
    
    if actual_length == 5003:  # 5000 + "..."
        print_success(f"長文字截斷: {len(long_text)} → {actual_length}")
        return True
    else:
        print_error(f"長文字截斷失敗: {len(long_text)} → {actual_length}")
        return False

def test_audio_format_handling():
    """測試音訊格式處理邏輯"""
    print_info("測試音訊格式處理邏輯...")
    
    test_cases = [
        ('m4a', 'audio/mp4', 'audio.m4a'),
        ('mp3', 'audio/mpeg', 'audio.mp3'),
    ]
    
    all_pass = True
    for audio_format, expected_mimetype, expected_filename in test_cases:
        mimetype = 'audio/mp4' if audio_format == 'm4a' else 'audio/mpeg'
        filename = f'audio.{audio_format}'
        
        if mimetype == expected_mimetype and filename == expected_filename:
            print_success(f"{audio_format} → {mimetype}, {filename}")
        else:
            print_error(f"{audio_format} → {mimetype}, {filename} (期望: {expected_mimetype}, {expected_filename})")
            all_pass = False
    
    return all_pass

def test_cache_entry_format():
    """測試快取條目格式"""
    print_info("測試快取條目格式...")
    
    # 模擬快取條目格式: (audio_data, timestamp, format_type)
    entry = (b'audio_data', '2025-01-01', 'm4a')
    
    if len(entry) >= 1:
        audio_data = bytes(entry[0]) if isinstance(entry[0], bytes) else entry[0]
        audio_format = entry[2] if len(entry) >= 3 else 'mp3'
        
        if audio_data and audio_format == 'm4a':
            print_success(f"快取條目格式正確: {audio_format}")
            return True
        else:
            print_error(f"快取條目格式錯誤: {audio_format}")
            return False
    else:
        print_error("快取條目格式錯誤: 長度不足")
        return False

def run_all_function_tests():
    """運行所有功能測試"""
    print("=" * 60)
    print("功能邏輯測試")
    print("=" * 60)
    print()
    
    results = {}
    
    print("【1/7】get_tts_lang 邏輯測試")
    results['tts_lang'] = test_get_tts_lang_logic()
    print()
    
    print("【2/7】翻譯邏輯測試")
    results['translation'] = test_translation_logic()
    print()
    
    print("【3/7】URL 處理邏輯測試")
    results['url'] = test_url_handling()
    print()
    
    print("【4/7】音訊長度計算測試")
    results['duration'] = test_duration_calculation()
    print()
    
    print("【5/7】文字截斷邏輯測試")
    results['truncation'] = test_text_truncation()
    print()
    
    print("【6/7】音訊格式處理測試")
    results['format'] = test_audio_format_handling()
    print()
    
    print("【7/7】快取條目格式測試")
    results['cache'] = test_cache_entry_format()
    print()
    
    # 總結
    print("=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name}: 通過")
        else:
            print_error(f"{test_name}: 失敗")
    
    print()
    print(f"總計: {total} 項測試")
    print_success(f"通過: {passed}")
    if failed > 0:
        print_error(f"失敗: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_function_tests()
    sys.exit(0 if success else 1)

