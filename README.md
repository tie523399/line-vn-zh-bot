# line-vn-zh-bot

LINE Bot 自動翻譯機器人 - 支援越南語與繁體中文雙向翻譯

## 功能

- 自動檢測輸入語言
- 越南語 ↔ 繁體中文自動翻譯
- 支援簡體中文轉換為越南語
- **文字轉語音（TTS）** - 自動生成並發送語音訊息

## 部署到 Railway

### 步驟

1. **Fork 或 Clone 此專案**

2. **在 Railway 建立新專案**
   - 前往 [Railway](https://railway.app)
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇此專案

3. **設定環境變數**
   在 Railway 專案設定中新增以下環境變數：
   - `LINE_CHANNEL_ACCESS_TOKEN` - LINE Bot Channel Access Token
   - `LINE_CHANNEL_SECRET` - LINE Bot Channel Secret
   - `BASE_URL` - 你的 Railway 公開 URL（例如：`https://你的專案.up.railway.app`）
     - 部署完成後，Railway 會提供公開 URL，將其設定為 `BASE_URL`
     - 如果不設定，系統會嘗試自動偵測，但建議手動設定以確保語音功能正常
   - `PORT` - Railway 會自動設定，無需手動添加

4. **部署**
   - Railway 會自動偵測 Python 專案並開始部署
   - 等待部署完成

5. **設定 LINE Webhook URL**
   - 在 LINE Developers Console 設定 Webhook URL
   - URL 格式：`https://你的專案名稱.railway.app/callback`

## 本地開發

```bash
# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
export LINE_CHANNEL_ACCESS_TOKEN=你的token
export LINE_CHANNEL_SECRET=你的secret
export BASE_URL=http://localhost:8080  # 本地開發時使用

# 執行程式
python main.py
```

## 依賴套件

- flask - Web 框架
- line-bot-sdk - LINE Bot SDK
- googletrans - Google 翻譯 API
- gtts - Google Text-to-Speech（文字轉語音）

## 語音功能說明

機器人會自動為翻譯後的文字生成語音訊息：
- 越南語文字 → 越南語語音
- 繁體中文文字 → 繁體中文語音
- 語音檔案會自動清理（1 小時後過期）
- 需要設定 `BASE_URL` 環境變數以確保語音 URL 正確