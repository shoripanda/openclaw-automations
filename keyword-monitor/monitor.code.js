// キーワード監視: GitHub / Hacker News / Hugging Face の新着を拾い、初回はseedのみ、以降は新規だけTelegram通知
const staticData = $getWorkflowStaticData('global');
const seen = staticData.seen || {};
const firstRun = !staticData.seeded;
const KW = ["abliterated","uncensored LLM","Claude Code","Codex","coding agent","LLM agent","MCP","GLM"];
const TOKEN = process.env.TG_BOT_TOKEN;
const CHAT = process.env.TG_CHAT_ID;
const out = [];
const mark = (id) => { if (seen[id]) return false; seen[id] = Date.now(); return true; };

// GitHub（新規＆高スター）
for (const kw of KW) {
  const q = encodeURIComponent(`${kw} in:name,description,readme stars:>30`);
  try {
    const res = await this.helpers.httpRequest({ url: `https://api.github.com/search/repositories?q=${q}&sort=updated&order=desc&per_page=5`, json: true, headers: { 'User-Agent': 'n8n-keyword-monitor', 'Accept': 'application/vnd.github+json' } });
    for (const r of (res.items || [])) if (mark('gh:' + r.id) && !firstRun) out.push(`⭐${r.stargazers_count} [GitHub] ${r.full_name}\n${(r.description || '').slice(0,120)}\n${r.html_url}`);
  } catch (e) {}
}
// Hacker News（Algolia）
for (const kw of KW) {
  try {
    const res = await this.helpers.httpRequest({ url: `https://hn.algolia.com/api/v1/search_by_date?query=${encodeURIComponent(kw)}&tags=story&numericFilters=points%3E20`, json: true });
    for (const h of (res.hits || []).slice(0,3)) if (mark('hn:' + h.objectID) && !firstRun) out.push(`🟠[HN ${h.points||0}pt] ${h.title}\n${h.url || 'https://news.ycombinator.com/item?id=' + h.objectID}`);
  } catch (e) {}
}
// Hugging Face（新着モデル）
for (const kw of KW) {
  try {
    const res = await this.helpers.httpRequest({ url: `https://huggingface.co/api/models?search=${encodeURIComponent(kw)}&sort=createdAt&direction=-1&limit=5`, json: true });
    for (const m of (res || [])) if (mark('hf:' + m.id) && !firstRun) out.push(`🤗[HF] ${m.id} (dl:${m.downloads||0}, likes:${m.likes||0})\nhttps://huggingface.co/${m.id}`);
  } catch (e) {}
}
staticData.seen = seen;
staticData.seeded = true;

async function tg(text) {
  await this.helpers.httpRequest({ method: 'POST', url: `https://api.telegram.org/bot${TOKEN}/sendMessage`, body: { chat_id: CHAT, text, disable_web_page_preview: true }, json: true });
}
if (firstRun) {
  await tg.call(this, `🔎 キーワード監視をセットアップしました。既存の項目（${Object.keys(seen).length}件）は既読にしました。次回から新着だけ通知します。`);
  return [{ json: { seeded: true, count: Object.keys(seen).length } }];
}
if (out.length) {
  const header = `🔎 キーワード監視 新着 ${out.length}件\n\n`;
  const chunks = []; let cur = header;
  for (const block of out) { if ((cur + '\n\n' + block).length > 3800) { chunks.push(cur); cur = block; } else { cur = cur === header ? cur + block : cur + '\n\n' + block; } }
  if (cur) chunks.push(cur);
  for (const c of chunks) await tg.call(this, c);
}
return [{ json: { sent: out.length } }];
