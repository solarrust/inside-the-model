# Measurements for "Is English really the cheapest language for prompts?"

Series "How a model works inside", part 1. Every number in the article comes from here. Русская версия ниже.

## Setup

```bash
uv venv .venv && uv pip install --python .venv/bin/python tiktoken tokenizers sentencepiece huggingface_hub anthropic pymorphy3 pymorphy3-dicts-ru
.venv/bin/python fetch_tokenizers.py   # tokenizer.json of open models → data/hf/
```

- FLORES-200: `curl -L https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz | tar -xz -C data/flores`. License CC BY-SA 4.0.
- Claude: `ant auth login` (no API key needed). `count_tokens` is free, the limit starts at 5,000 requests per minute. Source: `sources/claude-token-counting.md`.
- Blog posts are not in the repository. Point `BLOG_DIR` to the posts folder, otherwise `exp1_language_tax.py` counts FLORES only.

`data/` and `private/` are not committed.

## Scripts

| Script | What it does | Output |
| --- | --- | --- |
| `exp1_language_tax.py [--claude]` | Premium over English for 20 FLORES languages and the blog posts | `results/exp1_flores.csv`, `exp1_blog.csv`, `exp1_summary.json` |
| `exp1_claude_models.py` | EN and RU on 10 Claude models: where the tokenizer changes | `results/exp1_claude_models.json` |
| `extract_prompts.py` | Russian prompts from Claude Code history | `private/prompts.jsonl` |
| `find_real_typos.py` | Real typos in the prompts | `private/real_typos.csv`, `results/exp2_real_typos_stats.json` |
| `exp2_typos.py [--claude]` | Cost of a typo: real ones, synthetic 2/5/10%, wrong keyboard layout | `results/exp2_typos.json`, `exp2_pieces_examples.json` |
| `exp3_answers.py [--limit N]` | Answer tokens of Claude Opus 5.5 on 20 tasks (`exp3_tasks.json`) in Russian and English. Paid, capped at $4.80 | `results/exp3_answers.json` |
| `BLOG_DIR=… export_web_data.py` | Builds the chart data for the article from `results/` | `src/data/tokens.json` in the blog repository |

## Method and caveats

- **Premium**: tokens of a text in language X divided by tokens of the same text in English. Term and approach: Petrov et al., 2023, [arXiv:2305.15425](https://arxiv.org/abs/2305.15425).
- **OpenAI models and vocabularies** follow `tiktoken/model.py`: davinci → r50k, gpt-4 and gpt-3.5-turbo → cl100k, gpt-4o, gpt-4.1, o1, o3, gpt-5 → o200k.
- **Llama 3 and Gemma 3** are gated on Hugging Face. The tokenizer comes from the open copies `unsloth/Llama-3.2-1B-Instruct` and `unsloth/gemma-3-4b-it`.
- **Claude**: `count_tokens` adds service tokens of the message wrapper. I subtract a baseline: the count for "a" minus 1.
- **Real typos**: the search is strict. The word is not in the pymorphy3 dictionary, one edit turns it into a word the author uses often, jargon is on a stop list. 14 finds in 905 prompts are a lower bound on typo frequency, not the frequency itself.
- **Synthetic typos**: one edit in a word of 3+ letters. Kinds: neighbour key, omission, repetition, transposition, extra neighbour key. Weights are real typo frequencies +1. Three random seeds. In `results/` the kinds keep their Russian keys: `сосед`, `пропуск`, `повтор`, `перестановка`, `вставка`.
- Chart years are the year of the first model with that vocabulary.

---

# Замеры для статьи «Правда ли, что русский текст дороже английского?»

Серия «Как модель устроена внутри», часть 1. Все цифры статьи — отсюда.

## Подготовка

```bash
uv venv .venv && uv pip install --python .venv/bin/python tiktoken tokenizers sentencepiece huggingface_hub anthropic pymorphy3 pymorphy3-dicts-ru
.venv/bin/python fetch_tokenizers.py   # tokenizer.json открытых моделей → data/hf/
```

- FLORES-200: `curl -L https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz | tar -xz -C data/flores`. Лицензия CC BY-SA 4.0.
- Claude: `ant auth login` (ключ не нужен). `count_tokens` бесплатный, лимит от 5 000 запросов в минуту. Источник: `sources/claude-token-counting.md`.

- Статьи блога в репозиторий не входят. Укажите папку со статьями в `BLOG_DIR`, иначе `exp1_language_tax.py` посчитает только FLORES.

`data/` и `private/` не коммитятся.

## Скрипты

| Скрипт | Что делает | Результат |
| --- | --- | --- |
| `exp1_language_tax.py [--claude]` | Премия к английскому для 20 языков FLORES и статей блога | `results/exp1_flores.csv`, `exp1_blog.csv`, `exp1_summary.json` |
| `exp1_claude_models.py` | EN и RU на 10 моделях Claude: где меняется токенизатор | `results/exp1_claude_models.json` |
| `extract_prompts.py` | Русские промпты из истории Claude Code | `private/prompts.jsonl` |
| `find_real_typos.py` | Настоящие опечатки в промптах | `private/real_typos.csv`, `results/exp2_real_typos_stats.json` |
| `exp2_typos.py [--claude]` | Цена опечатки: настоящие, искусственные 2/5/10%, не та раскладка | `results/exp2_typos.json`, `exp2_pieces_examples.json` |
| `exp3_answers.py [--limit N]` | Токены ответа Claude Opus 5.5 на 20 задач (`exp3_tasks.json`) на русском и английском. Платный, лимит $4,8 | `results/exp3_answers.json` |
| `BLOG_DIR=… export_web_data.py` | Собирает данные для графиков статьи из `results/` | `src/data/tokens.json` в репозитории блога |

## Метод и оговорки

- **Премия** — токены текста на языке X, делённые на токены того же текста на английском. Термин и подход: Petrov et al., 2023, [arXiv:2305.15425](https://arxiv.org/abs/2305.15425).
- **Модели OpenAI и словари** — по `tiktoken/model.py`: davinci → r50k, gpt-4 и gpt-3.5-turbo → cl100k, gpt-4o, gpt-4.1, o1, o3, gpt-5 → o200k.
- **Llama 3 и Gemma 3** закрыты на Hugging Face. Токенизатор взят из открытых копий `unsloth/Llama-3.2-1B-Instruct` и `unsloth/gemma-3-4b-it`.
- **Claude**: `count_tokens` добавляет служебные токены обёртки. Вычитаю базу: счёт для «a» минус 1.
- **Настоящие опечатки**: поиск строгий. Слово не в словаре pymorphy3, исправляется одной правкой в частое слово автора, жаргон в стоп-листе. 14 находок на 905 промптов — это нижняя граница частоты опечаток, а не сама частота.
- **Искусственные опечатки**: одна правка в слове из 3+ букв. Типы: соседняя клавиша, пропуск, повтор, перестановка, лишняя соседняя клавиша. Веса — частоты настоящих опечаток +1. Три случайных зерна.
- Годы на графиках — год первой модели с этим словарём.
