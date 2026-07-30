#!/usr/bin/env python3
"""Query the Boohee food API with a private Wiki cache and daily quota."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE_URL = "https://api.boohee.com/open-apis"
DAILY_LIMIT = 30
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 15
CODE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
KIND_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class BooheeError(Exception):
    pass


def require_wiki() -> Path:
    raw = os.environ.get("WIKI_PATH", "").strip()
    if not raw:
        raise BooheeError("WIKI_PATH is not configured")
    wiki = Path(raw).expanduser().resolve()
    if wiki == Path("/"):
        raise BooheeError("Refusing to use filesystem root as WIKI_PATH")
    return wiki


def cache_root(wiki: Path) -> Path:
    root = wiki / "raw" / "sources" / "boohee"
    root.mkdir(parents=True, exist_ok=True)
    return root


def canonical_key(operation: str, payload: object) -> str:
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{operation}:{body}".encode()).hexdigest()


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        raise BooheeError(f"Invalid cache file: {path.name}") from exc


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


@contextmanager
def quota_slot(root: Path):
    usage_dir = root / "usage"
    usage_dir.mkdir(parents=True, exist_ok=True)
    lock_path = usage_dir / ".quota.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        today = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
        usage_path = usage_dir / f"{today}.json"
        usage = read_json(usage_path) or {"date": today, "calls": 0}
        if not isinstance(usage.get("calls"), int):
            raise BooheeError("Invalid quota counter")
        if usage["calls"] >= DAILY_LIMIT:
            raise BooheeError(f"Boohee daily limit reached ({DAILY_LIMIT} calls)")
        usage["calls"] += 1
        write_json(usage_path, usage)
        try:
            yield usage
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def api_key() -> str:
    key = os.environ.get("BOHE_NUTRITION_API_KEY", "").strip()
    if not key:
        raise BooheeError("BOHE_NUTRITION_API_KEY is not configured")
    return key


def request_api(root: Path, method: str, path: str, query: dict | None = None, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json", "X-Api-Key": api_key()}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with quota_slot(root):
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise BooheeError(f"Boohee API returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise BooheeError("Boohee API request failed") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise BooheeError("Boohee API response exceeded size limit")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BooheeError("Boohee API returned invalid JSON") from exc
    if not isinstance(payload, dict) or payload.get("code") != 0:
        raise BooheeError(f"Boohee API error: {payload.get('message', 'unknown error') if isinstance(payload, dict) else 'invalid response'}")
    return payload


def cached_call(root: Path, operation: str, method: str, path: str, payload: dict, body: dict | None = None) -> dict:
    digest = canonical_key(operation, payload)
    cache_path = root / operation / f"{digest}.json"
    cached = read_json(cache_path)
    if cached is not None:
        cached["_cache"] = "hit"
        return cached
    response = request_api(root, method, path, query=payload if body is None else None, body=body)
    response["_cached_at"] = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
    write_json(cache_path, response)
    response["_cache"] = "miss"
    return response


def valid_code(value: str) -> str:
    if not CODE_RE.fullmatch(value):
        raise BooheeError("Invalid food code")
    return value


def write_food_summary(wiki: Path, response: dict) -> None:
    data = response.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("code"), str):
        return
    code = valid_code(data["code"])
    nutrients = []
    for key in ("calories", "protein", "fat", "carbohydrate"):
        value = data.get(key)
        if isinstance(value, dict) and "value" in value:
            nutrients.append(f"| {value.get('name', key)} | {value['value']} | {value.get('unit_name', value.get('unit', ''))} |")
    target = wiki / "concepts" / "food-db" / "boohee" / f"{code}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {data.get('name', code)}",
        "",
        "- Source: Boohee Food API",
        f"- Food code: {code}",
        f"- Cached at: {response.get('_cached_at', '')}",
        "- Basis: values supplied by the database; verify a user-provided package label first.",
        "",
        "| Nutrient | Value | Unit |",
        "| --- | ---: | --- |",
        *nutrients,
        "",
    ]
    target.write_text("\n".join(lines), encoding="utf-8")


def command_search(args: argparse.Namespace, wiki: Path, root: Path) -> dict:
    query: dict[str, object] = {"page": args.page, "per_page": args.per_page, "with_units": "true" if args.with_units else "false"}
    if args.keyword:
        if not 1 <= len(args.keyword) <= 30:
            raise BooheeError("keyword must be 1-30 characters")
        query["keyword"] = args.keyword
    elif re.fullmatch(r"\d{13}", args.barcode or ""):
        query["barcode"] = args.barcode
    else:
        raise BooheeError("provide a 1-30 character keyword or a 13-digit barcode")
    return cached_call(root, "search", "GET", "/v1/food/search", query)


def command_detail(args: argparse.Namespace, wiki: Path, root: Path) -> dict:
    query = {"code": valid_code(args.code), "with_ingredients": "true", "with_units": "true", "with_materials": "true"}
    response = cached_call(root, "detail", "GET", "/v1/food/detail", query)
    write_food_summary(wiki, response)
    return response


def command_category(args: argparse.Namespace, wiki: Path, root: Path) -> dict:
    if args.category_id < 1 or not KIND_RE.fullmatch(args.kind):
        raise BooheeError("Invalid category id or kind")
    query = {"id": args.category_id, "kind": args.kind, "with_units": "true" if args.with_units else "false"}
    return cached_call(root, "category-list", "GET", "/v1/food/list", query)


def command_ingredients(args: argparse.Namespace, wiki: Path, root: Path) -> dict:
    try:
        foods = json.loads(args.foods_json)
    except json.JSONDecodeError as exc:
        raise BooheeError("foods-json must be valid JSON") from exc
    if not isinstance(foods, list) or not 1 <= len(foods) <= 50:
        raise BooheeError("foods-json must contain 1-50 foods")
    for food in foods:
        if not isinstance(food, dict):
            raise BooheeError("Each food must be an object")
        if "code" in food:
            valid_code(str(food["code"]))
            if not isinstance(food.get("weight"), (int, float)) or food["weight"] <= 0:
                raise BooheeError("code entries require a positive gram weight")
        elif not re.fullmatch(r"\d{13}", str(food.get("barcode", ""))):
            raise BooheeError("Each food requires a code or 13-digit barcode")
    body = {"foods": foods}
    return cached_call(root, "ingredients", "POST", "/v1/food/ingredients", body, body=body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Boohee food API client with private Wiki cache")
    subparsers = parser.add_subparsers(dest="command", required=True)
    search = subparsers.add_parser("search")
    group = search.add_mutually_exclusive_group(required=True)
    group.add_argument("--keyword")
    group.add_argument("--barcode")
    search.add_argument("--page", type=int, default=1)
    search.add_argument("--per-page", type=int, default=50, choices=range(1, 51))
    search.add_argument("--with-units", action="store_true")
    detail = subparsers.add_parser("detail")
    detail.add_argument("--code", required=True)
    category = subparsers.add_parser("category-list")
    category.add_argument("--category-id", type=int, required=True)
    category.add_argument("--kind", required=True)
    category.add_argument("--with-units", action="store_true")
    ingredients = subparsers.add_parser("ingredients")
    ingredients.add_argument("--foods-json", required=True)
    args = parser.parse_args()
    if args.command == "search" and (args.page < 1):
        raise BooheeError("page must be positive")
    wiki = require_wiki()
    root = cache_root(wiki)
    handlers = {"search": command_search, "detail": command_detail, "category-list": command_category, "ingredients": command_ingredients}
    result = handlers[args.command](args, wiki, root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BooheeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
