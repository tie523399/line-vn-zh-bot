#!/usr/bin/env python3
"""
自動測試和修復腳本
自動檢測問題並修復
"""
import os
import sys
import subprocess
import re
import ast

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

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def check_python_syntax(file_path):
    """檢查 Python 語法"""
    print_info(f"檢查 {file_path} 語法...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print_success(f"{file_path} 語法正確")
        return True
    except SyntaxError as e:
        print_error(f"{file_path} 語法錯誤: {e}")
        return False
    except Exception as e:
        print_error(f"{file_path} 讀取錯誤: {e}")
        return False

def check_imports(file_path):
    """檢查導入語句"""
    print_info(f"檢查 {file_path} 導入...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有明顯的導入問題
        required_imports = [
            'from flask import',
            'from linebot import',
            'from googletrans import',
            'from gtts import'
        ]
        
        missing = []
        for imp in required_imports:
            if imp not in content:
                missing.append(imp)
        
        if missing:
            print_warning(f"可能缺少導入: {', '.join(missing)}")
        else:
            print_success("導入檢查通過")
        return True
    except Exception as e:
        print_error(f"導入檢查錯誤: {e}")
        return False

def check_code_issues(file_path):
    """檢查代碼問題"""
    print_info(f"檢查 {file_path} 代碼問題...")
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 檢查是否有日誌輸出被插入到代碼中
        for i, line in enumerate(lines, 1):
            # 檢查是否有 Flask 啟動日誌在代碼中
            if 'Starting Container' in line or '* Running on http://' in line:
                issues.append(f"第 {i} 行: 發現日誌輸出被插入到代碼中")
            # 檢查是否有棄用警告在代碼中
            if 'LineBotSdkDeprecatedIn30' in line and ':' not in line:
                issues.append(f"第 {i} 行: 發現警告訊息在代碼中")
            # 檢查是否有 HTTP 日誌在代碼中
            if re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line.strip()):
                issues.append(f"第 {i} 行: 發現 HTTP 日誌在代碼中")
        
        if issues:
            print_error(f"發現 {len(issues)} 個問題:")
            for issue in issues:
                print_error(f"  {issue}")
            return False, issues
        else:
            print_success("未發現明顯代碼問題")
            return True, []
    except Exception as e:
        print_error(f"代碼檢查錯誤: {e}")
        return False, [str(e)]

def fix_code_issues(file_path, issues):
    """修復代碼問題"""
    print_info(f"嘗試修復 {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            # 跳過包含日誌輸出的行
            if any(keyword in line for keyword in [
                'Starting Container',
                '* Running on http://',
                'Press CTRL+C to quit',
                'LineBotSdkDeprecatedIn30',
                'WARNING: This is a development server',
                '* Serving Flask app',
                '* Debug mode:',
                '* Running on all addresses'
            ]):
                # 檢查是否是註釋或字符串中的內容
                stripped = line.strip()
                if not stripped.startswith('#') and not (stripped.startswith('"') or stripped.startswith("'")):
                    print_warning(f"移除第 {i+1} 行: {line.strip()[:50]}...")
                    continue
            
            # 跳過 HTTP 日誌行
            if re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line.strip()):
                print_warning(f"移除第 {i+1} 行: HTTP 日誌")
                continue
            
            fixed_lines.append(line)
        
        # 寫回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        
        print_success(f"{file_path} 已修復")
        return True
    except Exception as e:
        print_error(f"修復錯誤: {e}")
        return False

def check_file_structure():
    """檢查文件結構"""
    print_info("檢查文件結構...")
    required_files = ['main.py', 'requirements.txt', 'Procfile']
    missing = []
    
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file} 存在")
        else:
            print_error(f"{file} 不存在")
            missing.append(file)
    
    return len(missing) == 0

def check_requirements():
    """檢查 requirements.txt"""
    print_info("檢查 requirements.txt...")
    if not os.path.exists('requirements.txt'):
        print_error("requirements.txt 不存在")
        return False
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_packages = ['flask', 'line-bot-sdk', 'googletrans', 'gtts', 'gunicorn']
        missing = []
        
        for pkg in required_packages:
            if pkg not in content:
                missing.append(pkg)
        
        if missing:
            print_warning(f"可能缺少套件: {', '.join(missing)}")
        else:
            print_success("requirements.txt 看起來完整")
        
        return True
    except Exception as e:
        print_error(f"檢查 requirements.txt 錯誤: {e}")
        return False

def test_main_functions():
    """測試 main.py 中的函數定義"""
    print_info("檢查 main.py 函數定義...")
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            'cleanup_old_audio',
            'get_base_url',
            'callback',
            'health_check',
            'serve_audio',
            'generate_audio',
            'get_tts_lang',
            'save_audio_to_cache',
            'handle_message'
        ]
        
        missing = []
        for func in required_functions:
            if f'def {func}(' not in content:
                missing.append(func)
        
        if missing:
            print_error(f"缺少函數: {', '.join(missing)}")
            return False
        else:
            print_success("所有必需函數都存在")
            return True
    except Exception as e:
        print_error(f"檢查函數定義錯誤: {e}")
        return False

def run_all_checks():
    """運行所有檢查"""
    print("=" * 60)
    print("自動測試和修復")
    print("=" * 60)
    print()
    
    results = {}
    issues_found = []
    
    # 1. 檢查文件結構
    print("【1/7】文件結構檢查")
    results['structure'] = check_file_structure()
    print()
    
    # 2. 檢查 requirements.txt
    print("【2/7】requirements.txt 檢查")
    results['requirements'] = check_requirements()
    print()
    
    # 3. 檢查 main.py 語法
    print("【3/7】main.py 語法檢查")
    results['syntax'] = check_python_syntax('main.py')
    print()
    
    # 4. 檢查導入
    print("【4/7】導入檢查")
    results['imports'] = check_imports('main.py')
    print()
    
    # 5. 檢查代碼問題
    print("【5/7】代碼問題檢查")
    ok, issues = check_code_issues('main.py')
    results['code_issues'] = ok
    if issues:
        issues_found.extend(issues)
    print()
    
    # 6. 修復問題
    if issues:
        print("【6/7】自動修復")
        results['fix'] = fix_code_issues('main.py', issues)
        # 重新檢查語法
        if results['fix']:
            results['syntax_after_fix'] = check_python_syntax('main.py')
        print()
    else:
        print("【6/7】自動修復")
        print_success("無需修復")
        results['fix'] = True
        print()
    
    # 7. 檢查函數定義
    print("【7/7】函數定義檢查")
    results['functions'] = test_main_functions()
    print()
    
    # 總結
    print("=" * 60)
    print("檢查總結")
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
    print(f"總計: {total} 項檢查")
    print_success(f"通過: {passed}")
    if failed > 0:
        print_error(f"失敗: {failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)

