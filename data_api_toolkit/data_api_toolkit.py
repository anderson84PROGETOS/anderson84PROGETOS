#!/usr/bin/env python3

# instalar o   pip install pyarrow

# ou instalar  pip install pyarrow  --break-system-packages
"""
Kit de Ferramentas de Dados e API — um utilitário Python de arquivo único para:
• Buscar dados de APIs HTTP (com novas tentativas, paginação e tratamento de limite de taxa)
• Analisar/validar entradas (datas, decimais, conversores baseados em regex)
• Analisar dados localmente com estatísticas básicas e resumos de séries temporais
• Exportar resultados para CSV/JSON/Parquet

Usage examples

https://github.com/pallets/flask/issues

"/repos/pallets/flask/issues"


fetch   Fetch data from an HTTP API salvar em JSON

python3 data_api_toolkit.py fetch --api github --endpoint "/repos/pallets/flask/issues" --outfile repo.json
============================================================================================================

Exportar para Parquet

python3 data_api_toolkit.py export --infile repo.json --outfile repo.parquet

python3 data_api_toolkit.py export --infile repo.json --outfile repo.csv
========================================================================

Analyze → funciona com JSON, CSV ou Parquet

# JSON
python3 data_api_toolkit.py analyze --infile repo.json

# CSV
python3 data_api_toolkit.py analyze --infile repo.csv

# Parquet
python3 data_api_toolkit.py analyze --infile repo.parquet
==========================================================================

Observações:
  • Defina variáveis ​​de ambiente para personalizar os padrões (veja ENV_DEFAULTS abaixo).
  • Para APIs que exigem autenticação, passe --token ou defina uma variável de ambiente.
  • Este arquivo evita dependências pesadas; requer apenas: requests, pandas, python-dateutil, pyarrow (opcional, para Parquet).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import requests
import pandas as pd
from dateutil import parser as dateparser

# ------------------------------
# Logging
# ------------------------------
LOG = logging.getLogger("data_api_toolkit")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
LOG.addHandler(handler)
LOG.setLevel(logging.INFO)

# ------------------------------
# Environment defaults
# ------------------------------
ENV_DEFAULTS = {
    "TIMEZONE": "UTC",
    "HTTP_TIMEOUT": "20",  # seconds
    "HTTP_MAX_RETRIES": "3",
    "HTTP_BACKOFF": "1.5",  # seconds multiplier
    "GITHUB_BASE_URL": "https://api.github.com",
}

for k, v in ENV_DEFAULTS.items():
    os.environ.setdefault(k, v)

# ------------------------------
# Helpers: regex-powered type converters
# ------------------------------

def with_pattern(pattern: str, regex_group_count: Optional[int] = None):
    """Attach a regex pattern to a converter function (for documentation/introspection).

    Example:
        @with_pattern(r"\\d+")
        def parse_number(text):
            return int(text)
    """

    def decorator(func):
        func.pattern = pattern  # type: ignore[attr-defined]
        func.regex_group_count = regex_group_count  # type: ignore[attr-defined]
        return func

    return decorator


@with_pattern(r"^\\d{4}-\\d{2}-\\d{2}$")
def to_date(s: str) -> datetime:
    """Parse YYYY-MM-DD into datetime (UTC)."""
    dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt


@with_pattern(r"^[+-]?\\d+(?:\\.\\d+)?$")
def to_decimal(s: str) -> Decimal:
    try:
        return Decimal(s)
    except InvalidOperation as e:
        raise argparse.ArgumentTypeError(f"Invalid decimal: {s}") from e


# ------------------------------
# API client with retries + pagination
# ------------------------------
@dataclass
class ApiConfig:
    base_url: str
    token: Optional[str] = None


class ApiClient:
    def __init__(self, config: ApiConfig):
        self.base_url = config.base_url.rstrip("/")
        self.token = config.token
        self.timeout = float(os.getenv("HTTP_TIMEOUT", "20"))
        self.max_retries = int(os.getenv("HTTP_MAX_RETRIES", "3"))
        self.backoff = float(os.getenv("HTTP_BACKOFF", "1.5"))
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = endpoint
        if not endpoint.startswith("http"):
            url = f"{self.base_url}{endpoint if endpoint.startswith('/') else '/' + endpoint}"

        retries = 0
        while True:
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kwargs)
                if resp.status_code in {429, 500, 502, 503, 504} and retries < self.max_retries:
                    delay = self.backoff ** (retries + 1)
                    LOG.warning("Transient error %s. Retrying in %.2fs", resp.status_code, delay)
                    time.sleep(delay)
                    retries += 1
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                if retries >= self.max_retries:
                    raise
                delay = self.backoff ** (retries + 1)
                LOG.warning("Request failed: %s. Retrying in %.2fs", e, delay)
                time.sleep(delay)
                retries += 1

    def get_json(self, endpoint: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        resp = self._request("GET", endpoint, params=params)
        # Handle rate limit from GitHub specifically
        if resp.headers.get("X-RateLimit-Remaining") == "0":
            reset = resp.headers.get("X-RateLimit-Reset")
            if reset:
                ts = int(reset)
                wait_sec = max(0, ts - int(time.time()))
                LOG.warning("Rate limit reached. Sleeping %.1fs", wait_sec)
                time.sleep(wait_sec)
                return self.get_json(endpoint, params=params)
        try:
            return resp.json()
        except json.JSONDecodeError:
            return resp.text

    def paged(self, endpoint: str, params: Optional[Mapping[str, Any]] = None, page_param: str = "page", per_page: int = 100, max_pages: int = 10) -> Iterable[Any]:
        """Simple page iteration using numeric page parameter."""
        p: Dict[str, Any] = dict(params or {})
        p[page_param] = 1
        p["per_page"] = per_page
        pages = 0
        while pages < max_pages:
            data = self.get_json(endpoint, params=p)
            if not data:
                break
            yield data
            pages += 1
            p[page_param] += 1


# ------------------------------
# Built-in API presets
# ------------------------------

def build_client(name: str, token: Optional[str]) -> ApiClient:
    name = name.lower()
    if name == "github":
        base = os.getenv("GITHUB_BASE_URL", ENV_DEFAULTS["GITHUB_BASE_URL"])
        return ApiClient(ApiConfig(base_url=base, token=token))
    elif name == "jsonplaceholder":
        return ApiClient(ApiConfig(base_url="https://jsonplaceholder.typicode.com", token=None))
    elif name == "restcountries":
        return ApiClient(ApiConfig(base_url="https://restcountries.com/v3.1", token=None))
    else:
        # Treat as raw base URL
        if not name.startswith("http"):
            raise SystemExit("Unknown API preset. Use a full base URL or one of: github, jsonplaceholder, restcountries.")
        return ApiClient(ApiConfig(base_url=name, token=token))


# ------------------------------
# Data analysis helpers (pandas)
# ------------------------------

def load_dataframe(path: str) -> pd.DataFrame:
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        # Normalize JSON to rows
        if isinstance(obj, list):
            return pd.json_normalize(obj)
        elif isinstance(obj, dict):
            # try common container keys
            for key in ("items", "data", "results"):
                if key in obj and isinstance(obj[key], list):
                    return pd.json_normalize(obj[key])
            return pd.json_normalize(obj)
        else:
            raise SystemExit("Unsupported JSON structure")
    elif path.endswith(".csv"):
        return pd.read_csv(path)
    elif path.endswith(".parquet"):
        return pd.read_parquet(path)
    else:
        raise SystemExit("Unsupported file type. Use .json, .csv, or .parquet")


def analyze_dataframe(df: pd.DataFrame, date_field: Optional[str], group_by: Optional[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}

    # Basic schema
    result["columns"] = list(df.columns)
    result["rows"] = int(df.shape[0])

    # Summary of numeric columns
    num_df = df.select_dtypes(include=["number"])  # type: ignore
    if not num_df.empty:
        result["numeric_summary"] = num_df.describe().to_dict()

    if date_field and date_field in df.columns:
        dt = pd.to_datetime(df[date_field], errors="coerce", utc=True)
        by_day = dt.dt.strftime("%Y-%m-%d").value_counts().sort_index()
        result["by_day_counts"] = by_day.to_dict()

    if group_by and group_by in df.columns:
        result["grouped_counts"] = df[group_by].value_counts(dropna=False).to_dict()

    return result


def export_dataframe(df: pd.DataFrame, outfile: str) -> None:
    if outfile.endswith(".json"):
        df.to_json(outfile, orient="records", lines=False, force_ascii=False)
    elif outfile.endswith(".csv"):
        df.to_csv(outfile, index=False)
    elif outfile.endswith(".parquet"):
        try:
            import pyarrow  # noqa: F401
        except Exception as e:
            raise SystemExit("Writing Parquet requires 'pyarrow' to be installed.") from e
        df.to_parquet(outfile, index=False)
    else:
        raise SystemExit("Unsupported export format. Use .json, .csv, or .parquet")


# ------------------------------
# CLI commands
# ------------------------------

def cmd_fetch(args: argparse.Namespace) -> None:
    client = build_client(args.api, token=args.token or os.getenv(args.token_env) if args.token_env else args.token)

    # Parse key=value pairs from --params
    params: Dict[str, Any] = {}
    for kv in args.params or []:
        if "=" not in kv:
            raise SystemExit(f"Invalid --params entry (expected key=value): {kv}")
        k, v = kv.split("=", 1)
        # Cast simple numerics
        if re.fullmatch(r"[0-9]+", v):
            v = int(v)
        elif re.fullmatch(r"[0-9]+\\.[0-9]+", v):
            v = float(v)
        params[k] = v

    if args.paged:
        all_rows: List[Any] = []
        for page in client.paged(args.endpoint, params=params, per_page=args.per_page, max_pages=args.max_pages):
            if isinstance(page, list):
                all_rows.extend(page)
            else:
                all_rows.append(page)
        data = all_rows
    else:
        data = client.get_json(args.endpoint, params=params)

    # Write output
    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    LOG.info("Saved %s", args.outfile)


def cmd_analyze(args: argparse.Namespace) -> None:
    df = load_dataframe(args.infile)
    report = analyze_dataframe(df, args.date_field, args.group_by)
    # Pretty print
    print(json.dumps(report, ensure_ascii=False, indent=2))


def cmd_export(args: argparse.Namespace) -> None:
    df = load_dataframe(args.infile)
    export_dataframe(df, args.outfile)
    LOG.info("Exported %s", args.outfile)


# ------------------------------
# Argument parser
# ------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Data & API Toolkit")
    sub = p.add_subparsers(dest="command", required=True)

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch data from an HTTP API")
    p_fetch.add_argument("--api", required=True, help="Preset (github, jsonplaceholder, restcountries) or a base URL")
    p_fetch.add_argument("--endpoint", required=True, help="Endpoint path, e.g., /repos/owner/repo/issues")
    p_fetch.add_argument("--params", nargs="*", help="Optional query params as key=value pairs")
    p_fetch.add_argument("--token", help="Bearer token for Authorization header")
    p_fetch.add_argument("--token-env", help="Env var name that holds the token (overrides --token if present)")
    p_fetch.add_argument("--outfile", required=True, help="File path to write JSON output")
    p_fetch.add_argument("--paged", action="store_true", help="Iterate using numeric pages")
    p_fetch.add_argument("--per-page", type=int, default=100, help="Items per page when --paged is used")
    p_fetch.add_argument("--max-pages", type=int, default=10, help="Max pages to iterate when --paged is used")
    p_fetch.set_defaults(func=cmd_fetch)

    # analyze
    p_an = sub.add_parser("analyze", help="Analyze a local data file (JSON/CSV/Parquet)")
    p_an.add_argument("--infile", required=True)
    p_an.add_argument("--date-field", help="Column name to treat as date/time for by-day counts")
    p_an.add_argument("--group-by", help="Column name to count occurrences")
    p_an.set_defaults(func=cmd_analyze)

    # export
    p_ex = sub.add_parser("export", help="Convert between formats (JSON/CSV/Parquet)")
    p_ex.add_argument("--infile", required=True)
    p_ex.add_argument("--outfile", required=True)
    p_ex.set_defaults(func=cmd_export)

    return p


# ------------------------------
# Entrypoint
# ------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except KeyboardInterrupt:
        LOG.error("Interrupted by user")
        return 2
    except Exception as e:
        LOG.exception("Error: %s", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
