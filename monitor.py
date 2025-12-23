import requests
import re
import os
import time
from playwright.sync_api import sync_playwright

# --- 配置區 ---
webhook_raw = os.environ.get("DISCORD_WEBHOOK", "")
DISCORD_WEBHOOK_URLS = [url.strip() for url in webhook_raw.split(",") if url.strip()]

CATEGORIES = [3, 4]
# 黑名單 ID 清單 (字串格式)
CAT4_BLACKLIST = ["3", "46", "65"]

def send_to_discord(title, link, text_content):
    if not DISCORD_WEBHOOK_URLS:
        print("⚠️ 未設定 Discord Webhook")
        return

    # Discord 限制 Embed description 為 4096 字
    if len(text_content) > 3000:
        text_content = text_content[:3000] + "\n\n...(內容過長，請點擊連結查看全文)"

    payload = {
        "username": "FFXIV 光之工具人",
        "embeds": [{
            "title": title,
            "url": link,
            "description": text_content,
            "color": 3447003
        }]
    }

    for url in DISCORD_WEBHOOK_URLS:
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            print(f"發送失敗: {e}")

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for cat in CATEGORIES:
            try:
                url = f"https://www.ffxiv.com.tw/web/news/news_list.aspx?category={cat}"
                print(f"正在檢查分類 {cat}: {url}")
                page.goto(url, timeout=60000)
                page.wait_for_selector(".news_list .item")

                # 抓取該頁所有的公告項目
                all_items = page.query_selector_all(".news_list .item")

                target_item = None
                target_id = None

                # 尋找第一篇「不在黑名單內」的公告
                for item in all_items:
                    current_id = item.query_selector(".news_id").inner_text().strip()

                    if cat == 4 and current_id in CAT4_BLACKLIST:
                        print(f"⏩ 略過黑名單編號: {current_id}")
                        continue

                    # 找到第一篇合格的，就鎖定它並跳出迴圈
                    target_item = item
                    target_id = current_id
                    break

                if not target_item:
                    print(f"分類 {cat} 在過濾後沒有可抓取的公告。")
                    continue

                # 取得標題與連結
                title_link = target_item.query_selector(".title a")
                title = title_link.inner_text().strip()
                link = "https://www.ffxiv.com.tw" + title_link.get_attribute("href")

                # 檢查是否已更新過 (每個分類獨立檔案)
                record_file = f"last_news_id_{cat}.txt"
                if os.path.exists(record_file):
                    with open(record_file, "r", encoding="utf-8") as f:
                        if f.read().strip() == target_id:
                            print(f"😴 分類 {cat} 已是最新狀態 (ID: {target_id})。")
                            continue

                # 進入內文頁抓取 .article
                print(f"🔔 發現新公告: {title} (ID: {target_id})")
                page.goto(link, timeout=60000)
                page.wait_for_selector(".article")

                # 獲取 article 元素
                article_element = page.query_selector(".article")

                # 使用 inner_text() 並嘗試手動清理一些 HTML 殘留
                # inner_text 會嘗試模仿瀏覽器渲染的排版（包含縮排）
                article_text = article_element.inner_text().strip()

                # 核心邏輯：匹配所有連續 2 個以上的 \n，並將每一組匹配到的長度都減 1
                def subtract_one(match):
                    full_match = match.group(0)
                    # 返回長度減 1 的換行字串
                    return '\n' * (len(full_match) - 1)

                # re.sub 會尋找所有符合條件的地方，但每一處只會執行一次 lambda 轉換
                compact_text = re.sub(r'\n{2,}', subtract_one, article_text)
                # 4. 包裹進代碼塊
                formatted_text = f"```\n{compact_text}\n```"

                # 發送通知
                category_name = "伺服器維護" if cat == 3 else "公告"
                send_to_discord(f"[{category_name}] {title}", link, formatted_text)

                # 更新紀錄檔
                with open(record_file, "w", encoding="utf-8") as f:
                    f.write(target_id)

            except Exception as e:
                print(f"分類 {cat} 執行出錯: {e}")

        browser.close()

if __name__ == "__main__":
    run_scraper()