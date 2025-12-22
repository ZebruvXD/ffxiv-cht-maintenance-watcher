import requests
import re
import os
import time
from playwright.sync_api import sync_playwright

# --- 配置區 ---
webhook_raw = os.environ.get("DISCORD_WEBHOOK", "")
DISCORD_WEBHOOK_URLS = [url.strip() for url in webhook_raw.split(",") if url.strip()]
LAST_NEWS_FILE = "last_news_title.txt"

def send_to_discord(title, link, text_content):
    """發送到所有設定的 Discord Webhooks"""
    if len(text_content) > 3000:
        text_content = text_content[:3000] + "\n\n...(內容過長)"

    payload = {
        "username": "FFXIV 公告小幫手",
        "embeds": [{
            "title": title,
            "url": link,
            "description": text_content,
            "color": 3447003,
        }]
    }

    # 遍歷所有網址發送
    for url in DISCORD_WEBHOOK_URLS:
        try:
            res = requests.post(url, json=payload)
            if res.status_code in [200, 204]:
                print(f"✅ 成功發送到 Webhook: {url[:30]}...")
            else:
                print(f"❌ 發送失敗 ({res.status_code}): {url[:30]}...")
        except Exception as e:
            print(f"發送至 {url[:30]} 時發生異常: {e}")

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. 列表頁抓連結
        try:
            page.goto("https://www.ffxiv.com.tw/web/news/news_list.aspx?category=3", timeout=60000)
            page.wait_for_selector(".news_list .item")

            first_item = page.query_selector(".news_list .item")
            title = first_item.query_selector(".title a").inner_text().strip()
            link = "https://www.ffxiv.com.tw" + first_item.query_selector(".title a").get_attribute("href")

            # 檢查是否已發送過
            if os.path.exists(LAST_NEWS_FILE):
                with open(LAST_NEWS_FILE, "r", encoding="utf-8") as f:
                    if f.read().strip() == title:
                        print(f"😴 已處理過最新公告: {title}")
                        return

            # 2. 進入內文頁抓取 .article
            page.goto(link, timeout=60000)
            page.wait_for_selector(".article")

            # 使用 inner_text() 可以保留大部分的換行與縮排排版
            article_element = page.query_selector(".article")
            raw_text = article_element.inner_text().strip()

            # 簡單清理：將三個以上的連續換行縮減為兩個，保持段落感但不浪費空間
            formatted_text = re.sub(r'\n{3,}', '\n\n', raw_text)

            # 3. 執行發送
            send_to_discord(title, link, formatted_text)

            # 4. 更新紀錄
            with open(LAST_NEWS_FILE, "w", encoding="utf-8") as f:
                f.write(title)

        except Exception as e:
            print(f"發生錯誤: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_scraper()