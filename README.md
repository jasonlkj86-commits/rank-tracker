# 📦 스마트스토어 키워드 순위 트래커

코딩 몰라도 설정 가능! 순서대로 따라하면 됩니다.

---

## 📋 전체 흐름

```
① GitHub에 이 폴더 업로드
② crawler.py에 내 스토어 정보 입력
③ Netlify에 배포
→ 매일 자동으로 순위 수집 + 웹에서 확인!
```

---

## Step 1. GitHub 업로드

1. [github.com](https://github.com) 회원가입/로그인
2. **New repository** 클릭
3. Repository name: `rank-tracker` (이름 자유)
4. **Public** 선택 (Netlify 무료 플랜 사용시 필요)
5. Create repository 클릭
6. 이 폴더 전체를 GitHub Desktop이나 드래그&드롭으로 업로드

---

## Step 2. crawler.py 수정

`crawler.py` 파일을 열어서 **맨 위 이 부분만** 수정:

```python
MY_STORE_ID = "여기에내스토어주소"   # ← 내 스마트스토어 URL 끝 부분

KEYWORDS = [
    "키워드1",
    "키워드2",
    "키워드3",
]
```

예시:
- 스토어 주소가 `smartstore.naver.com/bbiddulz` → `"bbiddulz"`
- 키워드: `"아이그림 키링"`, `"아크릴키링 주문제작"` 등

---

## Step 3. Netlify 배포

1. [netlify.com](https://netlify.com) 회원가입/로그인
2. **Add new site** → **Import an existing project**
3. GitHub 연결 → 아까 만든 repo 선택
4. Deploy site 클릭
5. 완료! 주소가 생성됩니다 (예: `rank-tracker.netlify.app`)

---

## Step 4. 자동 실행 설정 (GitHub Actions)

`.github/workflows/daily-crawl.yml` 파일이 이미 설정되어 있습니다.

기본 설정: **매일 오전 9시(한국시간) 자동 실행**

수동으로 실행하고 싶을 때:
1. GitHub → 내 repo → **Actions** 탭
2. "매일 순위 자동 수집" → **Run workflow** 클릭

---

## 📊 웹앱 사용법

- **카드 클릭**: 해당 키워드만 집중 분석
- **카드 다시 클릭**: 전체 보기로 돌아가기
- 상단 카드: 현재 순위 + 어제 대비 변동
- 아래 차트: 날짜별 순위 변동 추이

---

## ❓ 자주 묻는 문제

**Q: 순위가 안 나와요**
→ 내 상품이 해당 키워드로 100위 밖에 있을 수 있습니다.
  `MAX_RANK = 200`으로 늘려볼 수 있어요 (시간이 더 걸림).

**Q: Actions가 실패해요**
→ GitHub repo 설정 → Settings → Actions → General
  → "Read and write permissions" 선택 후 저장

**Q: 네이버가 차단해요**
→ 크롤러 내 대기 시간을 늘려보세요 (random.uniform 값을 키우기)
