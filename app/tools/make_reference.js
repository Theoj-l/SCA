// Records the built app's key numbers to data/app_reference.json, so notebooks/MoveWell_Analysis.ipynb can check
// that the notebook and the app agree. Run after `python app/build.py`:
//     npm install playwright && npx playwright install chromium
//     node app/tools/make_reference.js
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
(async () => { const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1440,height:900}});
  await p.goto('file://' + path.join(ROOT, 'app', 'MoveWell_HDB_Moving_Demand.html')); await p.waitForTimeout(1000);
  await p.evaluate(()=>openAnalysis()); await p.waitForTimeout(8000);
  const ref = await p.evaluate(()=>{ const m=MODEL, L=MOVEWELL.LAST; const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
    const res4 = CL.best(CL.X,4);
    const yearly = L.sc.map(s=>[0,1,2,3,4].map(k=>{let v=0;for(let t=k*12;t<k*12+12;t++)v+=s.res[t]+s.rent[t]+s.bto[t]+s.priv[t];return v;}));
    const q=(a,pp)=>{const s=[...a].sort((x,y)=>x-y);const pos=(s.length-1)*pp,lo=Math.floor(pos),hi=Math.ceil(pos);return s[lo]+(s[hi]-s[lo])*(pos-lo)};
    return {
      hNow: Object.fromEntries([1,3,5,6,10,20,30].map(a=>[a,m.hNow(a)])), h1: Object.fromEntries([1,3,5,6,10,20,30].map(a=>[a,m.h1(a)])),
      E2026:m.E(2026), E2031:m.E(2031), annual2025:m.annual(2025),
      S:m.S, M:m.M, mu:m.mu, phi:m.phi, sdM:m.sdM, epsSd:m.epsSd,
      metrics:m.metrics, rolling:{model:m.rolling.model.map(mean), naive:m.rolling.naive.map(mean)},
      dyn:m.dyn, shocks:{bRec:m.shocks.bRec,bPol:m.shocks.bPol,r2Plain:m.shocks.r2Plain,r2Ind:m.shocks.r2Ind,bPol11:m.shocks.bPol11,loo:m.shocks.loo},
      CR:newsvendor(A).CR, nv:newsvendor(A),
      clusters:{k:4, inertia:res4.inertia, sil:CL.silhouette(CL.X,res4.labels), labels:Object.fromEntries(CL.rows.map((r,i)=>[r.name,res4.labels[i]])), names:CL.nameClusters(res4)},
      strategies:Object.fromEntries(Object.entries(L.results).map(([k,v])=>[k,{meanNPV:v.meanNPV,pLoss:v.pLoss,cvar5:v.cvar5,cashNeed:v.cashNeed,T:[0,12,24,36,48].map(t=>v.T[t]),irr:v.irr}])),
      jobs2031:{p10:q(yearly.map(r=>r[4]),0.1),p50:q(yearly.map(r=>r[4]),0.5),p90:q(yearly.map(r=>r[4]),0.9)},
      scen:L.scen.map(r=>({name:r.name,res31:r.res31,npv:r.npv,pLoss:r.pLoss,cvar:r.cvar})),
      jobsYear:Object.fromEntries(JOB_YEARS.map(y=>[y,jobsYear(y)]))
    }; });
  fs.writeFileSync(path.join(ROOT, 'data', 'app_reference.json'), JSON.stringify(ref, null, 1)); console.log('wrote data/app_reference.json'); await b.close(); })();
