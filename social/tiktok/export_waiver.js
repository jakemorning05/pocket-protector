const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.route(/^https?:\/\/(?!localhost)/, r => r.abort());
  await p.goto('file://' + require('path').resolve(__dirname, '../../docs/index.html') + ''); await p.waitForTimeout(800);
  const out = await p.evaluate(() => {
    const base = {}; for (const r of FAN.games) if (!base[r.id] || r.wk === FAN.cw) base[r.id] = r;
    const ros = Object.entries(FAN.ros).filter(([id]) => base[id]).map(([id, t]) => ({ id, name: base[id].name, pos: base[id].pos, team: base[id].team, pg: t.n ? fp(t) / t.n : 0, n: t.n, s: (FAN.season || {})[id] }));
    const rank = {}; for (const pos of ['QB', 'RB', 'WR', 'TE']) ros.filter(r => r.pos === pos).sort((a, b) => b.pg - a.pg).forEach((r, i) => rank[r.id] = i + 1);
    const wk = FAN.cw;
    const thisWk = {}; FAN.games.filter(r => r.wk === wk).forEach(r => thisWk[r.id] = { pts: fp(r), opp: r.opp, flag: r.flag });
    return { cw: FAN.cw, risers: FAN.risers.map(r => ({ ...r, rk: rank[r.id], pg: (ros.find(x => x.id === r.id) || {}).pg, wk: thisWk[r.id] })), cuffs: FAN.cuffs,
      ros: ros.map(r => ({ ...r, rk: rank[r.id], wk: thisWk[r.id] })) };
  });
  require('fs').writeFileSync(__dirname + '/waiv.json', JSON.stringify(out));
  console.log('cw', out.cw);
  console.log('RISERS'); out.risers.forEach(r => console.log(r.name, r.pos, r.team, r.before.toFixed(1), '->', r.recent.toFixed(1), 'rk', r.rk, 'pg', r.pg && r.pg.toFixed(1), 'wk', r.wk && r.wk.pts.toFixed(1), r.wk && r.wk.opp));
  console.log('CUFFS'); out.cuffs.slice().sort((a, b) => (b.rb2_share || 0) - (a.rb2_share || 0)).slice(0, 12).forEach(c => console.log(c.team, c.rb1, c.rb1_out ? '(OUT)' : '', (c.rb1_share || 0).toFixed(2), c.rb2, (c.rb2_share || 0).toFixed(2)));
  await b.close();
})();
