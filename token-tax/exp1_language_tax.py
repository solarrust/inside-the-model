"""Experiment 1. The language tax.

Metric: tokenization premium (Petrov et al., 2023), tokens of a text in language X
divided by tokens of the same text in English. 1.0 is parity, 2.0 is twice as expensive.

Corpora:
  * FLORES-200 devtest: 1012 sentences, professional translation into 200+ languages (CC BY-SA 4.0).
  * Blog: RU and EN versions of posts from src/content/blog, prose only (no code, links, JSX).

Run: .venv/bin/python exp1_language_tax.py [--claude]
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path

from tokenizers_lib import all_local, claude

HERE = Path(__file__).parent
FLORES = HERE / "data" / "flores" / "flores200_dataset" / "devtest"
# Blog posts live in the blog's own repository. Without them the script counts FLORES only.
BLOG = Path(os.environ.get("BLOG_DIR", HERE.parent.parent / "src" / "content" / "blog"))
OUT = HERE / "results"

LANGS = {
    "eng_Latn": "English",
    "rus_Cyrl": "Русский",
    "ukr_Cyrl": "Українська",
    "deu_Latn": "Deutsch",
    "fra_Latn": "Français",
    "spa_Latn": "Español",
    "por_Latn": "Português",
    "pol_Latn": "Polski",
    "tur_Latn": "Türkçe",
    "vie_Latn": "Tiếng Việt",
    "ell_Grek": "Ελληνικά",
    "heb_Hebr": "עברית",
    "arb_Arab": "العربية",
    "hin_Deva": "हिन्दी",
    "ben_Beng": "বাংলা",
    "tha_Thai": "ไทย",
    "kat_Geor": "ქართული",
    "jpn_Jpan": "日本語",
    "kor_Hang": "한국어",
    "zho_Hans": "中文",
}


def flores_text(code: str) -> str:
    return (FLORES / f"{code}.devtest").read_text(encoding="utf-8")


def strip_mdx(src: str) -> str:
    src = re.sub(r"^---\n.*?\n---\n", "", src, flags=re.S)  # frontmatter
    src = re.sub(r"```.*?```", "", src, flags=re.S)  # code blocks
    src = re.sub(r"^(import|export) .*$", "", src, flags=re.M)
    src = re.sub(r"<[^>]+>", "", src)  # JSX and HTML
    src = re.sub(r"`[^`]*`", "", src)  # inline code
    src = re.sub(r"\]\([^)]*\)", "]", src)  # link URLs
    src = re.sub(r"https?://\S+", "", src)
    src = re.sub(r"[#>*_\[\]|]", "", src)  # markup
    src = re.sub(r"\n{2,}", "\n", src)
    return src.strip()


def blog_pairs() -> dict[str, tuple[str, str]]:
    pairs = {}
    for en in sorted((BLOG / "en").glob("*.mdx")):
        ru = BLOG / "ru" / en.name
        if ru.exists():
            pairs[en.stem] = (strip_mdx(ru.read_text("utf-8")), strip_mdx(en.read_text("utf-8")))
    return pairs


def main() -> None:
    OUT.mkdir(exist_ok=True)
    toks = all_local() + (claude() if "--claude" in sys.argv else [])
    meta = [{"key": t.key, "label": t.label, "family": t.family, "year": t.year, "vocab": t.vocab} for t in toks]

    # --- FLORES ---
    texts = {c: flores_text(c) for c in LANGS}
    rows = []
    for code, name in LANGS.items():
        t = texts[code]
        row = {"lang": code, "name": name, "chars": len(t), "bytes": len(t.encode("utf-8")), "words": len(t.split())}
        for tok in toks:
            row[tok.key] = tok.count(t)
        rows.append(row)
        print(f"{name:12}", " ".join(f"{tok.key}={row[tok.key]}" for tok in toks), flush=True)
    eng = next(r for r in rows if r["lang"] == "eng_Latn")
    for r in rows:
        for tok in toks:
            r[f"{tok.key}_premium"] = round(r[tok.key] / eng[tok.key], 3)
        r["bytes_premium"] = round(r["bytes"] / eng["bytes"], 3)
        r["chars_premium"] = round(r["chars"] / eng["chars"], 3)
    with open(OUT / "exp1_flores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # --- Blog ---
    blog = []
    pairs = blog_pairs()
    ru_all = "\n".join(p[0] for p in pairs.values())
    en_all = "\n".join(p[1] for p in pairs.values())
    for name, (ru, en) in list(pairs.items()) + [("ВСЕ", (ru_all, en_all))]:
        row = {"article": name, "ru_words": len(ru.split()), "en_words": len(en.split()),
               "ru_bytes": len(ru.encode()), "en_bytes": len(en.encode())}
        for tok in toks:
            a, b = tok.count(ru), tok.count(en)
            row[f"{tok.key}_ru"], row[f"{tok.key}_en"], row[f"{tok.key}_premium"] = a, b, round(a / b, 3)
        blog.append(row)
    with open(OUT / "exp1_blog.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(blog[0].keys()))
        w.writeheader()
        w.writerows(blog)

    # Merge with previous runs: Claude is counted separately and must not be wiped by a local run.
    summary_path = OUT / "exp1_summary.json"
    old = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    keep = [m for m in old.get("tokenizers", []) if m["key"] not in {t.key for t in toks}]
    summary = {
        "tokenizers": keep + meta,
        "flores": {r["lang"]: {**old.get("flores", {}).get(r["lang"], {}), **r} for r in rows},
        "blog_all": {**old.get("blog_all", {}), **blog[-1]},
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=1))

    print("\nRussian premium over English:")
    ru = next(r for r in rows if r["lang"] == "rus_Cyrl")
    for tok in toks:
        print(f"  {tok.label:16} FLORES {ru[f'{tok.key}_premium']:.2f}   blog {blog[-1][f'{tok.key}_premium']:.2f}")
    print(f"  {'UTF-8 bytes':16} FLORES {ru['bytes_premium']:.2f}   blog {blog[-1]['ru_bytes'] / blog[-1]['en_bytes']:.2f}")
    print(f"  {'words':16} FLORES {ru['words'] / eng['words']:.2f}   blog {blog[-1]['ru_words'] / blog[-1]['en_words']:.2f}")


if __name__ == "__main__":
    main()
