"""Downloads only tokenizer.json of open models from Hugging Face into data/hf/."""
from huggingface_hub import hf_hub_download

REPOS = [
    "openai-community/gpt2",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen3-8B",
    "deepseek-ai/DeepSeek-V3",
    "mistralai/Mistral-Nemo-Instruct-2407",
    # The original Llama 3 and Gemma 3 repos are gated; the open unsloth copies have the same tokenizer
    "unsloth/Llama-3.2-1B-Instruct",
    "unsloth/gemma-3-4b-it",
    "ai-sage/GigaChat-20B-A3B-instruct",
]
for repo in REPOS:
    try:
        p = hf_hub_download(repo, "tokenizer.json", local_dir=f"data/hf/{repo.replace('/', '__')}")
        print("ok  ", repo)
    except Exception as e:
        print("FAIL", repo, type(e).__name__)

# YandexGPT ships a SentencePiece model instead of tokenizer.json
hf_hub_download("yandex/YandexGPT-5-Lite-8B-pretrain", "tokenizer.model", local_dir="data/hf/yandex__YandexGPT-5-Lite-8B-pretrain")
print("ok   yandex/YandexGPT-5-Lite-8B-pretrain")
