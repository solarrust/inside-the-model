# Как модель устроена внутри

Скрипты и результаты замеров для серии статей в блоге [blog.alena.rocks](https://blog.alena.rocks). Каждая папка — одна статья. Цифры в статьях посчитаны этими скриптами: их можно перепроверить.

| Папка | Статья |
| --- | --- |
| [`token-tax`](token-tax) | Правда ли, что русский текст дороже английского? Налог на язык в токенах и цена опечаток. |

Личные данные автора (промпты, история разговоров) в репозиторий не входят. Скрипты, которые с ними работают, читают их из локальной папки `private/`.

---

# How a model works inside

Scripts and measurements behind a blog series on [blog.alena.rocks](https://blog.alena.rocks). One folder per article. Every number in the articles comes from these scripts, so you can re-run them. Comments and READMEs are in Russian.

## License

Code — MIT. Results in `*/results/` are derived from [FLORES-200](https://github.com/openlanguagedata/flores) (CC BY-SA 4.0) and keep that license.
