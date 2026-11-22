"""Experiment 2, hypothesis A: a typo breaks token merges.

1. Real typos (private/real_typos.csv): how many tokens a misspelled word costs vs the correct one.
2. Synthetic typos on FLORES devtest (ru and en): 2, 5 and 10% of words, 3 random seeds.
   Typo kinds are weighted by the frequencies of Alena's real typos (+1 for each kind).
3. Extreme case: the whole Russian text typed in the English layout ("ghbdtn").

Run: .venv/bin/python exp2_typos.py [--claude]
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
from pathlib import Path

from tokenizers_lib import all_local, claude
from typos_lib import corrupt, wrong_layout

HERE = Path(__file__).parent
FLORES = HERE / "data/flores/flores200_dataset/devtest"
OUT = HERE / "results"
KEEP = {"cl100k_base", "o200k_base", "llama3", "qwen3", "gigachat", "yandexgpt5"}
RATES = [0.02, 0.05, 0.10]
SEEDS = [1, 2, 3]

toks = [t for t in all_local() if t.key in KEEP] + (claude()[1:] if "--claude" in sys.argv else [])
stats = json.loads((OUT / "exp2_real_typos_stats.json").read_text())
# Typo kinds (keys in results/): neighbour key, omission, repetition, transposition, insertion
kinds = ["сосед", "пропуск", "повтор", "перестановка", "вставка"]
weights = {k: stats["kinds"].get(k, 0) + 1 for k in kinds}

# --- 1. Real typos ---
pairs = list(csv.DictReader(open(HERE / "private/real_typos.csv", encoding="utf-8")))
per_tok = {}
examples = []
for t in toks:
    diffs = [t.count(" " + p["typo"]) - t.count(" " + p["correct"]) for p in pairs]
    rel = [t.count(" " + p["typo"]) / t.count(" " + p["correct"]) for p in pairs]
    per_tok[t.key] = {"mean_extra_tokens": round(st.mean(diffs), 2), "mean_ratio": round(st.mean(rel), 2),
                      "share_more_expensive": round(sum(d > 0 for d in diffs) / len(diffs), 2)}
# Token splits for the article examples: «важно» / «вадно» and a few more
for t in toks:
    if t.encode_pieces:
        for w in ["важно", "вадно", "функции", "фунцкии", "привет", "ghbdtn"]:
            examples.append({"tok": t.label, "word": w, "pieces": t.encode_pieces(" " + w)})

# --- 2. Synthetic typos ---
synth = []
for lang, code in [("ru", "rus_Cyrl"), ("en", "eng_Latn")]:
    clean = (FLORES / f"{code}.devtest").read_text(encoding="utf-8")
    base = {t.key: t.count(clean) for t in toks}
    for rate in RATES:
        for seed in SEEDS:
            noisy = corrupt(clean, rate, lang, seed, weights)
            for t in toks:
                synth.append({"lang": lang, "rate": rate, "seed": seed, "tok": t.key,
                              "tokens": t.count(noisy), "clean": base[t.key]})
synth_summary = {}
for r in synth:
    k = f"{r['tok']}|{r['lang']}|{r['rate']}"
    synth_summary.setdefault(k, []).append(r["tokens"] / r["clean"] - 1)
synth_summary = {k: round(st.mean(v) * 100, 2) for k, v in synth_summary.items()}  # % increase

# --- 3. Wrong keyboard layout ---
ru = (FLORES / "rus_Cyrl.devtest").read_text(encoding="utf-8")
layout = {t.key: round(t.count(wrong_layout(ru)) / t.count(ru), 2) for t in toks}

res = {"weights": weights, "real_pairs": len(pairs), "real": per_tok, "synthetic_pct": synth_summary,
       "wrong_layout_ratio": layout, "labels": {t.key: t.label for t in toks}}
old = json.loads((OUT / "exp2_typos.json").read_text()) if (OUT / "exp2_typos.json").exists() else {}
for k in ("real", "wrong_layout_ratio", "labels"):
    res[k] = {**old.get(k, {}), **res[k]}
res["synthetic_pct"] = {**old.get("synthetic_pct", {}), **res["synthetic_pct"]}
(OUT / "exp2_typos.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
(OUT / "exp2_pieces_examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=1))

print("Real typos:", len(pairs))
for t in toks:
    r = per_tok[t.key]
    s = " ".join(f"{lang}{int(rate*100)}%=+{synth_summary[f'{t.key}|{lang}|{rate}']}%" for lang in ("ru", "en") for rate in RATES)
    print(f"{t.label:15} +{r['mean_extra_tokens']} tok/typo (x{r['mean_ratio']}, more expensive in {int(r['share_more_expensive']*100)}%) | {s} | layout x{layout[t.key]}")
