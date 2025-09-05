import csv
import time
import re
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://transit.yahoo.co.jp/search/result"
DESTINATIONS = ["三田", "田町"]
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_routes(frm, to):
    params = {"from": frm, "to": to, "plane": "off"}
    html = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=10).text
    soup = BeautifulSoup(html, "lxml")

    routes = {}
    for li in soup.select("ul.routeList li"):
        # どのルートか（早・安・乗換少）をアイコンから判定
        if li.select_one(".icnPriTime"):
            key = "fast"
        elif li.select_one(".icnPriFare"):
            key = "cheap"
        elif li.select_one(".icnPriTrans"):
            key = "few"
        else:
            continue

        # 運賃
        fare_tag = li.select_one(".fare .mark")
        fare = int(fare_tag.text.replace(",", "").replace("円", "")) if fare_tag else None

        # 定期代
        pass_tag = li.select_one(".farePass .mark")  # 画像の部分
        pass_price = (
            int(pass_tag.text.replace(",", "").replace("円", "")) if pass_tag else None
        )

        # 所要時間（「1時間20分」形式を分に変換）
        time_tag = li.select_one(".time .mark")
        if time_tag:
            m = re.search(r'(?:(\d+)時間)?(\d+)分', time_tag.text)
            minutes = int(m.group(1) or 0) * 60 + int(m.group(2))
        else:
            minutes = None

        # 乗換回数
        transfer_tag = li.select_one(".transfer .mark")
        if transfer_tag:
            m = re.search(r'(\d+)回', transfer_tag.text)
            transfer = int(m.group(1)) if m else 0
        else:
            transfer = 0

        routes[key] = {
            "fare": fare,
            "pass_price": pass_price,
            "minutes": minutes,
            "transfer": transfer,
        }
    return routes

with open("stations.csv", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        departure = row[0].strip()
        if not departure:
            continue
        for dest in DESTINATIONS:
            routes = fetch_routes(departure, dest)
            print(f"=== {departure} → {dest} ===")
            for label, key in [("早い", "fast"), ("安い", "cheap"), ("乗換少ない", "few")]:
                r = routes.get(key)
                if r:
                    print(f"{label}ルート: 運賃{r['fare']}円, 定期代{r['pass_price']}円, "
                          f"時間{r['minutes']}分, 乗換{r['transfer']}回")
            print()
            time.sleep(1)  # アクセス間隔をあける
