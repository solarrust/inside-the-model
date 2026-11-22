"""Ищет настоящие опечатки в промптах Алёны (private/prompts.jsonl).

Опечатка-кандидат — слово, которого нет в словаре pymorphy3, но которое одной правкой
(соседняя клавиша, пропуск, повтор, перестановка, вставка, замена) превращается в словарное.
Не та раскладка — латиница, которая по клавишам ЙЦУКЕН даёт словарное русское слово.

Выход (не коммитится): private/real_typos.csv — пары для ручной проверки,
private/prompts_fixed.jsonl — промпты с исправленными опечатками.
Агрегаты (коммитятся): results/exp2_real_typos_stats.json.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

import pymorphy3

from typos_lib import EN2RU, classify

HERE = Path(__file__).parent
morph = pymorphy3.MorphAnalyzer()
RU = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
CYR = re.compile(r"[а-яё]+", re.I)
LAT = re.compile(r"\b[a-z;',.\[\]`]{4,}\b", re.I)
# Жаргон Алёны, который словарь не знает, а поиск принимает за опечатки (проверено вручную)
JARGON = {"прод", "проде", "юай", "акк", "блоб", "пушь", "винды", "рест", "пиарь", "промо", "гист"}
EN_WORDS = {w.strip().lower() for w in open("/usr/share/dict/words", encoding="utf-8")}
PREF = {"сосед": 0, "перестановка": 1, "пропуск": 2, "повтор": 3, "вставка": 4, "замена": 5}

prompts = [json.loads(l) for l in open(HERE / "private/prompts.jsonl", encoding="utf-8")]
# Длинные сообщения — обычно вставленный текст, а не набранный руками
typed = [p for p in prompts if len(p["text"]) <= 1500]
freq = Counter(w.lower() for p in typed for w in CYR.findall(p["text"]))


def known(w: str) -> bool:
    return morph.word_is_known(w)


def edits1(w: str) -> set[str]:
    splits = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    return {a + b[1:] for a, b in splits if b} | {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1} \
        | {a + c + b[1:] for a, b in splits if b for c in RU} | {a + c + b for a, b in splits for c in RU}


def correct(w: str) -> tuple[str, str] | None:
    # Настоящая опечатка обычно портит слово, которое автор пишет часто.
    # Редкое «исправление» чаще значит, что исходное слово — жаргон («закомить» → «закосить»).
    cands = [c for c in edits1(w) if c != w and known(c) and freq.get(c, 0) >= 2]
    scored = []
    for c in cands:
        kind = classify(w, c, "ru")
        if kind == "замена" and freq.get(c, 0) < 5:
            continue
        if kind:
            scored.append((PREF[kind], -freq.get(c, 0), c, kind))
    if not scored:
        return None
    _, _, c, kind = min(scored)
    return c, kind


pairs, n_words, layout = [], 0, []
fixed = []
for p in typed:
    t = p["text"]
    words = CYR.findall(t)
    n_words += len(words)
    new = t
    for w in words:
        lw = w.lower()
        if len(lw) < 3 or lw in JARGON or known(lw) or freq[lw] > 2:  # частое «незнакомое» слово — жаргон, а не опечатка
            continue
        r = correct(lw)
        if r:
            pairs.append({"typo": lw, "correct": r[0], "kind": r[1], "context": t[:160].replace("\n", " ")})
            new = re.sub(rf"\b{re.escape(w)}\b", r[0] if w.islower() else r[0].capitalize(), new, count=1)
    for m in LAT.finditer(t):
        ru = "".join(EN2RU.get(ch.lower(), ch) for ch in m.group(0))
        if m.group(0).lower() not in EN_WORDS and CYR.fullmatch(ru) and known(ru.lower()) and len(ru) >= 4:
            layout.append({"typo": m.group(0), "correct": ru, "kind": "раскладка", "context": t[:160].replace("\n", " ")})
    fixed.append({**p, "fixed": new})

with open(HERE / "private/real_typos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["typo", "correct", "kind", "context"])
    w.writeheader()
    w.writerows(pairs + layout)
with open(HERE / "private/prompts_fixed.jsonl", "w", encoding="utf-8") as f:
    for r in fixed:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

kinds = Counter(p["kind"] for p in pairs)
stats = {
    "prompts": len(typed), "words": n_words, "typos": len(pairs), "wrong_layout": len(layout),
    "typo_rate_words": round(len(pairs) / n_words, 4),
    "prompts_with_typo": sum(r["fixed"] != r["text"] for r in fixed),
    "kinds": dict(kinds.most_common()),
}
(HERE / "results").mkdir(exist_ok=True)
(HERE / "results/exp2_real_typos_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1))
print(json.dumps(stats, ensure_ascii=False))
