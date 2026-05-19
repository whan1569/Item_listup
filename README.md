# Item_listup

검색어 / 상품명 수집 및 정제 파이프라인.

웹 소스에서 상품 관련 phrase를 수집한 뒤 아래 과정을 수행한다:

- 검색어 정규화
- 노이즈 제거
- 상품 / 브랜드 / 카테고리 분류
- CSV 산출

---

# Installation

## 1. Python 설치

권장 버전:

- Python 3.10+

버전 확인:

```bash
python --version
```

---

## 2. 저장소 클론

```bash
git clone https://github.com/whan1569/Item_listup.git
cd Item_listup
```

---

## 3. 가상환경 생성 (권장)

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 4. 패키지 설치

```bash
pip install -r requirements.txt
```

### requirements.txt 예시

```txt
pandas
numpy
requests
beautifulsoup4
lxml
tqdm
```

---

# Project Structure

```txt
Item_listup/
│
├── main.py
├── Crawler.py
├── Aggregator.py
├── Cleaner.py
├── Classify.py
│
├── data/
│   ├── raw_search_phrases.csv
│   ├── search_volume.csv
│   ├── clean_search_volume.csv
│   ├── removed_search_volume.csv
│   ├── classified_search_terms.csv
│   ├── category_signals.csv
│   └── product_entities.csv
│
├── requirements.txt
└── README.md
```

---

# Execution

전체 파이프라인은 `main.py` 하나로 실행한다.

```bash
python main.py
```

실행 순서:

1. 원천 데이터 수집
2. 검색어 집계
3. 노이즈 제거 및 정제
4. 상품 / 브랜드 / 카테고리 분류

생성 파일:

- `raw_search_phrases.csv`
- `search_volume.csv`
- `clean_search_volume.csv`
- `removed_search_volume.csv`
- `classified_search_terms.csv`
- `category_signals.csv`
- `product_entities.csv`

---

# Output Data Dictionary

## raw_search_phrases.csv

원천 크롤링 phrase 데이터.

| Column       | Description        |
| ------------ | ------------------ |
| collected_at | 수집 시간           |
| source       | 데이터 소스         |
| page_url     | 수집 페이지 URL     |
| item_type    | 수집 타입           |
| raw_phrase   | 원문 phrase         |
| item_id      | 내부 ID            |
| item_url     | 원문 item URL      |
| extractor    | 사용 extractor     |

---

## search_volume.csv

동일 phrase 집계 데이터.

| Column             | Description          |
| ------------------ | -------------------- |
| search_term        | 정규화 검색어         |
| search_volume      | 검색어 출현 횟수      |
| source_count       | 검색어 발견 소스 수   |
| sources            | 발견 소스 목록        |
| example_raw_phrase | 대표 원문 phrase      |

---

## clean_search_volume.csv

노이즈 제거 후 검색어 데이터.

| Column             | Description        |
| ------------------ | ------------------ |
| search_term        | 정제 검색어         |
| search_volume      | 검색량              |
| source_count       | 발견 소스 수        |
| sources            | 발견 소스           |
| example_raw_phrase | 대표 원문 phrase    |

---

## removed_search_volume.csv

제거된 검색어 데이터.

| Column         | Description |
| -------------- | ----------- |
| search_term    | 제거 검색어  |
| search_volume  | 검색량       |
| removed_reason | 제거 사유    |

---

## classified_search_terms.csv

검색어 분류 결과.

| Column            | Description      |
| ----------------- | ---------------- |
| search_term       | 검색어           |
| primary_type      | 메인 분류        |
| category_bucket   | 카테고리 버킷    |
| brand             | 브랜드           |
| product_type      | 상품 유형        |
| ingredient        | 성분             |
| attribute         | 속성             |
| is_product_entity | 상품 엔티티 여부 |

---

## category_signals.csv

카테고리 / 브랜드 / 성분 중심 데이터.

---

## product_entities.csv

실제 상품 엔티티 후보 데이터.

---

# Classification Types

| Type            | Description |
| ---------------- | ----------- |
| product_entity   | 실제 상품명  |
| brand            | 브랜드      |
| category         | 카테고리     |
| product_type     | 상품 유형    |
| ingredient       | 성분         |
| attribute        | 속성         |
| noise            | 노이즈       |
| unclassified     | 미분류       |

---

# Removed Reasons

| Reason                    | Description           |
| ------------------------- | --------------------- |
| number_only               | 숫자만 존재            |
| reddit_username_or_system | Reddit 시스템 문구    |
| ui_navigation_policy      | UI / 정책 문구        |
