# Claude: token counting

Source: https://platform.claude.com/docs/en/build-with-claude/token-counting (read 2026-11-22). Русская версия ниже.

- The `POST /v1/messages/count_tokens` endpoint is free. The limit is requests per minute by account tier: 5,000 (Start), 10,000 (Build), 20,000 (Scale).
- Counting and generation limits are independent.
- The count is an estimate: the real number of input tokens may differ slightly. The count includes service tokens, which are not billed.
- All active models support counting. Claude 4.7 brought a new tokenizer: the same text gives about 30% more tokens, the exact difference depends on the text.

Prices (claude-api skill, as of 2026-11-03): Opus 4.6 costs $5 per 1M input tokens, Opus 5.5 costs $4.

More from the claude-api skill (2026-11-22): Opus 5.5 costs $4 input and $20 output per 1M tokens, 1M-token context. Opus 5 costs $5/$25 and already uses the new tokenizer, so Opus 5.5 lowered the price, not the tokenizer change.

Thinking (claude-api skill, 2026-11-22): Opus 5.5 always has adaptive thinking on, `thinking.display` defaults to `omitted`. The API does not return the thinking text, but thinking tokens are part of `usage.output_tokens` and billed as output.

---

# Claude: подсчёт токенов

Источник: https://platform.claude.com/docs/en/build-with-claude/token-counting (прочитано 2026-11-22).

- Эндпоинт `POST /v1/messages/count_tokens` бесплатный. Лимит — запросы в минуту по уровню аккаунта: 5 000 (Start), 10 000 (Build), 20 000 (Scale).
- Лимиты подсчёта и генерации независимы.
- Счёт — оценка: реальное число входных токенов может немного отличаться. В счёт входят служебные токены, за них не платят.
- Все активные модели поддерживают подсчёт. С Claude 4.7 новый токенизатор: тот же текст даёт примерно на 30% больше токенов, точная разница зависит от текста.

Цены (claude-api skill, данные на 2026-11-03): Opus 4.6 — $5 за 1 млн входных токенов, Opus 5.5 — $4.

Ещё из claude-api skill (2026-11-22): Opus 5.5 — $4 за вход и $20 за выход за 1 млн токенов, контекст 1 млн токенов. Opus 5 стоит $5/$25 и уже на новом токенизаторе, так что цену снизил Opus 5.5, а не смена токенизатора.

Размышление (claude-api skill, 2026-11-22): у Opus 5.5 адаптивное размышление включено всегда, `thinking.display` по умолчанию `omitted` — текст размышления API не возвращает, но токены размышления входят в `usage.output_tokens` и оплачиваются как выход.
