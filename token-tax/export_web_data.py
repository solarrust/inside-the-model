"""Builds a compact JSON for the article charts: src/data/tokens.json."""
import json
import os
from pathlib import Path

HERE = Path(__file__).parent
R = HERE / "results"
s = json.loads((R / "exp1_summary.json").read_text())
cm = json.loads((R / "exp1_claude_models.json").read_text())
ty = json.loads((R / "exp2_typos.json").read_text())
an = json.loads((R / "exp3_answers.json").read_text())["summary"]
f = s["flores"]

tokenizers = [{**t, "ru_premium": f["rus_Cyrl"][f"{t['key']}_premium"], "blog_premium": s["blog_all"][f"{t['key']}_premium"],
               "en": f["eng_Latn"][t["key"]], "ru": f["rus_Cyrl"][t["key"]]} for t in s["tokenizers"]]
languages = [{"code": c, "name": r["name"], **{t["key"]: r[f"{t['key']}_premium"] for t in s["tokenizers"]},
              "bytes": r["bytes_premium"]} for c, r in f.items()]
typos = {k: {lang: [0] + [ty["synthetic_pct"][f"{k}|{lang}|{rate}"] for rate in (0.02, 0.05, 0.1)] for lang in ("ru", "en")}
         for k in ty["labels"]}
out = {
    "source": "github.com/solarrust/inside-the-model/tree/main/token-tax — FLORES-200 devtest (1012 предложений), статьи блога; замер 2026-11-22",
    "tokenizers": tokenizers,
    "languages": languages,
    "claude_models": cm,
    "typos": {"rates": [0, 2, 5, 10], "series": typos, "labels": ty["labels"],
              "per_typo": ty["real"], "wrong_layout": ty["wrong_layout_ratio"]},
    # Opus 5.5 answers: per-answer means and the RU/EN ratio of totals (both languages have the same number of answers)
    "answers": {"model": an["model"], "n": an["pairs"], "spent_usd": an["spent_usd"], "by_lang": an["by_lang"],
                "cost": an["cost_per_answer_usd"],
                "ratio": {k: round(an["by_lang"]["ru"][k] / an["by_lang"]["en"][k], 4)
                          for k in ("words", "chars", "answer_tokens", "output_tokens")},
                "flores_claude": round(cm["claude-opus-5-5"]["rus_Cyrl"] / cm["claude-opus-5-5"]["eng_Latn"], 3)},
}
# Where to write: the blog repository. BLOG_DIR sets its path.
dst = Path(os.environ.get("BLOG_DIR", HERE.parent.parent)) / "src/data/tokens.json"
dst.parent.mkdir(exist_ok=True)
dst.write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(dst, dst.stat().st_size)
