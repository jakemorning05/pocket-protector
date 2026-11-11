const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.route(/^https?:\/\/(?!localhost)/, r => r.abort());
  await p.goto('file://' + require('path').resolve(__dirname, '../../docs/index.html') + '');
  await p.waitForTimeout(800);
  const rows = await p.evaluate(() => {
    const rs = marketRows();
    const S = FAN.season || {};
    return rs.map(r => ({ name: r.name, pos: r.pos, team: r.team, act: +r.act.toFixed(1), proj: +r.proj.toFixed(1), diff: +r.diff.toFixed(1), why: r.why, flag: r.flag || '', s: S[r.id], ros: FAN.ros[r.id], id: r.id }));
  });
  require('fs').writeFileSync(__dirname + '/mkt.json', JSON.stringify(rows, null, 1));
  const buy = rows.filter(r => r.diff >= 1.5).sort((a, b) => b.diff - a.diff), sell = rows.filter(r => r.diff <= -1.5).sort((a, b) => a.diff - b.diff);
  console.log('BUY'); buy.slice(0, 14).forEach(r => console.log(r.name, r.pos, r.team, r.act, '->', r.proj, r.diff, '|', r.why, '|', r.flag));
  console.log('SELL'); sell.slice(0, 14).forEach(r => console.log(r.name, r.pos, r.team, r.act, '->', r.proj, r.diff, '|', r.why, '|', r.flag));
  await b.close();
})();
