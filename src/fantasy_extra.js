// ---------- Fantasy: buy low / sell high and the trade calculator ----------
const fanBase = () => { const b = {}; for (const r of FAN.games) if (!b[r.id] || r.wk === FAN.cw + 1) b[r.id] = r; return b; };
const tdPts = (r) => 4 * (r.pass_td || 0) + 6 * ((r.rush_td || 0) + (r.rec_td || 0));
// compare what a player has scored per game with what the model projects per game the rest of the way
function marketRows() {
  const base = fanBase(), rows = [];
  for (const [id, ros] of Object.entries(FAN.ros)) {
    const b = base[id], s = (FAN.season || {})[id];
    if (!b || !s || s.g < 4 || !ros.n) continue;
    const act = fp(s) / s.g, proj = fp(ros) / ros.n;
    if (Math.max(act, proj) < (b.pos === 'QB' ? 14 : 8)) continue;
    const tdGap = tdPts(s) / s.g - tdPts(ros) / ros.n, use = b.pos !== 'QB' && s.before != null ? s.recent - s.before : 0;
    const diff = proj - act;
    let why;
    if (diff > 0) why = use >= 3 ? 'Workload is growing: ' + s.before.toFixed(0) + ' touches a game before, ' + s.recent.toFixed(0) + ' in the last two'
      : tdGap <= -1.2 ? 'Touchdowns haven’t matched his workload yet' : 'Yardage has run below his usual efficiency';
    else why = use <= -3 ? 'Workload is shrinking: ' + s.before.toFixed(0) + ' touches a game before, ' + s.recent.toFixed(0) + ' in the last two'
      : tdGap >= 1.2 ? 'Scoring touchdowns at a rate that rarely lasts' : 'Yardage has run above his usual efficiency';
    rows.push({ ...b, act, proj, diff, why });
  }
  return rows;
}
function marketHtml() {
  const rows = marketRows();
  const table = (list, cls) => '<div class="tablewrap"><table class="ptable"><thead><tr><th class="l">Player</th><th>So far</th><th>Projected</th><th>Change</th><th class="l">Why</th></tr></thead><tbody>' +
    list.map((r) => '<tr><td class="l"><span class="pname">' + esc(r.name) + '</span><span class="ppos pos-' + r.pos + '">' + r.pos + ' · ' + r.team + '</span>' + (r.flag ? ' <span class="qbchip" data-tip="' + esc(r.flag) + '">News</span>' : '') + '</td><td>' + r.act.toFixed(1) + '</td><td><b>' + r.proj.toFixed(1) + '</b></td><td class="' + cls + '">' + signed(r.diff) + '</td><td class="l muted small" style="white-space:normal;min-width:11em">' + r.why + '</td></tr>').join('') +
    '</tbody></table></div>';
  const buy = rows.filter((r) => r.diff >= 1.5).sort((a, b) => b.diff - a.diff).slice(0, 12);
  const sell = rows.filter((r) => r.diff <= -1.5).sort((a, b) => a.diff - b.diff).slice(0, 12);
  return '<div class="panel"><div class="panel-head"><h3>Buy low</h3><span class="muted small">Projected to score more than they have</span></div>' + (buy.length ? table(buy, 'rank-good') : '<p class="muted">No clear buy-low players this week.</p>') + '</div>' +
    '<div class="panel"><div class="panel-head"><h3>Sell high</h3><span class="muted small">Projected to score less than they have</span></div>' + (sell.length ? table(sell, 'rank-bad') : '<p class="muted">No clear sell-high players this week.</p>') + '</div>' +
    '<p class="muted small">Points per game. “So far” is this season’s average; “Projected” is the model’s average over the player’s remaining games, including the schedule. Players need four games played to appear. These are candidates, not guarantees: check the “News” notes and the reason before making an offer.</p>';
}

// trade value = rest-of-season points above the player you could get off waivers at that position (12-team league)
const REPL_RANK = { QB: 12, RB: 30, WR: 36, TE: 12 };
function tradeValues() {
  const base = fanBase(), by = { QB: [], RB: [], WR: [], TE: [] };
  for (const [id, ros] of Object.entries(FAN.ros)) { const b = base[id]; if (b && by[b.pos]) by[b.pos].push({ ...b, tot: fp(ros), n: ros.n }); }
  const out = {};
  for (const [pos, list] of Object.entries(by)) {
    list.sort((a, b) => b.tot / Math.max(1, b.n) - a.tot / Math.max(1, a.n));
    const rp = list[Math.min(REPL_RANK[pos], list.length - 1)], replPg = rp ? rp.tot / Math.max(1, rp.n) : 0;
    for (const r of list) out[r.id] = { ...r, pg: r.n ? r.tot / r.n : 0, value: Math.max(0, r.tot - replPg * r.n) };
  }
  return out;
}
let trade = prefs.get('trade', { give: [], get: [] });
function tradeHtml() {
  const V = tradeValues(), max = Math.max(1, ...Object.values(V).map((x) => x.value));
  const score = (x) => Math.round(x.value / max * 100);
  trade.give = trade.give.filter((id) => V[id]); trade.get = trade.get.filter((id) => V[id]);
  const taken = new Set([...trade.give, ...trade.get]);
  const options = ['QB', 'RB', 'WR', 'TE'].map((pos) => '<optgroup label="' + pos + '">' + Object.values(V).filter((x) => x.pos === pos && !taken.has(x.id)).sort((a, b) => b.value - a.value)
    .map((x) => '<option value="' + x.id + '">' + esc(x.name) + ' (' + x.team + ') · ' + score(x) + '</option>').join('') + '</optgroup>').join('');
  const side = (key, title) => {
    const list = trade[key].map((id) => V[id]), tot = list.reduce((s, x) => s + x.value, 0);
    return '<div class="panel"><div class="panel-head"><h3>' + title + '</h3><span class="muted small">Value ' + Math.round(list.reduce((s, x) => s + score(x), 0)) + '</span></div>' +
      (list.length ? '<div class="tablewrap"><table class="ptable"><thead><tr><th class="l">Player</th><th>Pts/game</th><th>Value</th><th></th></tr></thead><tbody>' +
        list.map((x) => '<tr><td class="l"><span class="pname">' + esc(x.name) + '</span><span class="ppos pos-' + x.pos + '">' + x.pos + ' · ' + x.team + '</span></td><td>' + x.pg.toFixed(1) + '</td><td><b>' + score(x) + '</b></td><td><button class="linkbtn" data-trm="' + key + ':' + x.id + '" aria-label="Remove ' + esc(x.name) + '" style="text-decoration:none;font-size:1.1rem;padding:0 4px">✕</button></td></tr>').join('') + '</tbody></table></div>'
        : '<p class="muted small">No players yet.</p>') +
      '<label class="field" style="margin-top:10px"><span class="label">Add a player</span><select id="tr-add-' + key + '"><option value="">Choose…</option>' + options + '</select></label></div>';
  };
  const g = trade.give.map((id) => V[id]), r = trade.get.map((id) => V[id]);
  const gv = g.reduce((s, x) => s + x.value, 0), rv = r.reduce((s, x) => s + x.value, 0), diff = rv - gv;
  const weeks = Math.max(1, ...[...g, ...r].map((x) => x.n));
  let verdict = '';
  if (g.length && r.length) {
    const even = Math.abs(diff) < Math.max(6, 0.08 * Math.max(gv, rv));
    const head = even ? 'About even' : diff > 0 ? 'You win this trade' : 'You lose this trade';
    const detail = even ? 'The two sides are within a few points of each other over the rest of the season.'
      : 'You ' + (diff > 0 ? 'gain' : 'give up') + ' about ' + Math.abs(diff).toFixed(0) + ' points of starter value over the rest of the season, roughly ' + (Math.abs(diff) / weeks).toFixed(1) + ' a week.';
    const slots = r.length < g.length ? ' You also get ' + (g.length - r.length) + ' roster spot' + (g.length - r.length > 1 ? 's' : '') + ' back for waiver pickups, and the side that gets the single best player usually does better than the totals show.'
      : r.length > g.length ? ' You’d have to drop ' + (r.length - g.length) + ' player' + (r.length - g.length > 1 ? 's' : '') + ' to make room, so count what you’d lose there too.' : '';
    verdict = '<div class="panel"><div class="result"><div class="side"><span class="label">You give</span><span class="bigpct num">' + Math.round(g.reduce((s, x) => s + score(x), 0)) + '</span></div><div class="side r"><span class="label">You get</span><span class="bigpct num">' + Math.round(r.reduce((s, x) => s + score(x), 0)) + '</span></div></div>' +
      '<p style="margin-top:10px"><b class="' + (even ? '' : diff > 0 ? 'rank-good' : 'rank-bad') + '">' + head + '.</b> ' + detail + slots + '</p></div>';
  }
  return '<div class="tradegrid">' + side('give', 'You give') + side('get', 'You get') + '</div>' + verdict +
    (g.length || r.length ? '<p><button class="linkbtn" id="tr-clear">Clear trade</button></p>' : '') +
    '<p class="muted small">Value is a player’s projected rest-of-season points above the kind of starter you could find on waivers in a 12-team league, scaled so the most valuable player is 100. It follows the scoring format above. Injured players who are out of the projections aren’t listed. It doesn’t know your roster, so a trade that fills a hole in your lineup is worth more to you than the numbers say.</p>';
}
function wireFantasyExtra(el) {
  for (const key of ['give', 'get']) {
    const sel = el.querySelector('#tr-add-' + key);
    if (sel) sel.onchange = (e) => { if (e.target.value) { trade[key].push(e.target.value); prefs.set('trade', trade); renderFantasy(); } };
  }
  el.querySelectorAll('[data-trm]').forEach((b) => b.onclick = () => { const [key, id] = b.dataset.trm.split(':'); trade[key] = trade[key].filter((x) => x !== id); prefs.set('trade', trade); renderFantasy(); });
  const c = el.querySelector('#tr-clear'); if (c) c.onclick = () => { trade = { give: [], get: [] }; prefs.set('trade', trade); renderFantasy(); };
}
