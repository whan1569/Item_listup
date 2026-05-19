from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional


DATA_DIR = Path("data")
INPUT_CSV = DATA_DIR / "clean_search_volume.csv"
CLASSIFIED_OUTPUT_CSV = DATA_DIR / "classified_search_terms.csv"
CATEGORY_OUTPUT_CSV = DATA_DIR / "category_signals.csv"
PRODUCT_ENTITY_OUTPUT_CSV = DATA_DIR / "product_entities.csv"

MAX_TERM_TOKENS = 20


BRANDS = {
    "anua", "skin1004", "mediheal", "torriden", "d'alba", "dalba", "vt", "medicube",
    "aestura", "unove", "beplain", "dr jart", "dr. jart", "joseon", "beauty of joseon",
    "hera", "yunjac", "vitalbeautie", "laneige", "cosrx", "round lab", "numbuzin",
    "abib", "isntree", "mixsoon", "axis-y", "axisy", "romand", "etude", "innisfree",
    "nike", "adidas", "puma", "new balance", "uniqlo", "zara", "h&m", "hm",
    "gillette", "skechers", "palmolive", "finish", "quiltton", "quillton", "kelloggs",
}


INGREDIENTS = {
    "pdrn", "centella", "cica", "centella asiatica", "niacinamide", "panthenol", "hyaluronic acid",
    "hyaluronic", "retinol", "tretinoin", "collagen", "peptide", "ceramide", "allantoin",
    "madecassoside", "tea tree", "houttuynia", "houttuynia cordata", "snail", "mucin",
    "vitamin c", "salicylic acid", "aha", "bha", "lactic acid", "glycolic acid",
}


ATTRIBUTES = {
    "anti aging", "well-aging", "brightening", "hydrating", "moisturising", "moisturizing",
    "soothing", "sensitive", "oily", "dry", "combination", "combination&normal", "visible pores",
    "acne", "blackheads", "dullness", "balancing", "damage repair", "hair loss", "hair growth",
    "anti-frizz", "anti-dandruff", "thickening", "volumising", "heat protection", "colour protection",
    "no white cast", "clean beauty", "vegan", "cruelty-free", "fragrance-free",
}


CATEGORIES = {
    "skincare", "skin care", "sun care", "suncare", "hair care", "body care", "bath & body",
    "bath & shower", "hand care", "hands care", "foot care", "oral care", "makeup", "fragrance",
    "wellness", "supplements", "food & drink", "men's grooming", "men`s care", "k-beauty",
    "korean skin care", "korean makeup", "japanese beauty", "chinese cosmetics", "taiwanese beauty",
    "western beauty", "southeast asia beauty", "us beauty",
    "tops", "pants", "jeans", "skirts", "dresses", "shorts", "socks", "socks & tights",
    "coats & jackets", "jackets", "outerwear", "activewear", "sportswear", "sleepwear",
    "swimwear", "lingerie", "underwear", "undergarments", "shoes", "sneakers", "boots",
    "slip-on shoes", "bags", "sling bags", "shopper bags & tote bags", "wallets & purses",
    "wallets & coin purses", "accessories", "watches & timepieces", "maternity clothes",
}


PRODUCT_TYPES = {
    "serum", "cream", "eye cream", "toner", "cleanser", "cleansing foam", "foam", "ampoule",
    "essence", "moisturizer", "moisturiser", "sunscreen", "sun serum", "sun stick", "mask",
    "sheet mask", "mask sheet", "eye patch", "patch", "pads", "balm", "lotion", "oil",
    "mist", "spray serum", "shampoo", "conditioner", "treatment", "scalp treatment",
    "body moisturizers", "body moisturizer", "lip balm", "lip tint", "lip gloss", "lip stick",
    "foundation", "concealer", "cushion", "makeup cushion", "eyeshadow", "eyeliner", "eyebrow",
    "blush", "contour", "powder", "pact", "razor", "blade", "deodorant", "nose pack",
    "t shirts", "t-shirts", "shirts", "knit tops", "sports tops", "wide leg jeans", "wide-leg pants",
    "cargo pants", "capri pants", "harem pants", "jumper pants", "wrap dresses", "sundresses",
    "cardigans", "blazers", "belts", "backpacks", "messenger bags", "rash guards",
    "bag", "bags", "case", "holder", "organizer", "organiser", "rack", "shelf", "container",
    "bottle", "tumbler", "brush", "sponge", "towel", "mat", "lamp", "nightlight",
    "dish drying rack", "peeler", "protector", "filter",
    "protein", "protein powder", "supplement", "supplements", "capsule", "tablet", "snack", "chips",
    "cookie", "drink", "coffee", "tea",
}


GENERIC_TERMS = {
    "new", "best", "top", "sale", "beauty", "brands", "face", "body", "hair", "lip", "eye",
    "fresh", "green", "sweet", "floral", "fruity", "synthetic", "mineral", "format", "scent",
    "events", "bestsellers", "best sellers", "new arrivals", "flash sales", "in-stock items",
    "all makeup", "all skincare", "all masks", "all hair", "all bath & body", "all sun care",
    "after sun care", "all beauty", "all clothing", "all tops", "all pants", "all footwear",
    "all bags", "all shorts", "all swimwear",
}


YEAR_PATTERN = re.compile(r"\b20\d{2}\b")
HAS_NUMBER_PATTERN = re.compile(r"\d")
PRICE_ONLY_PATTERN = re.compile(r"^(?:us\$|₩|\$|€|£|¥|₱|₹|฿|₫).*")
REDDIT_NATURAL_WORD_PATTERN = re.compile(
    r"\b(i|you|they|we|this|that|what|when|why|how|does|do|did|can|should|would|could|"
    r"tried|using|used|bought|recommend|recommended|review|reviews|anyone|honestly|"
    r"because|really|actually|good|bad|better|best)\b"
)


def normalize(value: Optional[str]) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def token_count(term: str) -> int:
    return len([x for x in re.split(r"\s+", normalize(term)) if x])


def contains_any_phrase(term: str, phrase_set: set[str]) -> list[str]:
    t = normalize(term)
    hits = []

    for phrase in phrase_set:
        p = normalize(phrase)
        if not p:
            continue

        if p == t or re.search(rf"(?<![a-z0-9]){re.escape(p)}(?![a-z0-9])", t):
            hits.append(phrase)

    hits.sort(key=len, reverse=True)
    return hits


def detect_brand(term: str) -> Optional[str]:
    hits = contains_any_phrase(term, BRANDS)
    return hits[0] if hits else None


def detect_product_type(term: str) -> Optional[str]:
    hits = contains_any_phrase(term, PRODUCT_TYPES)
    return hits[0] if hits else None


def detect_ingredient(term: str) -> Optional[str]:
    hits = contains_any_phrase(term, INGREDIENTS)
    return hits[0] if hits else None


def detect_attribute(term: str) -> Optional[str]:
    hits = contains_any_phrase(term, ATTRIBUTES)
    return hits[0] if hits else None


def detect_category(term: str) -> Optional[str]:
    t = normalize(term)

    if t in CATEGORIES:
        return t

    hits = contains_any_phrase(t, CATEGORIES)
    if hits:
        return hits[0]

    return None


def is_price_or_currency_noise(term: str) -> bool:
    t = normalize(term)

    if PRICE_ONLY_PATTERN.match(t) and token_count(t) <= 3:
        return True

    return False


def is_long_sentence_noise(term: str) -> bool:
    t = normalize(term)
    n = token_count(t)

    if not t:
        return True

    # 너무 긴 검색어/문장 제거
    if n > MAX_TERM_TOKENS:
        return True

    # 문장부호가 많으면 게시글/댓글형 문장으로 간주
    if t.count(".") >= 3 or t.count("?") >= 2 or t.count("!") >= 2:
        return True

    # reddit 후기/질문글 스타일 자연문 제거
    if n >= 12 and REDDIT_NATURAL_WORD_PATTERN.search(t):
        return True

    return False


def is_product_entity(term: str) -> bool:
    t = normalize(term)

    if not t or t in GENERIC_TERMS:
        return False
    if is_price_or_currency_noise(t):
        return False
    if is_long_sentence_noise(t):
        return False

    brand = detect_brand(t)
    product_type = detect_product_type(t)
    ingredient = detect_ingredient(t)
    attr = detect_attribute(t)
    n = token_count(t)
    has_year = bool(YEAR_PATTERN.search(t))
    has_number = bool(HAS_NUMBER_PATTERN.search(t))

    if brand and product_type:
        return True
    if brand and ingredient:
        return True
    if ingredient and product_type:
        return True
    if product_type and has_year:
        return True
    if product_type and has_number and n >= 3:
        return True
    if product_type and attr and n >= 3:
        return True
    if product_type and n >= 4:
        return True

    return False


def classify_term(term: str) -> dict:
    t = normalize(term)

    if is_price_or_currency_noise(t) or is_long_sentence_noise(t):
        return {
            "primary_type": "noise",
            "category_bucket": "noise",
            "brand": "",
            "product_type": "",
            "ingredient": "",
            "attribute": "",
            "is_product_entity": "0",
        }

    brand = detect_brand(t)
    product_type = detect_product_type(t)
    ingredient = detect_ingredient(t)
    attribute = detect_attribute(t)
    category = detect_category(t)
    product_entity = is_product_entity(t)

    if product_entity:
        primary_type = "product_entity"
    elif brand:
        primary_type = "brand"
    elif ingredient:
        primary_type = "ingredient"
    elif product_type:
        primary_type = "product_type"
    elif attribute:
        primary_type = "attribute"
    elif category:
        primary_type = "category"
    else:
        primary_type = "unclassified"

    if category:
        category_bucket = category
    elif ingredient:
        category_bucket = "ingredient"
    elif product_type:
        category_bucket = "product_type"
    elif brand:
        category_bucket = "brand"
    elif attribute:
        category_bucket = "attribute"
    else:
        category_bucket = "unclassified"

    return {
        "primary_type": primary_type,
        "category_bucket": category_bucket,
        "brand": brand or "",
        "product_type": product_type or "",
        "ingredient": ingredient or "",
        "attribute": attribute or "",
        "is_product_entity": "1" if product_entity else "0",
    }


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict], path: Path, fieldnames: list[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: Optional[str]) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def main() -> None:
    rows = read_csv(INPUT_CSV)

    classified_rows: list[dict] = []
    category_rows: list[dict] = []
    product_entity_rows: list[dict] = []

    for row in rows:
        search_term = normalize(row.get("search_term", ""))
        if not search_term:
            continue

        cls = classify_term(search_term)

        out = dict(row)
        out["search_term"] = search_term
        out.update(cls)
        classified_rows.append(out)

        if cls["primary_type"] in {"category", "ingredient", "attribute", "product_type", "brand"}:
            category_rows.append(out)

        if cls["is_product_entity"] == "1":
            product_entity_rows.append(out)

    classified_rows.sort(
        key=lambda r: (
            r.get("primary_type") == "product_entity",
            to_int(r.get("source_count")),
            to_int(r.get("search_volume")),
            token_count(r.get("search_term", "")),
        ),
        reverse=True,
    )

    category_rows.sort(
        key=lambda r: (
            r.get("primary_type") == "brand",
            to_int(r.get("source_count")),
            to_int(r.get("search_volume")),
            r.get("search_term", ""),
        ),
        reverse=True,
    )

    product_entity_rows.sort(
        key=lambda r: (
            to_int(r.get("source_count")),
            to_int(r.get("search_volume")),
            token_count(r.get("search_term", "")),
        ),
        reverse=True,
    )

    base_fields = list(rows[0].keys()) if rows else [
        "search_term", "search_volume", "source_count", "sources", "example_raw_phrase"
    ]
    added_fields = [
        "primary_type", "category_bucket", "brand", "product_type",
        "ingredient", "attribute", "is_product_entity"
    ]
    fieldnames = base_fields + [f for f in added_fields if f not in base_fields]

    write_csv(classified_rows, CLASSIFIED_OUTPUT_CSV, fieldnames)
    write_csv(category_rows, CATEGORY_OUTPUT_CSV, fieldnames)
    write_csv(product_entity_rows, PRODUCT_ENTITY_OUTPUT_CSV, fieldnames)

    print(f"input rows: {len(rows)}")
    print(f"classified rows: {len(classified_rows)} -> {CLASSIFIED_OUTPUT_CSV}")
    print(f"category signals: {len(category_rows)} -> {CATEGORY_OUTPUT_CSV}")
    print(f"product entities: {len(product_entity_rows)} -> {PRODUCT_ENTITY_OUTPUT_CSV}")

    print()
    print("TOP PRODUCT ENTITIES")
    for row in product_entity_rows[:40]:
        print(
            f"{row['search_term']} | volume={row.get('search_volume', '')} | "
            f"sources={row.get('source_count', '')} | brand={row.get('brand', '')} | "
            f"type={row.get('product_type', '')} | ingredient={row.get('ingredient', '')}"
        )

    print()
    print("TOP CATEGORY SIGNALS")
    for row in category_rows[:40]:
        print(
            f"{row['search_term']} | {row['primary_type']} | volume={row.get('search_volume', '')} | "
            f"sources={row.get('source_count', '')} | bucket={row.get('category_bucket', '')}"
        )


if __name__ == "__main__":
    main()
