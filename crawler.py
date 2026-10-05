"""
스마트스토어 키워드 순위 추적기 - 크롤러
config.json에 등록된 상품/키워드를 조회하여 data/rankings.json에 누적 저장합니다.
Playwright로 네이버 쇼핑 페이지를 직접 스크래핑합니다.
"""

import json
import os
import time
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
DATA_FILE   = BASE_DIR / "data" / "rankings.json"

MAX_RANK = 100


def get_rank(keyword: str, product_id: str, max_rank: int = 100):
    """
    네이버 쇼핑 검색 결과에서 특정 상품의 순위와 이미지 URL을 반환.
    Returns: (rank: int | None, image: str | None)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ko-KR",
        )
        page = context.new_page()
        rank = 0
        image_url = None

        try:
            for page_num in range(1, 4):  # 최대 3페이지 (약 120개)
                url = (
                    f"https://search.shopping.naver.com/search/all"
                    f"?query={quote(keyword)}&sort=sim"
                    f"&pagingIndex={page_num}&pagingSize=40"
                )
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(random.randint(2000, 3500))

                items = page.query_selector_all('[class*="basicList_item"]')
                if not items:
                    print(f"    ⚠️  상품 목록을 찾을 수 없음 (페이지 {page_num})")
                    break

                for item in items:
                    rank += 1
                    links = item.query_selector_all("a[href]")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if product_id in href:
                            img = item.query_selector("img")
                            if img:
                                image_url = img.get_attribute("src")
                            return rank, image_url

                    if rank >= max_rank:
                        return None, None

                time.sleep(random.uniform(1.5, 2.5))

        except Exception as e:
            print(f"    ⚠️  스크래핑 오류: {e}")
        finally:
            browser.close()

    return None, None


def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"🖼  config.json 이미지 업데이트 완료")


def load_data() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": "", "products": {}}


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 rankings.json 저장 완료")


def main():
    config = load_config()
    data = load_data()
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    today = now_kst.strftime("%Y-%m-%d")
    data["last_updated"] = now_kst.strftime("%Y-%m-%d %H:%M")

    products = config.get("products", [])
    config_updated = False

    print(f"\n🔍 순위 조회 시작 [{today}]")
    print(f"   상품: {len(products)}개\n")

    for product in products:
        pid      = product["id"]
        name     = product["name"]
        keywords = product["keywords"]
        has_image = bool(product.get("image"))

        print(f"📦 {name} (ID: {pid})")

        if pid not in data["products"]:
            data["products"][pid] = {}

        for keyword in keywords:
            print(f"  📌 '{keyword}' 조회 중...")
            rank, image = get_rank(keyword, pid, MAX_RANK)

            if rank:
                print(f"     ✅ {rank}위 발견!")
            else:
                print(f"     ❌ {MAX_RANK}위 밖")

            if not has_image and image:
                product["image"] = image
                has_image = True
                config_updated = True
                print(f"     🖼  이미지 URL 수집 완료")

            if keyword not in data["products"][pid]:
                data["products"][pid][keyword] = []

            history = data["products"][pid][keyword]
            existing = next((h for h in history if h["date"] == today), None)
            if existing:
                existing["rank"] = rank
            else:
                history.append({"date": today, "rank": rank})

            data["products"][pid][keyword].sort(key=lambda x: x["date"])
            time.sleep(random.uniform(1.0, 2.0))

    save_data(data)
    if config_updated:
        save_config(config)
    print("\n✨ 모든 키워드 조회 완료!")


if __name__ == "__main__":
    main()
