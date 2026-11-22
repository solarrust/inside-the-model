"""Experiment 3: how many tokens an answer takes in Russian and in English.

20 identical tasks in two languages (exp3_tasks.json), Claude Opus 5.5 with default settings.
Each task runs RUNS times. We count:
  * output_tokens from usage: everything billed as output, thinking + answer;
  * tokens of the answer itself: via count_tokens, minus the baseline (as in exp1);
  * thinking = output_tokens - answer tokens (the API does not return the thinking text);
  * words and characters of the answer.

Requests are paid. The script stops when spending reaches BUDGET dollars.
Full answers go to data/exp3_answers.jsonl (not committed); results/ keeps only the numbers.
Run: .venv/bin/python exp3_answers.py [--limit N]
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import anthropic

HERE = Path(__file__).parent
MODEL = "claude-opus-5-5"
PRICE_IN, PRICE_OUT = 4 / 1e6, 20 / 1e6  # $ per token, Opus 5.5 (claude-api skill, 2026-11-22)
BUDGET = 4.8  # headroom for the last request: at most $0.16
RUNS = 3
MAX_TOKENS = 8000

client = anthropic.Anthropic()
tasks = json.loads((HERE / "exp3_tasks.json").read_text("utf-8"))
if "--limit" in sys.argv:
    tasks = tasks[: int(sys.argv[sys.argv.index("--limit") + 1])]

raw_path = HERE / "data" / "exp3_answers.jsonl"
raw_path.parent.mkdir(exist_ok=True)
done = {}
if raw_path.exists():
    for line in raw_path.read_text("utf-8").splitlines():
        r = json.loads(line)
        done[(r["task"], r["lang"], r["run"])] = r

base = client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": "a"}]).input_tokens - 1


def count(text: str) -> int:
    return client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": text}]).input_tokens - base


spent = sum(r["cost"] for r in done.values())
with raw_path.open("a", encoding="utf-8") as out:
    for run in range(RUNS):
        for i, task in enumerate(tasks):
            for lang in ("ru", "en"):
                if (i, lang, run) in done:
                    continue
                if spent >= BUDGET:
                    print(f"Budget ${BUDGET} reached, stopping")
                    break
                resp = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": task[lang]}],
                )
                text = "".join(b.text for b in resp.content if b.type == "text")
                u = resp.usage
                cost = u.input_tokens * PRICE_IN + u.output_tokens * PRICE_OUT
                spent += cost
                answer_tokens = count(text)
                r = {
                    "task": i, "lang": lang, "run": run, "stop": resp.stop_reason,
                    "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                    "answer_tokens": answer_tokens, "thinking_tokens": max(u.output_tokens - answer_tokens, 0),
                    "words": len(text.split()), "chars": len(text), "cost": cost, "text": text,
                }
                done[(i, lang, run)] = r
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
                out.flush()
                print(f"{i:2} {lang} run{run}: out {u.output_tokens:5} answer {answer_tokens:5} words {r['words']:4}  ${spent:.2f}")

rows = list(done.values())
pairs = [(done[(i, "ru", k)], done[(i, "en", k)]) for (i, lang, k) in done if lang == "ru" and (i, "en", k) in done]


def mean(xs):
    return round(st.mean(xs), 1)


def ratio(key):
    """Ratio of RU / EN totals: the article's conclusions rest on these numbers."""
    return round(sum(ru[key] for ru, _ in pairs) / sum(en[key] for _, en in pairs), 3)


def median_ratio(key):
    """Median of per-pair ratios: shows the spread from task to task."""
    return round(st.median(ru[key] / en[key] for ru, en in pairs if en[key]), 2)


summary = {
    "model": MODEL, "runs": RUNS, "pairs": len(pairs), "spent_usd": round(spent, 2),
    "by_lang": {
        lang: {k: mean([r[k] for r in rows if r["lang"] == lang]) for k in ("input_tokens", "output_tokens", "answer_tokens", "thinking_tokens", "words", "chars")}
        for lang in ("ru", "en")
    },
    "ru_to_en_ratio": {k: ratio(k) for k in ("input_tokens", "output_tokens", "answer_tokens", "thinking_tokens", "words", "chars", "cost")},
    "ru_to_en_median_pair_ratio": {k: median_ratio(k) for k in ("output_tokens", "answer_tokens", "words", "chars")},
    "note": "Размышление = output_tokens − токены видимого ответа по count_tokens; это оценка. Задача 12 (стихотворение) даёт половину разницы в output_tokens.",
    "answer_tokens_per_word": {lang: round(sum(r["answer_tokens"] for r in rows if r["lang"] == lang) / sum(r["words"] for r in rows if r["lang"] == lang), 2) for lang in ("ru", "en")},
    "cost_per_answer_usd": {lang: round(st.mean(r["cost"] for r in rows if r["lang"] == lang), 4) for lang in ("ru", "en")},
    "truncated": sum(r["stop"] == "max_tokens" for r in rows),
}
(HERE / "results").mkdir(exist_ok=True)
per_task = [{k: v for k, v in r.items() if k != "text"} for r in sorted(rows, key=lambda r: (r["task"], r["run"], r["lang"]))]
(HERE / "results" / "exp3_answers.json").write_text(json.dumps({"summary": summary, "per_answer": per_task}, ensure_ascii=False, indent=1))
print(json.dumps(summary, ensure_ascii=False, indent=1))
