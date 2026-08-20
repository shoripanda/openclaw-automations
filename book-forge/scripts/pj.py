#!/usr/bin/env python3
# book-forge 状態管理CLI — project.json を確実に読み書きする。
# 全フェーズ(0-7)の土台。Claude Code/OpenClaw(bash)でもChatGPT(python)でも同じに動く。
#
# 使い方:
#   pj.py init <dir> [--種類 ..] [--タイトル ..] ...   プロジェクト作成(project.json)
#   pj.py show <dir|json>                              整形表示
#   pj.py get <dir|json> <dotted.key>                  値取得 (例: meta.種類)
#   pj.py set <dir|json> <dotted.key> <value>          値設定 (JSONとして解釈可)
#   pj.py add-research <dir|json> --出典 .. --url .. --要点 .. [--裏取り true] [--参照日 ..]
#   pj.py add-interview <dir|json> --q .. --a .. [--phase ..]
#   pj.py set-outline <dir|json> <json配列>             目次を丸ごと設定
#   pj.py approve <dir|json>                            目次を承認(approved=true, state=drafting)
#   pj.py state <dir|json> [new_state]                 状態の取得/設定
#   pj.py check <dir|json> <phase>                     ゲート判定 (intake/research/interview/outline)
import sys, os, json, argparse

STATES = ["intake","research","interview","outline","drafting","revision","layout","export"]

def skeleton():
    return {
        "meta": {"種類":"", "タイトル":"", "読者":"", "狙い":"", "言語":"ja",
                 "トーン":"", "体裁":"", "判型":"", "目標文字数":0, "締切":""},
        "research": [], "interview": [], "outline": [],
        "manuscript": {"章": []}, "assets": [],
        "layout": {"フォント":"Hiragino Mincho ProN", "サイズ":"11pt",
                   "判型":"", "余白":"", "目次": True},
        "approved": False, "state": "intake",
    }

def path_of(p):
    return os.path.join(p, "project.json") if os.path.isdir(p) else p

def load(p):
    with open(path_of(p), encoding="utf-8") as f: return json.load(f)

def save(p, d):
    with open(path_of(p), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def dset(d, dotted, val):
    ks = dotted.split("."); cur = d
    for k in ks[:-1]: cur = cur.setdefault(k, {})
    try: val = json.loads(val)
    except Exception: pass
    cur[ks[-1]] = val

def dget(d, dotted):
    cur = d
    for k in dotted.split("."): cur = cur[k]
    return cur

REQUIRED_META = ["種類","読者","狙い","体裁","判型","目標文字数"]

def check(d, phase):
    miss = []
    if phase == "intake":
        for k in REQUIRED_META:
            v = d["meta"].get(k)
            if v in (None, "", 0): miss.append("meta."+k)
    elif phase == "research":
        light = any(x in (d["meta"].get("種類","")+d["meta"].get("体裁","")) for x in ["エッセイ","自伝","小説","詩"])
        n = len(d["research"])
        if n == 0 and not light: miss.append("research(>=1件・裏取り済み)")
        if any(not r.get("url") for r in d["research"]): miss.append("research: URL未記載あり")
    elif phase == "interview":
        if len(d["interview"]) == 0: miss.append("interview(>=1件)")
    elif phase == "outline":
        if len(d["outline"]) == 0: miss.append("outline(章立て)")
        if not d.get("approved"): miss.append("approved(著者承認)")
    else:
        print("unknown phase:", phase); return 2
    if miss:
        print("NG:", ", ".join(miss)); return 1
    print("OK:", phase, "ゲート通過"); return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("dir")
    for k in ["種類","タイトル","読者","狙い","トーン","体裁","判型","目標文字数","締切"]:
        p.add_argument("--"+k)
    for name in ["show","state"]:
        q = sub.add_parser(name); q.add_argument("pj");
    sub._name_parser_map["state"].add_argument("new", nargs="?")
    g = sub.add_parser("get"); g.add_argument("pj"); g.add_argument("key")
    s = sub.add_parser("set"); s.add_argument("pj"); s.add_argument("key"); s.add_argument("value")
    r = sub.add_parser("add-research"); r.add_argument("pj")
    for k in ["出典","url","要点","裏取り","参照日"]: r.add_argument("--"+k, default="")
    iv = sub.add_parser("add-interview"); iv.add_argument("pj")
    iv.add_argument("--q", required=True); iv.add_argument("--a", default=""); iv.add_argument("--phase", default="interview")
    so = sub.add_parser("set-outline"); so.add_argument("pj"); so.add_argument("json")
    av = sub.add_parser("approve"); av.add_argument("pj")
    ck = sub.add_parser("check"); ck.add_argument("pj"); ck.add_argument("phase")
    a = ap.parse_args()

    if a.cmd == "init":
        os.makedirs(a.dir, exist_ok=True)
        d = skeleton()
        for k in ["種類","タイトル","読者","狙い","トーン","体裁","判型","締切"]:
            v = getattr(a, k, None)
            if v: d["meta"][k] = v
        if getattr(a,"目標文字数",None):
            try: d["meta"]["目標文字数"] = int(a.目標文字数)
            except: pass
        save(a.dir, d); print("created", path_of(a.dir)); return
    d = load(a.pj)
    if a.cmd == "show": print(json.dumps(d, ensure_ascii=False, indent=2))
    elif a.cmd == "get": print(dget(d, a.key))
    elif a.cmd == "set": dset(d, a.key, a.value); save(a.pj, d); print("set", a.key)
    elif a.cmd == "state":
        if a.new:
            if a.new not in STATES: print("invalid state"); sys.exit(1)
            d["state"]=a.new; save(a.pj,d); print("state=",a.new)
        else: print(d["state"])
    elif a.cmd == "add-research":
        d["research"].append({"出典":a.出典,"url":a.url,"要点":a.要点,
                              "裏取り": a.裏取り in ("true","True","1","はい"),"参照日":a.参照日})
        save(a.pj,d); print("research +1 (計%d)"%len(d["research"]))
    elif a.cmd == "add-interview":
        d["interview"].append({"q":a.q,"a":a.a,"phase":a.phase}); save(a.pj,d)
        print("interview +1 (計%d)"%len(d["interview"]))
    elif a.cmd == "set-outline":
        d["outline"]=json.loads(a.json); save(a.pj,d); print("outline set (%d章)"%len(d["outline"]))
    elif a.cmd == "approve":
        d["approved"]=True; d["state"]="drafting"; save(a.pj,d); print("approved → state=drafting")
    elif a.cmd == "check":
        sys.exit(check(d, a.phase))

if __name__ == "__main__":
    main()
