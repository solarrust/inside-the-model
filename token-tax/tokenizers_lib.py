"""One interface to tokenizers: tiktoken, Hugging Face tokenizers, SentencePiece, Claude count_tokens.

Each tokenizer is a count(text) -> int function plus metadata: model, year, vocabulary size.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

HERE = Path(__file__).parent
HF = HERE / "data" / "hf"


@dataclass
class Tok:
    key: str
    label: str  # chart label
    family: str  # openai | open | ru | claude
    year: int  # release year of the first model with this tokenizer
    count: Callable[[str], int]
    vocab: int | None = None
    encode_pieces: Callable[[str], list[str]] | None = field(default=None, repr=False)


def _tiktoken(name: str, label: str, year: int) -> Tok:
    import tiktoken

    enc = tiktoken.get_encoding(name)

    def pieces(t: str) -> list[str]:
        return [enc.decode_single_token_bytes(i).decode("utf-8", "replace") for i in enc.encode(t)]

    return Tok(name, label, "openai", year, lambda t: len(enc.encode(t, disallowed_special=())), enc.n_vocab, pieces)


def _hf(repo_dir: str, key: str, label: str, family: str, year: int) -> Tok:
    from tokenizers import Tokenizer

    tk = Tokenizer.from_file(str(HF / repo_dir / "tokenizer.json"))

    def pieces(t: str) -> list[str]:
        enc = tk.encode(t, add_special_tokens=False)
        return [t[a:b] for a, b in enc.offsets]

    return Tok(
        key, label, family, year,
        lambda t: len(tk.encode(t, add_special_tokens=False).ids),
        tk.get_vocab_size(), pieces,
    )


def _spm(repo_dir: str, key: str, label: str, family: str, year: int) -> Tok:
    import sentencepiece as spm

    sp = spm.SentencePieceProcessor(model_file=str(HF / repo_dir / "tokenizer.model"))
    return Tok(
        key, label, family, year,
        lambda t: len(sp.encode(t)), sp.vocab_size(),
        lambda t: sp.encode(t, out_type=str),
    )


def _claude(model: str, key: str, label: str, year: int) -> Tok:
    """count_tokens is free (docs: build-with-claude/token-counting, saved in sources/).

    The count includes service tokens of the message wrapper. We subtract a baseline: the count
    for the text "a" minus 1 token for "a" itself. On long texts the correction barely affects ratios.
    """
    import anthropic

    client = anthropic.Anthropic()
    cache: dict[str, int] = {}

    def raw(t: str) -> int:
        if t not in cache:
            r = client.messages.count_tokens(model=model, messages=[{"role": "user", "content": t}])
            cache[t] = r.input_tokens
        return cache[t]

    base = raw("a") - 1
    return Tok(key, label, "claude", year, lambda t: raw(t) - base, None)


_LOCAL = [
    lambda: _tiktoken("o200k_base", "GPT-4o (o200k)", 2024),
    lambda: _tiktoken("cl100k_base", "GPT-4 (cl100k)", 2023),
    lambda: _spm("yandex__YandexGPT-5-Lite-8B-pretrain", "yandexgpt5", "YandexGPT 5", "ru", 2025),
]


def all_local() -> list[Tok]:
    """Tokenizers that work offline. Year is that of the first model with this vocabulary."""
    toks = [
        # tiktoken/model.py: text-davinci-001/davinci → r50k_base; gpt-4/gpt-3.5-turbo → cl100k_base; gpt-4o → o200k_base
        _tiktoken("r50k_base", "GPT-3 (r50k)", 2020),
        _tiktoken("cl100k_base", "GPT-4 (cl100k)", 2023),
        _tiktoken("o200k_base", "GPT-4o (o200k)", 2024),
        # The original Llama and Gemma repos are gated on HF; we take the tokenizer from open unsloth copies
        _hf("unsloth__Llama-3.2-1B-Instruct", "llama3", "Llama 3", "open", 2024),
        _hf("unsloth__gemma-3-4b-it", "gemma3", "Gemma 3", "open", 2025),
        _hf("Qwen__Qwen2.5-7B-Instruct", "qwen25", "Qwen 2.5", "open", 2024),
        _hf("Qwen__Qwen3-8B", "qwen3", "Qwen 3", "open", 2025),
        _hf("deepseek-ai__DeepSeek-V3", "deepseek3", "DeepSeek V3", "open", 2024),
        _hf("mistralai__Mistral-Nemo-Instruct-2407", "nemo", "Mistral Nemo", "open", 2024),
        _hf("ai-sage__GigaChat-20B-A3B-instruct", "gigachat", "GigaChat", "ru", 2024),
        _spm("yandex__YandexGPT-5-Lite-8B-pretrain", "yandexgpt5", "YandexGPT 5", "ru", 2025),
    ]
    return toks


def available() -> list[Tok]:
    """Only the tokenizers whose files are downloaded (cleanup may have removed part of data/hf)."""
    out = []
    for make in _LOCAL:
        try:
            out.append(make())
        except Exception:
            pass
    return out


def claude() -> list[Tok]:
    # The SDK finds credentials itself: ANTHROPIC_API_KEY or the profile from `ant auth login`.
    # docs token-counting: «Claude 4.7 and later models … use a newer tokenizer»
    return [
        _claude("claude-sonnet-4-6", "claude_old", "Claude до 4.7", 2024),
        _claude("claude-opus-5-5", "claude_new", "Claude 4.7+", 2026),
    ]
