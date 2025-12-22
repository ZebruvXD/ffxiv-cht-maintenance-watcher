import requests
import re
import os
import time
from playwright.sync_api import sync_playwright

# --- 配置區 ---
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
LAST_NEWS_FILE = "last_news_title.txt"

def send_to_discord(title, link, text_content):
    """將文字公告發送到 Discord"""
    # Discord Embed 的內容上限為 4096 字，保險起見截斷在 3000 字
    if len(text_content) > 3000:
        text_content = text_content[:3000] + "\n\n...(內容過長，請點擊連結查看全文)"

    payload = {
        "username": "FFXIV 公告小幫手",
        "embeds": [{
            "title": title,
            "url": link,
            "description": text_content,
            "color": 3447003,  # 藍色
            "footer": {"text": f"擷取時間: {time.strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }

    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if res.status_code in [200, 204]:
        print("✅ 公告已成功發送到 Discord")
    else:
        print(f"❌ 發送失敗，狀態碼: {res.status_code}")

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