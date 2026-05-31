"""
스마트스토어 키워드 순위 추적기 - 크롤러
config.json에 등록된 상품/키워드를 조회하여 data/rankings.json에 누적 저장합니다.
"""

import json
import os
import time
import random
from datetime import datetime
from pathlib import Path

import requests

# ============================================================
# 파일 경로 (건드리지 마세요)
# ============================================================
BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
DATA_FILE   = BASE_DIR / "data" / "rankings.json"

MAX_RANK = 100

# 네이버 검색 API 키 (GitHub Secrets에서 주입)
CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

# ============================================================


def get_rank(keyword: str, product_id: str, max_rank: int = 100) -> int | None:
    """네이버 쇼핑 검색 API로 특정 상품의 순위를 반환. 없으면 None."""
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }

    display = 100
    start = 1
    found_count = 0

    while found_count < max_rank:
        params = {
            "query": keyword,
            "display": display,
            "start": start,
            "sort": "sim",
        }

        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/shop.json",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
        except Exception as e:
            print(f"    ⚠️  요청 실패: {e}")
            return None

        items = resp.json().get("items", [])
        if not items:
            break

        for item in items:
            found_count += 1
            link = item.get("link", "")
            product_id_field = str(item.get("productId", ""))

            if product_id in link or product_id in product_id_field:
                return found_count

            if found_count >= max_rank:
                return None

        start += display
        if start > 1000:
            break

        time.sleep(random.uniform(0.3, 0.7))

    return None


def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": "", "products": {}}


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 저장 완료: {DATA_FILE}")


def main():
    config = load_config()
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    data["last_updated"] = today

    products = config.get("products", [])
    print(f"\n🔍 순위 조회 시작 [{today}]")
    print(f"   상품: {len(products)}개\n")

    for product in products:
        pid      = product["id"]
        name     = product["name"]
        keywords = product["keywords"]

        print(f"📦 {name} (ID: {pid})")

        if pid not in data["products"]:
            data["products"][pid] = {}

        for keyword in keywords:
            print(f"  📌 '{keyword}' 조회 중...")
            rank = get_rank(keyword, pid, MAX_RANK)

            if rank:
                print(f"     ✅ {rank}위 발견!")
            else:
                print(f"     ❌ {MAX_RANK}위 밖")

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
    print("\n✨ 모든 키워드 조회 완료!")


if __name__ == "__main__":
    main()
