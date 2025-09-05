# -*- coding: utf-8 -*-
# Yahoo!路線検索 自動化スクリプト（田町・三田）最安＆最短の定期だけ出力

import pandas as pd
import re
import urllib.parse
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# 検索クラス
# =========================
class YahooRouteSearcher:
    def __init__(self, headless=True):
        self.setup_driver(headless)

    def setup_driver(self, headless):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,1600")
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(2)

    # ---- ユーティリティ ----
    def _parse_amounts(self, html):
        return [int(a.replace(",", "")) for a in re.findall(r"(\d{1,3}(?:,\d{3})*)\s*円", html)]

    def _choose_fare_from_html(self, html):
        vals = [f for f in self._parse_amounts(html) if 100 <= f < 2000]
        return min(vals) if vals else 0

    def _top_signature(self):
        routes = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='route']")
        return routes[0].text[:200] if routes else self.driver.page_source[:500]

    # ---- 並び替えタブ（アイコンclassで押す） ----
    def _switch_sort(self, mode):
        class_map = {
            "arrival": "icnPriTime",    # 到着時刻順（＝最短寄り）
            "cheap":   "icnPriFare",    # 料金の安い順（＝最安）
        }
        cls = class_map.get(mode)
        if not cls:
            return False
        old_url = self.driver.current_url
        old_sig = self._top_signature()
        try:
            span = self.driver.find_element(By.CSS_SELECTOR, f"span.{cls}")
            a = span.find_element(By.XPATH, "./ancestor::a")
            href = a.get_attribute("href")
            if href:
                self.driver.get(href)
            else:
                self.driver.execute_script("arguments[0].click();", a)
            WebDriverWait(self.driver, 10).until(
                lambda d: d.current_url != old_url or self._top_signature() != old_sig
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='route']"))
            )
            return True
        except Exception:
            return False

    # ---- 定期（6か月） ----
    def _extract_teiki_6m(self, route_elem):
        """定期券を開いて6か月の金額だけ返す。範囲外は0。"""
        def yen_to_int(txt):
            m = re.search(r"(\d{1,3}(?:,\d{3})*|\d+)\s*円", txt)
            return int(m.group(1).replace(",", "")) if m else None

        try:
            # ボタン押下（2段構え）
            try:
                btn = route_elem.find_element(
                    By.XPATH, ".//a[contains(., '定期券')] | .//button[contains(., '定期券')]"
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                self.driver.execute_script("""
                    const root = arguments[0];
                    const nodes = root.querySelectorAll('a,button');
                    for (const n of nodes) {
                        const t = (n.innerText||'').trim();
                        if (t.includes('定期券')) { n.click(); break; }
                    }
                """, route_elem)

            # LI群が表示されるまで待つ
            WebDriverWait(self.driver, 6).until(
                lambda d: len(route_elem.find_elements(
                    By.XPATH, ".//li[.//span or .//em or .//strong]"
                )) > 0
            )
            time.sleep(0.6)

            # 6か月/6ヶ月/6カ月
            li_candidates = route_elem.find_elements(
                By.XPATH,
                ".//li[contains(., '6か月') or contains(., '6ヶ月') or contains(., '6カ月') or contains(., '６か月')]"
            )
            for li in li_candidates:
                val = yen_to_int(li.text)
                if val and 10000 <= val <= 200000:
                    return val

            # 3番目LIフォールバック
            try:
                li3 = route_elem.find_element(By.XPATH, ".//li[position()=3]")
                val = yen_to_int(li3.text)
                if val and 10000 <= val <= 200000:
                    return val
            except Exception:
                pass

            # HTMLから大きめ金額
            inner = route_elem.get_attribute("innerHTML")
            cands = [a for a in self._parse_amounts(inner) if 10000 <= a <= 200000]
            if cands:
                return max(cands)
        except Exception:
            pass
        return 0

    # ---- ルート1抽出 ----
    def _extract_top_route(self):
        routes = self.driver.find_elements(By.CSS_SELECTOR, "div[id^='route']")
        if not routes:
            html = self.driver.page_source
            return {
                "fare": self._choose_fare_from_html(html),
                "duration": "-",
                "transfers": 0,
                "monthly_pass": 0,
            }
        r = routes[0]
        html = r.get_attribute("innerHTML")
        fare = self._choose_fare_from_html(html)
        dur_m = re.search(r"(\d+時間\d+分|\d+分)", html)
        tr_m = re.search(r"乗換\s*(\d+)\s*回", html)
        monthly = self._extract_teiki_6m(r)
        if not (10000 <= monthly <= 200000):
            monthly = 0
        return {
            "fare": fare,
            "duration": dur_m.group(1) if dur_m else "-",
            "transfers": int(tr_m.group(1)) if tr_m else 0,
            "monthly_pass": monthly,
        }

    # ---- 検索（最安＆最短だけ） ----
    def search_min_and_fast(self, home, company):
        """home→company の最安(cheap)と最短(arrival)のルート1を返す"""
        url = f"https://transit.yahoo.co.jp/search/result?from={urllib.parse.quote(home+'駅')}&to={urllib.parse.quote(company+'駅')}"
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='route']"))
        )

        out = {}

        # 料金の安い順（最安）
        if self._switch_sort("cheap"):
            out["cheapest"] = self._extract_top_route()
        else:
            out["cheapest"] = {"fare": 0, "monthly_pass": 0, "duration": "-", "transfers": 0}

        # 到着時刻順（最短とみなす）
        if self._switch_sort("arrival"):
            out["fastest"] = self._extract_top_route()
        else:
            out["fastest"] = {"fare": 0, "monthly_pass": 0, "duration": "-", "transfers": 0}

        return out

    def close(self):
        self.driver.quit()


# =========================
# バッチ処理（並列）
# =========================
def run_batch(excel_file):
    df = pd.read_excel(excel_file)
    results = []
    company_stations = ["田町", "三田"]

    def worker(row, home, company):
        s = YahooRouteSearcher(headless=True)
        try:
            info = s.search_min_and_fast(str(home), company)
        finally:
            s.close()

        cheapest = info.get("cheapest", {})
        fastest  = info.get("fastest", {})

        return {
            "個人コード": row.get("個人コード", ""),
            "個人氏名": row.get("個人氏名", ""),
            "部門": row.get("部門_総称", ""),
            "自宅最寄り駅": home,
            "会社最寄り駅": company,

            # 最安ルート
            "最安_運賃": cheapest.get("fare", 0),
            "最安_定期6か月": cheapest.get("monthly_pass", 0),
            "最安_所要時間": cheapest.get("duration", "-"),

            # 最短ルート
            "最短_所要時間": fastest.get("duration", "-"),
            "最短_運賃": fastest.get("fare", 0),
            "最短_定期6か月": fastest.get("monthly_pass", 0),
        }

    tasks = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for _, row in df.iterrows():
            home = row.get("通勤区間終了１")
            if pd.isna(home) or not home:
                continue
            for company in company_stations:
                tasks.append(ex.submit(worker, row, home, company))
        for fut in as_completed(tasks):
            results.append(fut.result())

    return pd.DataFrame(results)


# =========================
# メイン
# =========================
def main():
    input_file = "SearchResult.xlsx"   # 入力：通勤区間終了１ / 個人コード / 個人氏名 / 部門_総称
    df = run_batch(input_file)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = f"yahoo_route_summary_{ts}.xlsx"
    with pd.ExcelWriter(out) as w:
        df.to_excel(w, sheet_name="最安・最短まとめ", index=False)

    print(f"✅ 出力完了: {out}")
    print("  列：最安_運賃 / 最安_定期6か月 / 最安_所要時間 / 最短_所要時間 / 最短_運賃 / 最短_定期6か月")


if __name__ == "__main__":
    main()
