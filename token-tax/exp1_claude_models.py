"""Check: do Claude models with the same tokenizer generation give the same count? FLORES devtest, en and ru."""
import json, anthropic
from pathlib import Path
F = Path("data/flores/flores200_dataset/devtest")
c = anthropic.Anthropic()
MODELS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6", "claude-opus-4-7", "claude-opus-4-8",
          "claude-sonnet-5", "claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5", "claude-fable-5-2"]
res = {}
for m in MODELS:
    try:
        base = c.messages.count_tokens(model=m, messages=[{"role": "user", "content": "a"}]).input_tokens - 1
        res[m] = {l: c.messages.count_tokens(model=m, messages=[{"role": "user", "content": (F / f"{l}.devtest").read_text()}]).input_tokens - base
                  for l in ["eng_Latn", "rus_Cyrl"]}
        r = res[m]; print(f"{m:20} en={r['eng_Latn']:6} ru={r['rus_Cyrl']:6} premium={r['rus_Cyrl']/r['eng_Latn']:.2f}")
    except Exception as e:
        print(f"{m:20} {type(e).__name__}: {str(e)[:80]}")
Path("results/exp1_claude_models.json").write_text(json.dumps(res, indent=1))
