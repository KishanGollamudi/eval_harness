"""Local ChromaDB knowledge-base ingestion and retrieval."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PROJECT_ROOT / "data" / "catalog.json"
POLICIES_PATH = PROJECT_ROOT / "data" / "policies.md"
CHROMA_PATH = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "devgear_store_kb"
CONTENT_FORMAT_VERSION = 2
COLLECTION_METADATA = {
    "description": "DevGear Studio catalog and store policies",
    "content_format_version": CONTENT_FORMAT_VERSION,
}

_POLICY_KEYWORDS = {
    "Shipping & Delivery": (
        "shipping",
        "delivery",
        "free shipping",
        "standard shipping",
        "express",
        "dispatch",
        "international",
        "ship",
        "canada",
    ),
    "Returns & Refunds": (
        "return",
        "returns",
        "returning",
        "refund",
        "restocking",
        "opened audio",
        "clearance",
    ),
    "Warranty & Support": (
        "warranty",
        "warranties",
        "accidental damage",
        "manufacturing defects",
        "support",
        "rma",
    ),
    "Promo Codes & Discounts": (
        "fde15",
        "promo",
        "promo code",
        "discount",
        "coupon",
        "expired code",
    ),
}
_GENERIC_PRODUCT_TOKENS = {
    "audio",
    "black",
    "c",
    "custom",
    "dock",
    "ergonomic",
    "headphones",
    "headset",
    "hub",
    "keyboard",
    "keyboards",
    "light",
    "lighting",
    "mechanical",
    "mini",
    "monitor",
    "monitors",
    "mouse",
    "mice",
    "nvme",
    "portable",
    "pro",
    "ssd",
    "station",
    "storage",
    "usb",
    "webcam",
    "wireless",
}
_CATEGORY_KEYWORDS = {
    "Keyboards": ("keyboard", "keyboards"),
    "Hubs & Docks": ("hub", "dock", "docks"),
    "Storage": ("ssd", "nvme", "storage", "drive"),
    "Mice & Ergonomics": ("mouse", "mice", "trackball"),
    "Monitors & Lighting": ("monitor", "monitors", "display", "screen", "light"),
    "Audio & Webcams": ("audio", "headphone", "headset", "webcam", "camera"),
}

_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
# Chroma's default uses its ONNX all-MiniLM-L6-v2 embedding, without PyTorch.
_embedding_function = DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=_embedding_function,
    metadata=COLLECTION_METADATA,
)


@lru_cache(maxsize=1)
def _catalog_records() -> tuple[dict[str, Any], ...]:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        products = json.load(catalog_file)
    if not isinstance(products, list):
        raise ValueError("The product catalog must contain a JSON list.")
    return tuple(products)


@lru_cache(maxsize=1)
def _policy_sections() -> tuple[tuple[str, str], ...]:
    policy_text = POLICIES_PATH.read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^#{2,3}\s+(.+?)\s*$", policy_text))
    sections: list[tuple[str, str]] = []
    if headings:
        for index, heading in enumerate(headings):
            section_end = (
                headings[index + 1].start()
                if index + 1 < len(headings)
                else len(policy_text)
            )
            title = heading.group(1).strip()
            body = policy_text[heading.end() : section_end].strip()
            if body:
                sections.append((title, body))
    else:
        content = policy_text.strip()
        if content:
            sections.append(("Store Policies", content))
    return tuple(sections)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def _phrase_position(query_tokens: list[str], phrase_tokens: list[str]) -> int | None:
    if not phrase_tokens or len(phrase_tokens) > len(query_tokens):
        return None
    for start in range(len(query_tokens) - len(phrase_tokens) + 1):
        if query_tokens[start : start + len(phrase_tokens)] == phrase_tokens:
            return start
    return None


def _product_match(query_tokens: list[str], product_name: str) -> tuple[int, int] | None:
    name_tokens = _tokens(product_name)
    best: tuple[int, int] | None = None
    for length in range(len(name_tokens), 1, -1):
        for start in range(len(name_tokens) - length + 1):
            phrase = name_tokens[start : start + length]
            if all(token in _GENERIC_PRODUCT_TOKENS for token in phrase):
                continue
            position = _phrase_position(query_tokens, phrase)
            if position is None:
                continue
            candidate = (position, -length)
            if best is None or (candidate[1], candidate[0]) < (best[1], best[0]):
                best = candidate
    return best


def find_catalog_product_mentions(query: str) -> list[dict[str, Any]]:
    """Return catalog products whose identifying name phrase appears in the query."""
    query_tokens = _tokens(query)
    records = _catalog_records()
    token_products: dict[str, set[int]] = {}
    for index, product in enumerate(records):
        for token in set(_tokens(str(product["name"]))):
            if token not in _GENERIC_PRODUCT_TOKENS:
                token_products.setdefault(token, set()).add(index)

    matches: list[tuple[tuple[int, int], dict[str, Any]]] = []
    for index, product in enumerate(records):
        match = _product_match(query_tokens, str(product["name"]))
        if match is None:
            unique_mentions = [
                (position, token)
                for position, token in enumerate(query_tokens)
                if token in token_products
                and token_products[token] == {index}
                and token not in _GENERIC_PRODUCT_TOKENS
                and len(token) >= 3
            ]
            if unique_mentions:
                match = (unique_mentions[0][0], -1)
        if match is not None:
            matches.append((match, product))
    longest_match_at_position: dict[int, int] = {}
    for match, _ in matches:
        phrase_length = -match[1]
        longest_match_at_position[match[0]] = max(
            longest_match_at_position.get(match[0], 0), phrase_length
        )
    matches = [
        (match, product)
        for match, product in matches
        if longest_match_at_position[match[0]] < 3
        or -match[1] == longest_match_at_position[match[0]]
    ]
    query_categories = {
        category
        for category, keywords in _CATEGORY_KEYWORDS.items()
        if any(_phrase_position(query_tokens, _tokens(keyword)) is not None for keyword in keywords)
    }
    if len(query_categories) == 1:
        category = next(iter(query_categories))
        matches = [
            (match, product)
            for match, product in matches
            if product["category"] == category
        ]
    matches.sort(key=lambda item: item[0])
    return [product for _, product in matches]


def get_catalog_products() -> list[dict[str, Any]]:
    """Return all catalog records for deterministic, catalog-grounded responses."""
    return list(_catalog_records())


def _policy_matches(query: str) -> dict[str, tuple[int, int]]:
    query_tokens = _tokens(query)
    matches: dict[str, tuple[int, int]] = {}
    for title, keywords in _POLICY_KEYWORDS.items():
        best: tuple[int, int] | None = None
        for keyword in keywords:
            keyword_tokens = _tokens(keyword)
            position = _phrase_position(query_tokens, keyword_tokens)
            if position is not None:
                candidate = (position, -len(keyword_tokens))
                if best is None or candidate < best:
                    best = candidate
        if best is not None:
            matches[title] = best
    return matches


def find_policy_mentions(query: str) -> list[dict[str, str]]:
    """Return policy sections matched by known policy terms in the query."""
    matches = _policy_matches(query)
    return [
        {"title": title, "text": f"[POLICY: {title}]\n{body}"}
        for title, body in _policy_sections()
        if title in matches
    ]


def format_product_context(product: dict[str, Any]) -> str:
    """Format catalog facts in a compact, unambiguous key-value block."""
    stock_count = int(product["stock_count"])
    stock_status = "In Stock" if stock_count > 0 else "OUT OF STOCK"
    specs = "; ".join(
        f"{name}={value}" for name, value in product["specs"].items()
    )
    return (
        f"[PRODUCT: {product['name']} | PRICE: ${float(product['price_usd']):.2f} | "
        f"STOCK: {stock_count} units ({stock_status}) | "
        f"WARRANTY: {int(product['warranty_months'])} months | SPECS: {specs}]"
    )


def _catalog_chunks() -> tuple[list[str], list[str], list[dict[str, str]]]:
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    for product in _catalog_records():
        document = (
            f"{format_product_context(product)}\n"
            f"PRODUCT ID: {product['id']}\n"
            f"CATEGORY: {product['category']}\n"
            f"DESCRIPTION: {product['description']}"
        )
        ids.append(f"product:{product['id']}")
        documents.append(document)
        metadatas.append(
            {
                "source": "catalog.json",
                "product_id": str(product["id"]),
                "title": str(product["name"]),
            }
        )
    return ids, documents, metadatas


def _policy_chunks() -> tuple[list[str], list[str], list[dict[str, str]]]:
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    for index, (title, body) in enumerate(_policy_sections()):
        slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
        ids.append(f"policy:{index}:{slug}")
        documents.append(f"[POLICY: {title}]\n{body}")
        metadatas.append({"source": "policies.md", "title": title})
    return ids, documents, metadatas


def knowledge_base_needs_rebuild() -> bool:
    """Detect an empty index or a collection created with an older chunk format."""
    metadata = _collection.metadata or {}
    return (
        _collection.count() == 0
        or metadata.get("content_format_version") != CONTENT_FORMAT_VERSION
    )


def get_collection() -> Any:
    """Return the active ChromaDB collection."""
    return _collection


def indexed_chunk_count() -> int:
    """Return the number of records currently stored in the knowledge base."""
    return _collection.count()


def ingest_knowledge_base(force_rebuild: bool = False) -> int:
    """Upsert product and policy chunks, optionally replacing the collection."""
    global _collection

    _catalog_records.cache_clear()
    _policy_sections.cache_clear()
    ids, documents, metadatas = _catalog_chunks()
    policy_ids, policy_documents, policy_metadatas = _policy_chunks()
    ids.extend(policy_ids)
    documents.extend(policy_documents)
    metadatas.extend(policy_metadatas)

    if force_rebuild:
        existing = _client.list_collections()
        if any(
            collection == COLLECTION_NAME
            or getattr(collection, "name", None) == COLLECTION_NAME
            for collection in existing
        ):
            _client.delete_collection(name=COLLECTION_NAME)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_embedding_function,
            metadata=COLLECTION_METADATA,
        )

    _collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return _collection.count()


def retrieve_context(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Combine semantic results with exact catalog and policy keyword matches."""
    normalized_query = query.strip()
    if not normalized_query or top_k <= 0:
        return []

    count = _collection.count()
    if count == 0:
        return []

    results = _collection.query(
        query_texts=[normalized_query],
        n_results=count,
        include=["documents", "metadatas", "distances"],
    )
    documents = results.get("documents", [[]])[0] or []
    metadatas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    product_matches = find_catalog_product_mentions(normalized_query)
    product_ranks = {
        str(product["name"]): index for index, product in enumerate(product_matches)
    }
    policy_ranks = _policy_matches(normalized_query)

    ranked_context: list[tuple[tuple[int, int, int], dict[str, Any]]] = []
    semantic_context: dict[str, dict[str, Any]] = {}
    for index, text in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        source = metadata.get("source", "")
        title = metadata.get("title", "")
        item = {
            "text": text,
            "source": source,
            "title": title,
            "distance": float(distance) if distance is not None else None,
        }
        semantic_context[f"{source}:{title}"] = item
        if source == "catalog.json" and title in product_ranks:
            rank = (0, product_ranks[title], index)
        elif source == "policies.md" and title in policy_ranks:
            rank = (1, policy_ranks[title][0], index)
        else:
            rank = (2, index, index)
        ranked_context.append((rank, item))

    warranty_overview_query = any(
        phrase in normalized_query.casefold()
        for phrase in (
            "all hardware",
            "standard warranty",
            "warranty period",
            "warranty duration",
            "warranty months",
            "longer warranty",
        )
    )
    if (
        not product_matches
        and "Warranty & Support" in policy_ranks
        and warranty_overview_query
    ):
        warranty_examples: dict[int, dict[str, Any]] = {}
        for product in _catalog_records():
            months = int(product["warranty_months"])
            if months > 12 and months not in warranty_examples:
                warranty_examples[months] = product
        example_order = [18, 24, 36, 60]
        for months in example_order:
            product = warranty_examples.get(months)
            if product is None:
                continue
            item = semantic_context.get(f"catalog.json:{product['name']}")
            if item is not None:
                ranked_context.append(((1, len(policy_ranks) + months, 0), item))

    ranked_context.sort(key=lambda entry: entry[0])
    has_lexical_match = bool(product_matches or policy_ranks)
    if has_lexical_match:
        relevant = [
            item
            for rank, item in ranked_context
            if rank[0] < 2
        ]
        return relevant[:top_k]
    return [item for _, item in ranked_context[:top_k]]
