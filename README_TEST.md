# 自動測試和調試工具

## 簡介

`test_bot.py` 是一個自動化測試腳本，用於測試 LINE Bot 的所有核心功能。

## 功能

- ✅ 環境變數檢查
- ✅ 健康檢查端點測試
- ✅ 翻譯功能測試
- ✅ TTS 生成測試
- ✅ M4A 轉換測試
- ✅ 彩色終端輸出

## 使用方法

### 1. 測試本地服務

```bash
# 確保服務正在運行
python main.py

# 在另一個終端運行測試
python test_bot.py
```

### 2. 測試遠程服務（Railway）

```bash
# 使用命令行參數
python test_bot.py --url https://your-app.up.railway.app

# 或使用環境變數
BASE_URL=https://your-app.up.railway.app python test_bot.py
```

### 3. 跳過環境變數檢查

```bash
python test_bot.py --skip-env
```

## 測試項目

### 1. 環境變數檢查
- 檢查必需的環境變數（LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET）
- 檢查可選的環境變數（BASE_URL, PORT, RAILWAY_PUBLIC_DOMAIN）

### 2. 健康檢查測試
- 測試 `/` 端點
- 驗證返回的 JSON 格式

### 3. 翻譯功能測試
- 測試越南語 → 繁體中文
- 測試繁體中文 → 越南語
- 測試簡體中文 → 越南語

### 4. TTS 生成測試
- 測試 gTTS 音訊生成
- 驗證音訊資料不為空

### 5. M4A 轉換測試
- 測試 MP3 到 M4A 轉換（如果 pydub 可用）
- 驗證轉換後的音訊資料

## 輸出說明

- ✓ 綠色：測試通過
- ✗ 紅色：測試失敗
- ⚠ 黃色：警告或跳過的測試
- ℹ 藍色：信息提示

## 依賴

測試腳本需要以下套件：
- `requests` - HTTP 請求
- `googletrans` - 翻譯功能
- `gtts` - TTS 功能
- `pydub` - M4A 轉換（可選）

所有依賴已包含在 `requirements.txt` 中。

## 故障排除

### 連接錯誤
如果遇到連接錯誤，請確保：
1. 服務正在運行
2. BASE_URL 設定正確
3. 防火牆允許連接

### M4A 轉換失敗
如果 M4A 轉換測試失敗：
1. 檢查 `pydub` 是否已安裝
2. 檢查 `ffmpeg` 是否可用
3. 查看錯誤訊息以獲取詳細信息

## 示例輸出

```
============================================================
LINE Bot 自動測試和調試
============================================================

ℹ 測試目標: http://localhost:8080

【1/6】環境變數檢查
✓ LINE_CHANNEL_ACCESS_TOKEN: 已設定
✓ LINE_CHANNEL_SECRET: 已設定
✓ BASE_URL: http://localhost:8080

【2/6】健康檢查測試
ℹ 測試健康檢查端點...
✓ 健康檢查通過: {'status': 'ok', 'service': 'LINE Bot Translation Service'}

【3/6】翻譯功能測試
ℹ 測試翻譯功能...
✓ vi → zh-tw: Xin chào, đây là một tin nhắn... → 你好，這是一條測試訊息...

...

============================================================
測試總結
============================================================
✓ env: 通過
✓ health: 通過
✓ translation: 通過
✓ tts: 通過
✓ m4a: 通過
⚠ audio: 跳過

總計: 6 項測試
✓ 通過: 5
⚠ 跳過: 1
```

