"""Игрушечный BPE для статьи: какие пары склеиваются по шагам."""
from collections import Counter

corpus = {"кот": 6, "кота": 3, "коту": 2, "рот": 4, "крот": 1}
words = {tuple(w): n for w, n in corpus.items()}
for step in range(1, 6):
    pairs = Counter()
    for w, n in words.items():
        for a, b in zip(w, w[1:]):
            pairs[a, b] += n
    (a, b), n = pairs.most_common(1)[0]
    new = {}
    for w, c in words.items():
        out, i = [], 0
        while i < len(w):
            if i + 1 < len(w) and (w[i], w[i + 1]) == (a, b):
                out.append(a + b); i += 2
            else:
                out.append(w[i]); i += 1
        new[tuple(out)] = c
    words = new
    print(f"шаг {step}: {a}+{b} ({n} раз) →", "  ".join("·".join(w) for w in words))
