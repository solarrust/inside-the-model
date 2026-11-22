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

## Метод и оговорки

- **Премия** — токены текста на языке X, делённые на токены того же текста на английском. Термин и подход: Petrov et al., 2023, [arXiv:2305.15425](https://arxiv.org/abs/2305.15425).
- **Модели OpenAI и словари** — по `tiktoken/model.py`: davinci → r50k, gpt-4 и gpt-3.5-turbo → cl100k, gpt-4o, gpt-4.1, o1, o3, gpt-5 → o200k.
- **Llama 3 и Gemma 3** закрыты на Hugging Face. Токенизатор взят из открытых копий `unsloth/Llama-3.2-1B-Instruct` и `unsloth/gemma-3-4b-it`.
- **Claude**: `count_tokens` добавляет служебные токены обёртки. Вычитаю базу: счёт для «a» минус 1.
- **Настоящие опечатки**: поиск строгий. Слово не в словаре pymorphy3, исправляется одной правкой в частое слово автора, жаргон в стоп-листе. 14 находок на 905 промптов — это нижняя граница частоты опечаток, а не сама частота.
- **Искусственные опечатки**: одна правка в слове из 3+ букв. Типы: соседняя клавиша, пропуск, повтор, перестановка, лишняя соседняя клавиша. Веса — частоты настоящих опечаток +1. Три случайных зерна.
- Годы на графиках — год первой модели с этим словарём.
