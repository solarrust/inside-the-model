"""Typos: keyboard layouts, finding real typos, generating synthetic ones."""
from __future__ import annotations

import random
import re

RU_ROWS = ["ёйцукенгшщзхъ", "фывапролджэ", "ячсмитьбю"]
EN_ROWS = ["`qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,."]
# The same physical key in two layouts (ЙЦУКЕН ↔ QWERTY)
RU2EN = {r: e for rr, ee in zip(RU_ROWS, EN_ROWS) for r, e in zip(rr, ee)}
EN2RU = {e: r for r, e in RU2EN.items()}


def _neighbors(rows: list[str]) -> dict[str, set[str]]:
    """Neighbour keys: left, right and the two nearest in the rows above and below."""
    nb: dict[str, set[str]] = {}
    for i, row in enumerate(rows):
        for j, ch in enumerate(row):
            s = set()
            for dj in (-1, 1):
                if 0 <= j + dj < len(row):
                    s.add(row[j + dj])
            for di in (-1, 1):
                if 0 <= i + di < len(rows):
                    other = rows[i + di]
                    for dj in (0, 1) if di == -1 else (-1, 0):
                        if 0 <= j + dj < len(other):
                            s.add(other[j + dj])
            nb[ch] = {c for c in s if c.isalpha()}
    return nb


NEIGHBORS = {"ru": _neighbors(RU_ROWS), "en": _neighbors(EN_ROWS)}
ALPHA = {"ru": "абвгдеёжзийклмнопрстуфхцчшщъыьэюя", "en": "abcdefghijklmnopqrstuvwxyz"}


def wrong_layout(text: str) -> str:
    """Text typed in the English layout instead of the Russian one: «привет» → «ghbdtn»."""
    out = []
    for ch in text:
        low = ch.lower()
        m = RU2EN.get(low)
        out.append(ch if m is None else (m.upper() if ch.isupper() and m.isalpha() else m))
    return "".join(out)


# --- Typo kinds -------------------------------------------------------------

def typo_variants(word: str, lang: str) -> list[tuple[str, str]]:
    """All single-edit typos of a word: (kind, variant). Kind names are Russian keys used in results/."""
    nb, alpha = NEIGHBORS[lang], ALPHA[lang]
    out = []
    w = word
    for i, ch in enumerate(w):
        low = ch.lower()
        for n in nb.get(low, ()):  # neighbour key
            out.append(("сосед", w[:i] + n + w[i + 1:]))
        out.append(("пропуск", w[:i] + w[i + 1:]))
        out.append(("повтор", w[:i] + ch + w[i:]))
        if i + 1 < len(w) and w[i] != w[i + 1]:
            out.append(("перестановка", w[:i] + w[i + 1] + w[i] + w[i + 2:]))
        for n in nb.get(low, ()):  # extra neighbour key
            out.append(("вставка", w[:i] + n + w[i:]))
    return out


def classify(typo: str, correct: str, lang: str = "ru") -> str | None:
    for kind, v in typo_variants(correct, lang):
        if v == typo:
            return kind
    if len(typo) == len(correct) and sum(a != b for a, b in zip(typo, correct)) == 1:
        return "замена"
    return None


def make_typo(word: str, lang: str, rng: random.Random, weights: dict[str, float]) -> str:
    variants = typo_variants(word, lang)
    kinds = [k for k in weights if any(v[0] == k for v in variants)]
    if not kinds:
        return word
    kind = rng.choices(kinds, [weights[k] for k in kinds])[0]
    return rng.choice([v for k, v in variants if k == kind])


WORD = re.compile(r"[A-Za-zА-Яа-яЁё]+")


def corrupt(text: str, rate: float, lang: str, seed: int, weights: dict[str, float]) -> str:
    """Puts one typo into a share `rate` of words that are 3+ letters long."""
    rng = random.Random(seed)

    def sub(m: re.Match) -> str:
        w = m.group(0)
        if len(w) >= 3 and rng.random() < rate:
            return make_typo(w, lang, rng, weights)
        return w

    return WORD.sub(sub, text)
