# generate.py 抜粋 — reposapo-3themes automation で追加した実装
# 実体: ~/xpost-bot/generate.py （このファイルは記録用の抜粋）
# 導入日: 2026-09-01

def hf_uncensored(n=12, min_likes=30):
    # 無検閲LLM（uncensored / abliterated）で“いま話題”のモデルをHFから拾う。
    # 新着ゴミ（likes/dl=0の個人再配布）を避けるため trendingScore 順＋likes下限で選別。
    seen_ids=set(); out=[]
    for kw in ("uncensored","abliterated"):
        try:
            url=(f"https://huggingface.co/api/models?search={kw}"
                 f"&sort=trendingScore&direction=-1&limit={n}")
            req=urllib.request.Request(url, headers={"User-Agent":UA})
            arr=json.load(urllib.request.urlopen(req,timeout=40))
        except Exception as ex:
            print("hf uncensored err",kw,ex); continue
        for m in arr:
            mid=m.get("id") or m.get("modelId")
            if not mid or mid in seen_ids: continue
            if (m.get("likes",0) or 0) < min_likes: continue
            seen_ids.add(mid)
            out.append({"id":mid,"url":f"https://huggingface.co/{mid}",
                        "pipeline":m.get("pipeline_tag",""),"likes":m.get("likes",0),
                        "downloads":m.get("downloads",0),"kw":kw})
    out.sort(key=lambda x:(x["likes"] or 0), reverse=True)
    return out

def summarize_uncensored(item, use_opus=False):
    readme=_readme(item["id"])
    facts=(f"モデル: {item['id']} / 種別: 無検閲LLM({item['kw']}) / タスク: {item['pipeline']} "
           f"/ likes:{item['likes']} / DL:{item['downloads']}")
    p=(STYLE+"\n\n次は『いま話題の“無検閲(uncensored/abliterated)”ローカルLLM』。"
       "検閲・拒否応答を外したオープンウェイトのモデルで、ローカル実行・研究用途で注目されている点を、"
       "煽らず中立に、読む人が「何のモデルで何が特徴か」分かるXポストに。"
       f"事実(下記facts)とREADME由来のみ・誇張/捏造禁止・本文{CFG['max_body_chars']}字以内・最後の行にURL・#ローカルLLMや#生成AI等のタグ2個。"+GUARD+"\n\n"
       f"URL: {item['url']}\nfacts: {facts}\nREADME抜粋:\n{readme}")
    if use_opus:
        try:
            r=subprocess.run(["claude","-p",p,"--model","claude-opus-4-8"],capture_output=True,text=True,timeout=180,stdin=subprocess.DEVNULL)
            t=(r.stdout or "").strip()
            if t: return t
        except Exception as e: print("opus unc err",e)
    t=_fcc(p)
    if t and wx(t)>280:
        t2=_fcc(p+"\n\n※長すぎます。本文を日本語70字以内に短縮し、URLとハッシュタグは残す。")
        if t2 and wx(t2)<=280: t=t2
    return t

def collect_topics():
    # 依頼テーマ3種を各回きっちり拾う: Claude Code / Codex / 無検閲LLM
    # 各ソースから“seen未収録の最新1件”を選び、[(kind, item)] で返す。
    picks=[]
    news=collect_news()  # Claude Code + Codex（GitHub releases）
    for label in ("Claude Code","Codex"):
        for it in news:
            if it["src"]==label and ("news:"+it["id"]) not in seen:
                picks.append(("news",it)); break
    for it in hf_uncensored():
        if ("hfunc:"+it["id"]) not in seen:
            picks.append(("uncensored",it)); break
    return picks

def main():
    made=0; want=CFG["posts_per_run"]
    # --- 依頼テーマ3種（Claude Code / Codex / 無検閲LLM）を最優先で確保 ---
    tmade=0
    for kind,it in collect_topics():
        use_opus=(tmade % 3 == 2)
        try:
            if kind=="news":
                text=clean(summarize_news(it, use_opus))
                key="news:"+it["id"]; theme=it["src"]; url=it["url"]; title=it["title"]; src="news"
            else:
                text=clean(summarize_uncensored(it, use_opus))
                key="hfunc:"+it["id"]; theme="無検閲LLM"; url=it["url"]; title=it["id"]; src="uncensored"
        except Exception as ex: print("topic sum err",ex); continue
        if not text or key in seen: continue
        queue.append({"account":CFG["account"],"theme":theme,"paper_url":url,
                      "title":title,"text":text,"status":"pending","source":src,
                      "model":("opus" if use_opus else "free"),"made_at":int(time.time())})
        seen.add(key); tmade+=1
        print(f"[topic {tmade}] {theme} :: {title[:50]}")
    for theme in CFG["themes"]:
        if made>=want: break
        try: papers=arxiv(theme)
        except Exception as ex: print("arxiv err",theme,ex); continue
        for p in papers:
            if made>=want: break
            if p["id"] in seen: continue
            use_opus = (made % 4 == 3)  # 4本に1本はOpus
