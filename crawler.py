"""
📦 스마트스토어 키워드 순위 추적기 - 크롤러
==========================================
매일 실행하면 data/rankings.json에 순위가 누적 저장됩니다.

[처음 설정할 때 여기만 수정하세요!]
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ============================================================
# ✏️  여기를 내 정보로 바꾸세요
# ============================================================

# 내 스마트스토어 URL에 포함된 고유 주소
# 예: https://smartstore.naver.com/bbiddulz → "bbiddulz"
MY_STORE_ID = "bbiddulz"

# 추적할 키워드 목록
KEYWORDS = [
    "아이그림 키링",
    "어린이그림 폰케이스",
    "아크릴키링 주문제작",
    # 키워드 추가할 땐 이 형식으로 한 줄씩 추가하세요
]

# 몇 위까지 검색할지 (최대 100위 / 숫자 높을수록 시간 오래 걸림)
MAX_RANK = 100

# 데이터 저장 경로 (건드리지 마세요)
DATA_FILE = Path(__file__).parent / "data" / "rankings.json"

# ============================================================


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://search.shopping.naver.com/",
}


def get_rank(keyword: str, store_id: str, max_rank: int = 100) -> int | None:
    """
    네이버 쇼핑에서 키워드 검색 후 내 상품 순위 반환
    찾지 못하면 None 반환
    """
    rank = None
    page = 1
    found_count = 0

    while found_count < max_rank:
        url = (
            f"https://search.shopping.naver.com/search/all"
            f"?query={requests.utils.quote(keyword)}"
            f"&pagingIndex={page}&pagingSize=40&sort=rel"
        )

        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"    ⚠️  요청 실패: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # 상품 링크 추출 (네이버 쇼핑 구조)
        items = soup.select("a[href*='smartstore.naver.com']")

        if not items:
            # JSON 데이터에서도 시도
            import re
            links = re.findall(
                r'smartstore\.naver\.com/([^/"\'\\s]+)', resp.text
            )
            items_found = links
        else:
            items_found = [a.get("href", "") for a in items]

        if not items_found:
            break

        for link in items_found:
            found_count += 1
            link_str = str(link).lower()
            if store_id.lower() in link_str:
                rank = found_count
                return rank
            if found_count >= max_rank:
                return None

        page += 1
        # 과도한 요청 방지 - 1~2초 랜덤 대기
        time.sleep(random.uniform(1.0, 2.0))

    return rank


def load_data() -> dict:
    """기존 저장 데이터 불러오기"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"store_id": MY_STORE_ID, "keywords": {}}


def save_data(data: dict):
    """데이터 저장"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 저장 완료: {DATA_FILE}")


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🔍 순위 조회 시작 [{today}]")
    print(f"   스토어: {MY_STORE_ID}")
    print(f"   키워드: {len(KEYWORDS)}개\n")

    data = load_data()
    data["store_id"] = MY_STORE_ID
    data["last_updated"] = today

    for keyword in KEYWORDS:
        print(f"📌 '{keyword}' 조회 중...")
        rank = get_rank(keyword, MY_STORE_ID, MAX_RANK)

        if rank:
            print(f"   ✅ {rank}위 발견!")
        else:
            print(f"   ❌ {MAX_RANK}위 내 없음")

        # 키워드별 히스토리 누적
        if keyword not in data["keywords"]:
            data["keywords"][keyword] = []

        # 같은 날짜면 덮어쓰기, 새 날짜면 추가
        history = data["keywords"][keyword]
        existing = next((h for h in history if h["date"] == today), None)
        if existing:
            existing["rank"] = rank
        else:
            history.append({"date": today, "rank": rank})

        # 날짜 순 정렬
        data["keywords"][keyword].sort(key=lambda x: x["date"])

        # 키워드 사이 2~3초 대기
        time.sleep(random.uniform(2.0, 3.0))

    save_data(data)
    print("\n✨ 모든 키워드 조회 완료!")


if __name__ == "__main__":
    main()
