## FF14 針對繁中版官方維護公告的追蹤器
簡易的追蹤官方不定期發出來的伺服器護維公告
並且將最新的公告發送到相應的dicord頻道中

### 手動執行/自行架設
- 定期執行 python monitor.py
- 請確保環境變數中有 DISCORD_WEBHOOK

### 使用 github action
- 設定 GitHub Secrets (重要步驟)

進入你的 GitHub Repo 頁面。

點擊 Settings > Secrets and variables > Actions。

點擊 New repository secret。

Name 填入：DISCORD_WEBHOOK

Value 填入：你的 Discord Webhook 網址。

- 給予寫入權限 (為了更新 last_news_*.txt)

因為 GitHub Action 需要把新的公告標題寫回 Repo，你需要調整權限：
  
同樣在 Settings > Actions > General。

拉到最下方 Workflow permissions。

勾選 Read and write permissions 並存檔。

#### DISCORD_WEBHOOK 格式
- 支援多頻道同時發送：在 Value 欄位中，將所有 Webhook 網址貼進去，中間用 逗號 分隔。
範例：https://discord.com/api/webhooks/123/abc,https://discord.com/api/webhooks/456/def

### 測試
- 想要手動測試是否架設成功，請砍掉 last_news_*.txt 再執行即可。
