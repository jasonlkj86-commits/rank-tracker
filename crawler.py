"""
스마트스토어 키워드 순위 추적기 - 크롤러
매일 실행하면 data/rankings.json에 순위가 누적 저장됩니다.
"""

import json
import os
import time
import random
from datetime import datetime
from pathlib import Path

import requests

# ============================================================
# 여기를 내 정보로 바꾸세요
# ============================================================

MY_STORE_ID = "minimalsign"

# 순위를 추적할 특정 상품 ID
# https://smartstore.naver.com/minimalsign/products/4061216291
MY_PRODUCT_ID = "4061216291"

# 추적할 키워드 목록
KEYWORDS = [
    "미니간판",
    "카페간판",
    "스텐간판",
]

# 몇 위까지 검색할지 (네이버 검색 API 최대 100개)
MAX_RANK = 100

# 데이터 저장 경로
DATA_FILE = Path(__file__).parent / "data" / "rankings.json"

# ============================================================
# 네이버 검색 API 키 (환경변수 우선, 없으면 아래 직접 입력)
# ============================================================

CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID",     "")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

# ============================================================


def get_rank(keyword: str, product_id: str, max_rank: int = 100) -> int | None:
    """네이버 쇼핑 검색 API로 특정 상품의 순위를 반환. 없으면 None."""
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }

    display = 100  # 한 번에 최대 100개
    start = 1
    found_count = 0

    while found_count < max_rank:
        params = {
            "query": keyword,
            "display": display,
            "start": start,
            "sort": "sim",  # 유사도순 (= 기본 정렬)
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
            link = item.get("link", "") + item.get("productId", "")
            mall_name = item.get("mallName", "")
            product_id_field = str(item.get("productId", ""))

            if product_id in link or product_id in product_id_field:
                return found_count

            if found_count >= max_rank:
                return None

        # 다음 페이지 (API start 최대 1000)
        start += display
        if start > 1000:
            break

        time.sleep(random.uniform(0.3, 0.7))

    return None


def load_data() -> dict:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"store_id": MY_STORE_ID, "keywords": {}}


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 저장 완료: {DATA_FILE}")


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🔍 순위 조회 시작 [{today}]")
    print(f"   스토어: {MY_STORE_ID}")
    print(f"   상품ID: {MY_PRODUCT_ID}")
    print(f"   키워드: {len(KEYWORDS)}개\n")

    data = load_data()
    data["store_id"] = MY_STORE_ID
    data["last_updated"] = today

    for keyword in KEYWORDS:
        print(f"📌 '{keyword}' 조회 중...")
        rank = get_rank(keyword, MY_PRODUCT_ID, MAX_RANK)

        if rank:
            print(f"   ✅ {rank}위 발견!")
        else:
            print(f"   ❌ {MAX_RANK}위 내 없음")

        if keyword not in data["keywords"]:
            data["keywords"][keyword] = []

        history = data["keywords"][keyword]
        existing = next((h for h in history if h["date"] == today), None)
        if existing:
            existing["rank"] = rank
        else:
            history.append({"date": today, "rank": rank})

        data["keywords"][keyword].sort(key=lambda x: x["date"])

        time.sleep(random.uniform(1.0, 2.0))

    save_data(data)
    print("\n✨ 모든 키워드 조회 완료!")


if __name__ == "__main__":
    main()
