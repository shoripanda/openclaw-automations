#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
digest.py — OpenClaw非依存の「AIツール定期ダイジェスト」bot
  取得(curl相当) → 新着判定(seen.json) → ローカルLLM(LM Studio)で要約 → 配信(Telegram/Zennスクラップ)
使い方:
  python3 digest.py --dry-run   # 取得と新着判定だけ表示（LLM/配信なし・安全）
  python3 digest.py --no-post   # LLM要約まで（配信しない・印字のみ）
  python3 digest.py             # 本番（新着があれば要約して配信）
"""
import json, os, sys, subprocess, urllib.request, urllib.error
import re
import xml.etree.ElementTree as ET

HOME = os.path.expanduser("~")
BASE = os.path.join(HOME, "digest-bot")
SEEN_PATH = os.path.join(BASE, "seen.json")
LATEST_MD = os.path.join(BASE, "digest-latest.md")
LMS_URL   = "http://localhost:1234/v1"
TG_TOKEN_FILE = os.environ.get("TG_TOKEN_FILE", os.path.join(HOME, ".config", "digest-bot", "tg_token"))
TG_CHAT   = os.environ.get("TG_CHAT", "REPLACE_WITH_YOUR_CHAT_ID")
ZENN_HELPER = os.environ.get("DIGEST_ZENN_HELPER", "")  # optional; leave empty to skip Zenn
UA = "Mozilla/5.0 (digest-bot)"

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def _strip_html(h):
    t = re.sub(r"<[^>]+>", " ", h or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def src_atom(url, label, maxn=6, bodylen=600):
    out = []
    try:
        root = ET.fromstring(fetch(url))
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for e in root.findall(".//a:entry", ns)[:maxn]:
            title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
            link_el = e.find("a:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            eid = (e.findtext("a:id", default=link, namespaces=ns) or link)
            body = _strip_html(e.findtext("a:content", default="", namespaces=ns))[:bodylen]
            out.append({"src": label, "id": eid, "title": title, "url": link, "body": body})
    except Exception as ex:
        print("[warn] %s: %s" % (label, ex), file=sys.stderr)
    return out

def src_hf(maxn=12):
    out = []
    try:
        d = json.loads(fetch("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=%d" % maxn))
        for m in d:
            mid = m.get("modelId") or m.get("id") or ""
            if not mid:
                continue
            out.append({"src": "HuggingFace trending", "id": "hf:" + mid,
                        "title": mid, "url": "https://huggingface.co/" + mid,
                        "likes": m.get("likes"), "downloads": m.get("downloads")})
    except Exception as ex:
        print("[warn] HF: %s" % ex, file=sys.stderr)
    return out

def collect():
    items = []
    items += src_atom("https://github.com/openai/codex/releases.atom", "Codex (OpenAI)")
    items += src_atom("https://github.com/anthropics/claude-code/releases.atom", "Claude Code (Anthropic)")
    items += src_hf()
    return items

def load_seen():
    try:
        return set(json.load(open(SEEN_PATH)))
    except Exception:
        return set()

def save_seen(seen):
    json.dump(sorted(seen), open(SEEN_PATH, "w"), ensure_ascii=False, indent=0)

def lms_model():
    d = json.loads(fetch(LMS_URL + "/models", timeout=6))
    return d["data"][0]["id"]


HORDE = os.environ.get("DIGEST_HORDE_CMD", os.path.join(HOME, ".openclaw", "horde.sh"))  # optional external LLM helper

def brain(items, maxn=12):
    items = items[:maxn]
    def _one(i):
        b = (" — " + i["body"]) if i.get("body") else ""
        return "- [%s] %s%s (%s)" % (i["src"], i["title"], b, i.get("url",""))
    lines = [_one(i) for i in items]
    prompt = ("あなたは開発者向けAIツールニュースの編集者です。"
              "以下は前回以降の新着一覧です。開発者にとって意味のあるものだけを選び、"
              "日本語のです・ます調で簡潔なダイジェストにしてください。"
              "各項目は1〜2文（何が変わったか＋意味）＋末尾に出典URL。冒頭に1行サマリー。\n\n"
              "新着一覧:\n" + "\n".join(lines))
    r = subprocess.run([HORDE, prompt, "512"], capture_output=True, text=True, timeout=900)
    out = r.stdout or ""
    out = re.split(r"\n-{3,}\n\[model:", out)[0].strip()
    return out or "[生成に失敗しました]"

def llm(items, model):
    lines = ["- [%s] %s (%s)" % (i["src"], i["title"], i["url"]) for i in items]
    sys_p = ("あなたは開発者向けのAIツール・ニュースをまとめる編集者です。"
             "以下は前回以降の『新着』一覧です。この中で開発者にとって意味のある変化だけを選び、"
             "日本語の『です・ます調』で簡潔なダイジェストにしてください。"
             "各項目は見出し＋2〜3文（何が変わったか＋開発者にとっての意味）＋末尾に出典URL。"
             "重要でないものは省略。冒頭に1行サマリー。時点の前置きは書かない。")
    usr_p = "新着一覧:\n" + "\n".join(lines)
    body = json.dumps({"model": model,
                       "messages": [{"role": "system", "content": sys_p},
                                    {"role": "user", "content": usr_p},
                                    {"role": "assistant", "content": "<think></think>"}],
                       "temperature": 0.4, "max_tokens": 1400}).encode()
    req = urllib.request.Request(LMS_URL + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        d = json.loads(r.read())
    txt = d["choices"][0]["message"]["content"]
    return txt.replace("<think></think>", "").strip()

def tg_send(text):
    tok = os.environ.get("TG_BOT_TOKEN") or open(TG_TOKEN_FILE).read().strip()
    for i in range(0, len(text), 3800):
        chunk = text[i:i+3800]
        data = urllib.parse.urlencode({"chat_id": TG_CHAT, "text": chunk,
                                       "disable_web_page_preview": "true"}).encode()
        urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % tok, data=data, timeout=20).read()

def zenn_append(text):
    if not ZENN_HELPER:
        raise RuntimeError("ZENN_HELPER not set; skipping")
    open(LATEST_MD, "w").write(text)
    r = subprocess.run([ZENN_HELPER, LATEST_MD], capture_output=True, text=True, timeout=180)
    return (r.stdout or "").strip() + (" " + r.stderr.strip() if r.returncode else "")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    items = collect()
    seen = load_seen()
    new = [i for i in items if i["id"] not in seen]
    print("[info] collected=%d  new=%d" % (len(items), len(new)), file=sys.stderr)
    if mode == "--dry-run":
        for i in new:
            print("NEW  [%s] %s" % (i["src"], i["title"]))
        return
    if not new:
        print("[info] 新着なし。何もしません。", file=sys.stderr)
        return
    digest = brain(new)
    print(digest)
    if mode == "--no-post":
        return
    # 配信（Telegramは必須・Zennはベストエフォート）
    tg_send(digest)
    try:
        z = zenn_append("## 自動ダイジェスト\n\n" + digest)
        print("[zenn] %s" % z, file=sys.stderr)
    except Exception as ex:
        print("[warn] zenn append skipped: %s" % ex, file=sys.stderr)
    # 新着を既読化（配信できたので記録）
    for i in new:
        seen.add(i["id"])
    save_seen(seen)
    print("[info] done. seen=%d" % len(seen), file=sys.stderr)

import urllib.parse
if __name__ == "__main__":
    main()
