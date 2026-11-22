"""Collects user messages from Claude Code history into private/prompts.jsonl (not committed)."""
import json, glob, os, re
out, seen = [], set()
for path in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    for line in open(path, encoding="utf-8", errors="replace"):
        try: d = json.loads(line)
        except Exception: continue
        if d.get("type") != "user" or d.get("isMeta"): continue
        c = d.get("message", {}).get("content")
        if isinstance(c, list):
            c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
        if not isinstance(c, str): continue
        t = c.strip()
        # skip service text: commands, system inserts, tool output, pasted text
        if not t or t.startswith(("<", "[Request interrupted", "Caveat:")) or "<command-" in t or "tool_use_id" in t: continue
        if not re.search(r"[а-яё]", t, re.I) or len(t) < 15: continue
        if t in seen: continue
        seen.add(t)
        out.append({"project": os.path.basename(os.path.dirname(path)), "ts": d.get("timestamp"), "text": t})
with open("private/prompts.jsonl", "w", encoding="utf-8") as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
lens = sorted(len(r["text"]) for r in out)
print(len(out), "prompts; length: median", lens[len(lens)//2], "max", lens[-1])
