"""Read ERP / bank exports as they come out of the system.

- Excel (.xlsx) or CSV, with comma or semicolon separator
- Italian or English column names (aliases are matched ignoring case)
- Amounts written as 1234.56, 1.234,56 or 1,234.56
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def find_file(folder: Path, stem: str) -> Path:
    for ext in (".xlsx", ".xls", ".csv"):
        p = folder / f"{stem}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"Missing {folder / stem}.xlsx or .csv")


def read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=object)
    # sep=None lets pandas detect "," or ";" (Italian Excel uses ";")
    return pd.read_csv(path, sep=None, engine="python", dtype=str, encoding="utf-8-sig")


def to_number(s: pd.Series) -> pd.Series:
    def conv(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, (int, float)):
            return float(v)
        t = re.sub(r"[^\d,.\-]", "", str(v))
        if not t:
            return None
        if "," in t and "." in t:  # the last separator is the decimal one
            t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
        elif "," in t:  # 1234,56 (Italian)
            t = t.replace(",", ".")
        elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", t):  # 1.234 = thousands
            t = t.replace(".", "")
        return float(t)

    return s.map(conv)


def to_date(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    text = s.astype(str).str.strip()
    iso = text.str.match(r"^\d{4}-\d{2}-\d{2}")  # 2026-06-30: year first
    out = pd.to_datetime(text.where(iso).str[:10], format="%Y-%m-%d", errors="coerce")
    # everything else is read day-first, as in Italy: 30/06/2026
    rest = pd.to_datetime(text.where(~iso), dayfirst=True, errors="coerce", format="mixed")
    return out.fillna(rest)


def standardise(df: pd.DataFrame, aliases: dict[str, list[str]], required: list[str]) -> pd.DataFrame:
    """Rename columns to the standard names using the alias lists."""
    lookup = {str(c).strip().lower(): c for c in df.columns}
    rename = {}
    for std, names in aliases.items():
        for n in [std, *names]:
            if n.lower() in lookup:
                rename[lookup[n.lower()]] = std
                break
    df = df.rename(columns=rename)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Columns not found: {missing}. Columns in the file: {list(df.columns)}. "
            "Rename them or add an alias in the script."
        )
    return df
