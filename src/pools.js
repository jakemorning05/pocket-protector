// ---------- Pools: pick'em (confidence) and survivor ----------
// Week to plan for: the first week with at least 3 games still to play (so Monday night alone doesn't hold it back)
const planWeek = (() => { for (let w = 1; w <= 18; w++) if (games.filter((g) => g.wk === w && !g.done).length >= 3) return w; return 18; })();
let poolView = prefs.get('pool', 'pickem'), poolSrc = prefs.get('psrc', 'model'), pkWeek = planWeek;
const SRC_LABEL = { model: 'Model', market: 'Market', blend: 'Blend' };
// home team's chance to win under the chosen source (market odds only exist where a line is posted)
function srcProb(g, src) {
  const mp = mkProb(g);
  if (src === 'market' && mp != null) return mp;
  if (src === 'blend' && mp != null) return (g.p + mp) / 2;
  return g.p;
}
const usesMarket = (g, src) => src !== 'model' && mkProb(g) != null;
const segBtns = (name, cur, items) => '<div class="seg" role="group" aria-label="' + name + '">' + items.map(([k, l]) => '<button data-' + name + '="' + k + '" aria-pressed="' + (k === cur) + '">' + l + '</button>').join('') + '</div>';
const pct1 = (p) => p > 0 && p < 0.2 ? (p * 100).toFixed(1) + '%' : pct(p);
const winBar = (p) => '<span class="pbar" aria-hidden="true"><i style="width:' + (p * 100).toFixed(0) + '%"></i></span>';

// confidence pool: rank a week's games by the favorite's chance; most confident gets n points
function pickemWeek(w, src) {
  const gs = games.filter((g) => g.wk === w).map((g) => {
    const pH = srcProb(g, src), home = pH >= 0.5, p = home ? pH : 1 - pH;
    const pick = home ? g.h : g.a, opp = home ? g.a : g.h;
    const mFav = hasFav(g) ? (favHome(g) ? g.h : g.a) : null;
    const res = g.done ? (g.hs === g.as ? 'tie' : ((g.hs > g.as) === home ? 'w' : 'l')) : null;
    return { g, pick, opp, home, p, mFav, res };
  }).sort((x, y) => y.p - x.p || (x.g.day + x.g.time).localeCompare(y.g.day + y.g.time));
  gs.forEach((r, i) => { r.pts = gs.length - i; });
  return gs;
}
function pickemSeason(src) {
  let pts = 0, max = 0, w = 0, l = 0, weeks = 0;
  for (let wk = 1; wk <= 18; wk++) {
    const wg = games.filter((g) => g.wk === wk);
    if (!wg.length || wg.some((g) => !g.done)) continue;
    weeks++;
    for (const r of pickemWeek(wk, src)) { max += r.pts; if (r.res === 'w') { pts += r.pts; w++; } else if (r.res === 'l') l++; }
  }
  return { pts, max, w, l, weeks };
}

function renderPickem(box) {
  const rows = pickemWeek(pkWeek, poolSrc);
  const n = rows.length, maxPts = n * (n + 1) / 2;
  const exp = rows.reduce((s, r) => s + r.pts * r.p, 0);
  const done = rows.filter((r) => r.res), scored = rows.filter((r) => r.res === 'w').reduce((s, r) => s + r.pts, 0);
  const lost = rows.filter((r) => r.res === 'l').reduce((s, r) => s + r.pts, 0);
  const right = rows.filter((r) => r.res === 'w').length, wrong = rows.filter((r) => r.res === 'l').length;
  const left = rows.filter((r) => !r.res);
  const proj = scored + left.reduce((s, r) => s + r.pts * r.p, 0);
  const wkGames = games.filter((g) => g.wk === pkWeek), lastG = wkGames.slice().sort((a, b) => (a.day + a.time).localeCompare(b.day + b.time)).pop();
  const noMarket = poolSrc !== 'model' && rows.some((r) => !usesMarket(r.g, poolSrc));
  const season = ['model', 'market', 'blend'].map((s) => [s, pickemSeason(s)]);
  const upsets = rows.filter((r) => r.mFav && r.mFav !== r.pick);
  const byes = TEAMS.filter((t) => !wkGames.some((g) => g.a === t || g.h === t));

  let h = '<div class="weekbar"><button class="iconbtn" id="pk-prev" aria-label="Previous week"' + (pkWeek <= 1 ? ' disabled' : '') + '>‹</button>' +
    '<div><h2>Week ' + pkWeek + '</h2><p class="muted small">' + dayFmt(wkGames[0]) + ' – ' + dayFmt(lastG) + (pkWeek === planWeek ? ' · this week' : '') + '</p></div>' +
    '<button class="iconbtn" id="pk-next" aria-label="Next week"' + (pkWeek >= 18 ? ' disabled' : '') + '>›</button></div>';
  h += '<div class="tiles num">' +
    (done.length ? '<div class="tile"><span class="label">Points so far</span><b>' + scored + '</b><span class="muted small">' + lost + ' lost · ' + maxPts + ' possible</span></div>' +
      '<div class="tile"><span class="label">Picks right</span><b>' + right + '–' + wrong + '</b><span class="muted small">' + (left.length ? left.length + ' still to play' : 'Week complete') + '</span></div>'
      : '<div class="tile"><span class="label">Expected points</span><b>' + exp.toFixed(0) + '</b><span class="muted small">of ' + maxPts + ' possible</span></div>' +
      '<div class="tile"><span class="label">Expected right</span><b>' + rows.reduce((s, r) => s + r.p, 0).toFixed(1) + '</b><span class="muted small">of ' + n + ' games</span></div>') +
    (done.length && left.length ? '<div class="tile"><span class="label">Projected finish</span><b>' + proj.toFixed(0) + '</b><span class="muted small">points, if the rest go as expected</span></div>' : '') +
    (lastG ? '<div class="tile"><span class="label">Tiebreaker</span><b>' + Math.round(lastG.tot) + '</b><span class="muted small">Total points, ' + lastG.a + ' @ ' + lastG.h + '</span></div>' : '') + '</div>';

  h += '<div class="panel"><div class="panel-head"><h3>Picks in confidence order</h3><span class="muted small">' + SRC_LABEL[poolSrc] + ' odds</span></div>' +
    '<div class="tablewrap"><table class="ptable pk"><thead><tr><th>Pts</th><th class="l">Pick</th><th class="l">Chance</th>' + (done.length ? '<th class="l">Result</th>' : '') + '</tr></thead><tbody>' +
    rows.map((r) => {
      const tags = (r.mFav && r.mFav !== r.pick ? ' <span class="tag">Upset pick</span>' : '') + (r.p < 0.55 ? ' <span class="tag">Coin flip</span>' : '');
      const sc = r.home ? r.g.hs + '–' + r.g.as : r.g.as + '–' + r.g.hs; // pick's score first
      const res = r.res === 'w' ? '<span class="res w">✓ ' + sc + '</span>' : r.res === 'l' ? '<span class="res l">✗ ' + sc + '</span>' : r.res === 'tie' ? '<span class="res t">Tie</span>' : '<span class="muted">Not played</span>';
      return '<tr><td class="pk-pts">' + r.pts + '</td><td class="l" style="white-space:normal"><span class="teamcell"><span class="abbr">' + r.pick + '</span><span class="hide-sm">' + esc(nick(r.pick)) + '</span></span> <span class="muted small">' + (r.home ? 'vs ' : '@ ') + r.opp + (r.res ? '' : ' · ' + kick(r.g)) + '</span>' + tags + '</td>' +
        '<td class="l num">' + winBar(r.p) + ' ' + pct(r.p) + (usesMarket(r.g, poolSrc) || poolSrc === 'model' ? '' : ' <span class="muted small">model</span>') + '</td>' + (done.length ? '<td class="l">' + res + '</td>' : '') + '</tr>';
    }).join('') + '</tbody></table></div>' +
    (byes.length ? '<p class="muted small" style="margin-top:8px">Bye: ' + byes.join(', ') + '</p>' : '') +
    (noMarket ? '<p class="muted small" style="margin-top:8px">No betting line is posted yet for games marked “model”, so those use the model’s odds.</p>' : '') + '</div>';

  h += '<div class="panel"><div class="panel-head"><h3>How each set of odds has done</h3><span class="muted small">2026, completed weeks</span></div>' +
    '<div class="tablewrap"><table><thead><tr><th class="l">Odds</th><th>Picks right</th><th>Points</th></tr></thead><tbody>' +
    season.map(([s, x]) => '<tr' + (s === poolSrc ? ' class="hl"' : '') + '><td class="l">' + SRC_LABEL[s] + '</td><td>' + x.w + '–' + x.l + (x.w + x.l ? ' (' + pct(x.w / (x.w + x.l)) + ')' : '') + '</td><td>' + (x.max ? pct(x.pts / x.max) : '–') + '</td></tr>').join('') +
    '</tbody></table></div><p class="muted small" style="margin-top:8px">Points are the share of the maximum confidence points. Blend averages the model and the market. Over 2017–25 the betting market’s odds did a little better than the model (about 72% of max points vs. 70%), and blending them didn’t beat the market. This season the model has been ahead. Every past pick here was made before kickoff.</p></div>';

  h += '<div class="panel prose"><h3>How to use it</h3><ul>' +
    '<li><strong>Confidence pools:</strong> enter the picks in this order. Your surest game gets the most points.</li>' +
    '<li><strong>Straight-up pools:</strong> just take the pick column.</li>' +
    '<li><strong>Big pools:</strong> picking the favorite everywhere maximizes expected points, but so does everyone else. To finish first among hundreds of entries, consider an upset where the model and the market disagree' + (upsets.length ? ' (this week: ' + upsets.map((r) => r.pick + ' over ' + r.opp).join(', ') + ')' : '') + '.</li></ul></div>';
  box.innerHTML = h;
  box.querySelector('#pk-prev').onclick = () => { pkWeek--; renderPools(); };
  box.querySelector('#pk-next').onclick = () => { pkWeek++; renderPools(); };
}

// ---------- survivor ----------
// min-cost assignment of rows (weeks) to columns (teams), rows <= columns (Hungarian algorithm with potentials)
function assign(cost) {
  const n = cost.length, m = n ? cost[0].length : 0, INF = 1e18;
  if (!n) return [];
  const u = new Float64Array(n + 1), v = new Float64Array(m + 1), p = new Int32Array(m + 1), way = new Int32Array(m + 1);
  for (let i = 1; i <= n; i++) {
    p[0] = i; let j0 = 0;
    const minv = new Float64Array(m + 1).fill(INF), used = new Uint8Array(m + 1);
    do {
      used[j0] = 1; const i0 = p[j0]; let delta = INF, j1 = 0;
      for (let j = 1; j <= m; j++) if (!used[j]) {
        const cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
        if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
        if (minv[j] < delta) { delta = minv[j]; j1 = j; }
      }
      for (let j = 0; j <= m; j++) { if (used[j]) { u[p[j]] += delta; v[j] -= delta; } else minv[j] -= delta; }
      j0 = j1;
    } while (p[j0] !== 0);
    do { const j1 = way[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
  }
  const ans = new Array(n).fill(-1);
  for (let j = 1; j <= m; j++) if (p[j]) ans[p[j] - 1] = j - 1;
  return ans;
}
const NO_GAME = 60; // cost of a week with no game (bye or already kicked off) ~ log(1e-26)
// win chance for every team in every week; null = no game left to pick
function survivorGrid(src) {
  const grid = {};
  for (let w = 1; w <= 18; w++) {
    grid[w] = {};
    for (const g of games) {
      if (g.wk !== w || g.done) continue;
      const pH = srcProb(g, src);
      grid[w][g.h] = { p: pH, opp: g.a, home: true, g }; grid[w][g.a] = { p: 1 - pH, opp: g.h, home: false, g };
    }
  }
  return grid;
}
// best plan for the given weeks using only the given teams: maximizes the chance of surviving every week
function bestPlan(weeks, teams, grid) {
  if (!weeks.length) return { prob: 1, picks: [] };
  const cost = weeks.map((w) => teams.map((t) => { const x = grid[w][t]; return x && x.p > 0 ? -Math.log(x.p) : NO_GAME; }));
  const a = assign(cost);
  let prob = 1; const picks = [];
  weeks.forEach((w, i) => { const t = teams[a[i]], x = t && grid[w][t]; picks.push({ w, t, x }); prob *= x ? x.p : 0; });
  return { prob, picks };
}
let svUsed = new Set(prefs.get('svUsed', [])), svStart = null, svHorizon = prefs.get('svH', 'all'), svShowAll = false;
function renderSurvivor(box) {
  const startWeeks = []; for (let w = planWeek; w <= 18; w++) if (games.some((g) => g.wk === w && !g.done)) startWeeks.push(w);
  if (svStart == null || !startWeeks.includes(svStart)) svStart = startWeeks[0];
  const end = svHorizon === 'all' ? 18 : Math.min(18, svStart + (+svHorizon) - 1);
  const weeks = []; for (let w = svStart; w <= end; w++) weeks.push(w);
  const grid = survivorGrid(poolSrc);
  const avail = TEAMS.filter((t) => !svUsed.has(t));
  const enough = avail.length >= weeks.length;
  const plan = enough ? bestPlan(weeks, avail, grid) : null;
  // every option this week: its win chance now, and the best you can do afterwards without it
  const opts = enough ? avail.filter((t) => grid[svStart][t]).map((t) => {
    const x = grid[svStart][t], rest = bestPlan(weeks.slice(1), avail.filter((u) => u !== t), grid);
    let later = null;
    for (const w of weeks.slice(1)) { const y = grid[w][t]; if (y && (!later || y.p > later.p)) later = { w, ...y }; }
    return { t, x, surv: x.p * rest.prob, later };
  }).sort((a, b) => b.surv - a.surv) : [];
  const shown = svShowAll ? opts : opts.slice(0, 10);
  const safest = opts.slice().sort((a, b) => b.x.p - a.x.p)[0];

  let h = '<div class="controls">' +
    '<label class="field" style="min-width:140px"><span class="label">Picking for</span><select id="sv-start">' + startWeeks.map((w) => '<option value="' + w + '"' + (w === svStart ? ' selected' : '') + '>Week ' + w + '</option>').join('') + '</select></label>' +
    '<div class="field" style="min-width:0"><span class="label">Plan ahead</span>' + segBtns('svh', svHorizon, [['4', '4 weeks'], ['8', '8 weeks'], ['all', 'Season']]) + '</div></div>';
  h += '<div class="panel"><div class="panel-head"><h3>Teams you’ve already used</h3><span class="muted small">' + svUsed.size + ' used' + (svUsed.size ? ' · <button class="linkbtn" id="sv-clear">Clear</button>' : '') + '</span></div>' +
    '<div class="divchips">' + Object.entries(DIVS).map(([d, ts]) => '<div><span class="label">' + d + '</span><div class="chips">' +
      ts.map((t) => '<button class="chip" data-svt="' + t + '" aria-pressed="' + svUsed.has(t) + '" title="' + esc(full(t)) + '">' + t + '</button>').join('') + '</div></div>').join('') + '</div>' +
    '<p class="muted small" style="margin-top:8px">Tap a team to mark it used. Saved on this device.</p></div>';
  if (!enough) {
    h += '<p class="notice">Only ' + avail.length + ' teams left for ' + weeks.length + ' weeks. Shorten the plan or unmark a team.</p>';
    box.innerHTML = h; wireSurvivor(box); return;
  }
  h += '<div class="tiles num"><div class="tile"><span class="label">Best pick, Week ' + svStart + '</span><b>' + (opts[0] ? opts[0].t : '–') + '</b><span class="muted small">' + (opts[0] ? pct(opts[0].x.p) + ' to win ' + (opts[0].x.home ? 'vs ' : '@ ') + opts[0].x.opp : 'No games left this week') + '</span></div>' +
    '<div class="tile"><span class="label">Survive Weeks ' + svStart + '–' + end + '</span><b>' + pct1(plan.prob) + '</b><span class="muted small">Following the plan below</span></div>' +
    (safest && opts[0] && safest.t !== opts[0].t ? '<div class="tile"><span class="label">Safest pick this week</span><b>' + safest.t + '</b><span class="muted small">' + pct(safest.x.p) + ' to win, but worth more later</span></div>' : '') + '</div>';
  h += '<div class="panel"><div class="panel-head"><h3>Week ' + svStart + ' options</h3><span class="muted small">' + SRC_LABEL[poolSrc] + ' odds' + (poolSrc !== 'model' ? ' this week, model after' : '') + '</span></div>' +
    '<p class="muted small" style="max-width:64ch;margin-bottom:8px">“Survive” is the chance of making it through Week ' + end + ' if you take this team now and then follow the best path with the teams you have left. The highest win chance this week isn’t always the best pick, because a strong team may be worth more later.</p>' +
    '<div class="tablewrap"><table class="ptable"><thead><tr><th class="l">Team</th><th class="l">Win now</th><th>Survive</th><th class="l">Later</th></tr></thead><tbody>' +
    shown.map((o, i) => '<tr' + (i === 0 ? ' class="hl"' : '') + '><td class="l"><span class="teamcell"><span class="abbr">' + o.t + '</span><span class="hide-sm">' + esc(nick(o.t)) + '</span></span> <span class="muted small">' + (o.x.home ? 'vs ' : '@ ') + o.x.opp + '</span></td>' +
      '<td class="l num">' + winBar(o.x.p) + ' ' + pct(o.x.p) + '</td><td>' + pct1(o.surv) + '</td>' +
      '<td class="l" style="white-space:normal">' + (o.later ? pct(o.later.p) + ' <span class="muted small">Wk&nbsp;' + o.later.w + ' ' + (o.later.home ? 'vs&nbsp;' : '@&nbsp;') + o.later.opp + '</span>' : '<span class="muted small">–</span>') + '</td></tr>').join('') +
    '</tbody></table></div>' + (opts.length > 10 ? '<p style="margin-top:8px"><button class="linkbtn" id="sv-more">' + (svShowAll ? 'Show top 10' : 'Show all ' + opts.length) + '</button></p>' : '') + '</div>';
  h += '<div class="panel"><div class="panel-head"><h3>Best path</h3><span class="muted small">Weeks ' + svStart + '–' + end + '</span></div>' +
    '<div class="tablewrap"><table class="ptable"><thead><tr><th class="l">Week</th><th class="l">Pick</th><th class="l">Win chance</th><th>Still alive</th></tr></thead><tbody>' +
    (() => { let alive = 1; return plan.picks.map((pk) => { alive *= pk.x ? pk.x.p : 0;
      return '<tr><td class="l">' + pk.w + '</td><td class="l"><span class="teamcell"><span class="abbr">' + pk.t + '</span><span class="hide-sm">' + esc(nick(pk.t)) + '</span></span> <span class="muted small">' + (pk.x.home ? 'vs ' : '@ ') + pk.x.opp + '</span></td>' +
        '<td class="l num">' + winBar(pk.x.p) + ' ' + pct(pk.x.p) + '</td><td>' + pct1(alive) + '</td></tr>'; }).join(''); })() +
    '</tbody></table></div><p class="muted small" style="margin-top:8px">The path is re-solved every time the odds update, so treat later weeks as a sketch. Odds for later weeks are pulled toward 50% because ratings, quarterbacks and injuries will change before then' + (end === 18 ? ', and some teams rest starters in Week 18' : '') + '.</p></div>';
  h += '<p class="notice">Not included: how many people in your pool are on each team. In a big pool, a slightly riskier team that few others pick can be worth it, since a popular favorite losing knocks out much of the field.</p>';
  box.innerHTML = h; wireSurvivor(box);
}
function wireSurvivor(box) {
  box.querySelectorAll('[data-svt]').forEach((b) => b.onclick = () => {
    const t = b.dataset.svt; if (svUsed.has(t)) svUsed.delete(t); else svUsed.add(t);
    prefs.set('svUsed', [...svUsed]); renderPools();
  });
  const c = box.querySelector('#sv-clear'); if (c) c.onclick = () => { svUsed = new Set(); prefs.set('svUsed', []); renderPools(); };
  const s = box.querySelector('#sv-start'); if (s) s.onchange = (e) => { svStart = +e.target.value; renderPools(); };
  box.querySelectorAll('[data-svh]').forEach((b) => b.onclick = () => { svHorizon = b.dataset.svh; prefs.set('svH', svHorizon); renderPools(); });
  const m = box.querySelector('#sv-more'); if (m) m.onclick = () => { svShowAll = !svShowAll; renderPools(); };
}

function renderPools() {
  const el = document.getElementById('view-pools');
  el.innerHTML = '<div><h2>Pools</h2><p class="intro">Office pool tools built on what the model does best: picking winners. Pick’em ranks every game for confidence pools. Survivor plans one team per week without reusing anyone.</p></div>' +
    '<div class="controls">' + segBtns('pool', poolView, [['pickem', 'Pick’em'], ['survivor', 'Survivor']]) +
    '<div class="field" style="min-width:0"><span class="label">Odds from</span>' + segBtns('psrc', poolSrc, [['model', 'Model'], ['market', 'Market'], ['blend', 'Blend']]) + '</div></div>' +
    '<div id="pool-body" style="display:grid;gap:16px;margin-top:4px"></div>';
  el.querySelectorAll('[data-pool]').forEach((b) => b.onclick = () => { poolView = b.dataset.pool; prefs.set('pool', poolView); renderPools(); });
  el.querySelectorAll('[data-psrc]').forEach((b) => b.onclick = () => { poolSrc = b.dataset.psrc; prefs.set('psrc', poolSrc); renderPools(); });
  const box = el.querySelector('#pool-body');
  if (poolView === 'survivor') renderSurvivor(box); else renderPickem(box);
}
