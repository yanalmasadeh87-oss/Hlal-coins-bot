<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>EW Strategy V3</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#080c14;--bg2:#0d1421;--bg3:#111827;--border:#1e293b;--gold:#f0b429;--green:#22c55e;--red:#ef4444;--blue:#3b82f6;--orange:#f97316;--text:#e2e8f0;--muted:#64748b}
body{background:var(--bg);color:var(--text);font-family:'Courier New',monospace;padding:12px;min-height:100vh}
h1{font-size:20px;font-weight:900;background:linear-gradient(90deg,#f0b429,#f97316);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:2px}
.sub{text-align:center;font-size:9px;color:var(--muted);letter-spacing:2px;margin-bottom:14px}
.row{display:flex;gap:6px;margin-bottom:10px}
input{flex:1;background:var(--bg3);border:1px solid var(--border);border-radius:6px;padding:10px 12px;color:var(--text);font-family:'Courier New',monospace;font-size:13px;outline:none}
input:focus{border-color:var(--gold)}
.gbtn{background:var(--gold);color:#000;border:none;border-radius:6px;padding:10px 18px;font-weight:900;font-size:12px;cursor:pointer;font-family:'Courier New',monospace}
.coins{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.cbtn{background:var(--bg3);color:var(--muted);border:1px solid var(--border);border-radius:4px;padding:6px 12px;font-size:11px;cursor:pointer;font-family:'Courier New',monospace}
.modes{display:flex;gap:6px;margin-bottom:10px}
.mbtn{flex:1;background:var(--bg3);color:var(--muted);border:1px solid var(--border);border-radius:4px;padding:8px;font-size:11px;cursor:pointer;font-family:'Courier New',monospace;text-align:center}
.mbtn.on{background:#3b82f611;color:var(--blue);border-color:var(--blue)}
.tfs{display:flex;gap:5px;margin-bottom:14px}
.tbtn{flex:1;background:var(--bg3);color:var(--muted);border:1px solid var(--border);border-radius:4px;padding:6px 2px;font-size:10px;cursor:pointer;font-family:'Courier New',monospace;text-align:center}
.tbtn.on{background:#f0b42922;color:var(--gold);border-color:var(--gold)}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:12px}
.ct{font-size:9px;letter-spacing:3px;color:var(--muted);margin-bottom:10px}
.pbig{font-size:28px;font-weight:900;color:var(--gold)}
.ph{display:flex;justify-content:space-between;align-items:flex-start}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.si{background:var(--bg3);border-radius:6px;padding:10px;border:1px solid var(--border)}
.sl{font-size:8px;letter-spacing:2px;color:var(--muted);margin-bottom:3px}
.sv{font-size:13px;font-weight:900}
.wr{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border);font-size:10px}
.wr:last-child{border-bottom:none}
.ci{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:5px;margin-bottom:4px;font-size:10px}
.sb{padding:10px;border-radius:6px;font-size:11px;font-weight:700;text-align:center;margin-bottom:12px}
.info{text-align:center;padding:30px;color:var(--muted);font-size:12px;line-height:2}
.err{text-align:center;padding:20px;color:var(--red);font-size:11px;line-height:1.6}
.disc{text-align:center;font-size:8px;color:#334155;margin-top:16px;letter-spacing:1px;line-height:1.8}
canvas{width:100%!important;display:block;border-radius:4px}
.sbar{height:6px;border-radius:3px;background:var(--bg3);margin-top:6px;overflow:hidden}
.sfill{height:100%;border-radius:3px}
</style>
</head>
<body>
<h1>EW STRATEGY V3</h1>
<div class="sub">YOUR WAVE STRUCTURE · BINANCE DATA · MULTI-TIMEFRAME</div>
<div class="row">
  <input type="text" id="inp" placeholder="Enter symbol (BTC, XRP, ETH, SOL...)">
  <button class="gbtn" id="gobtn">GO</button>
</div>
<div class="coins">
  <button class="cbtn" id="btn-btc">BTC</button>
  <button class="cbtn" id="btn-xrp">XRP</button>
  <button class="cbtn" id="btn-eth">ETH</button>
  <button class="cbtn" id="btn-sol">SOL</button>
  <button class="cbtn" id="btn-bnb">BNB</button>
  <button class="cbtn" id="btn-ada">ADA</button>
</div>
<div class="modes">
  <button class="mbtn on" id="m-swing">SWING</button>
  <button class="mbtn" id="m-scalp">SCALP</button>
</div>
<div class="tfs" id="tfs">
  <button class="tbtn" id="tf-30">1M</button>
  <button class="tbtn" id="tf-90">3M</button>
  <button class="tbtn" id="tf-180">6M</button>
  <button class="tbtn" id="tf-365">1Y</button>
  <button class="tbtn" id="tf-730">2Y</button>
  <button class="tbtn on" id="tf-max">MAX</button>
</div>
<div id="main"><div class="info">Tap a coin or type a symbol (BTC, XRP...) and tap GO<br>Powered by Binance — Free · Unlimited · No Key Needed</div></div>
<div class="disc">FOR EDUCATIONAL PURPOSES ONLY · NOT FINANCIAL ADVICE<br>SPOT TRADING ONLY · HALAL COINS · ALWAYS MANAGE YOUR RISK</div>
<script>
var BN = 'https://api.binance.com/api/v3';
var sym = 'BTCUSDT';
var days = 365;
var mode = 'swing';
var priceData = [], volData = [], coinSym = 'BTC';
var globalATH = 0;  // Always from MAX history

// Binance symbol → display name
var NAMES = {
  'BTC':'Bitcoin','ETH':'Ethereum','XRP':'Ripple','SOL':'Solana',
  'BNB':'BNB','ADA':'Cardano','AVAX':'Avalanche','DOT':'Polkadot',
  'LINK':'Chainlink','ATOM':'Cosmos','NEAR':'NEAR','FIL':'Filecoin',
  'APT':'Aptos','ARB':'Arbitrum','OP':'Optimism','INJ':'Injective',
  'STX':'Stacks','TIA':'Celestia','SEI':'Sei','GRT':'The Graph',
  'VET':'VeChain','HBAR':'Hedera','ICP':'Internet Computer',
  'FTM':'Fantom','ETC':'Ethereum Classic','WLD':'Worldcoin',
  'RENDER':'Render','KAS':'Kaspa','ALGO':'Algorand','XLM':'Stellar',
  'LTC':'Litecoin','TON':'Toncoin','XTZ':'Tezos','BCH':'Bitcoin Cash',
  'IMX':'Immutable X','FET':'Fetch.ai','OCEAN':'Ocean Protocol',
  'AKT':'Akash','AR':'Arweave','HNT':'Helium','ONE':'Harmony',
  'ZIL':'Zilliqa','QTUM':'Qtum','DCR':'Decred','RVN':'Ravencoin',
  'EGLD':'MultiversX','FLOW':'Flow','ANKR':'Ankr','STORJ':'Storj',
  'BAND':'Band Protocol','NMR':'Numeraire','GLM':'Golem','SKL':'Skale',
  'CELO':'Celo','ROSE':'Oasis','CTSI':'Cartesi','WAVES':'Waves',
  'DGB':'DigiByte','GALA':'Gala','AXS':'Axie Infinity','SAND':'The Sandbox',
  'MANA':'Decentraland','ENJ':'Enjin','CHZ':'Chiliz','ASTR':'Astar',
  'BAT':'Basic Attention Token','LPT':'Livepeer','AUDIO':'Audius',
  'CVC':'Civic','POWR':'Power Ledger','HOT':'Holo'
};

function show(h){document.getElementById('main').innerHTML=h;}
function fp(p){
  if(!p&&p!==0)return'N/A';
  if(p>=1000)return'$'+Math.round(p).toLocaleString();
  if(p>=1)return'$'+p.toFixed(4);
  if(p>=0.01)return'$'+p.toFixed(5);
  return'$'+p.toFixed(7);
}
function fpc(p){return(p>=0?'+':'')+p.toFixed(2)+'%';}

function getInterval(){
  if(mode==='scalp') return '4h';  // 4H better for wave counting
  if(days<=30) return '4h';
  if(days<=90) return '4h';
  return '1d';
}

function getLimit(){
  if(mode==='scalp') return 540; // 90 days of 4H candles
  if(days===730) return 730;
  if(days===365) return 365;
  if(days===180) return 180;
  if(days===90) return 90;
  return 1000; // MAX
}

function loadSym(s){
  sym = s.toUpperCase() + 'USDT';
  coinSym = s.toUpperCase();
  document.getElementById('inp').value = s.toUpperCase();
  fetchData();
}

function doSearch(){
  var v = document.getElementById('inp').value.trim().toUpperCase();
  if(!v) return;
  coinSym = v;
  sym = v + 'USDT';
  fetchData();
}

function setMode(m){
  mode = m;
  document.getElementById('m-swing').classList.toggle('on', m==='swing');
  document.getElementById('m-scalp').classList.toggle('on', m==='scalp');
  if(sym) fetchData();
}

function setTF(d, btnId){
  days = d;
  document.querySelectorAll('.tbtn').forEach(function(b){b.classList.remove('on');});
  var el = document.getElementById(btnId);
  if(el) el.classList.add('on');
  if(sym) fetchData();
}

function fetchData(){
  show('<div class="info">Loading ' + coinSym + '/USDT from Binance...<br>Please wait</div>');
  var interval = getInterval();
  var limit = getLimit();

  // Fetch klines (OHLCV) + 24hr stats + MAX history for ATH
  var urlK   = BN + '/klines?symbol=' + sym + '&interval=' + interval + '&limit=' + limit;
  var url24  = BN + '/ticker/24hr?symbol=' + sym;
  var urlMax = BN + '/klines?symbol=' + sym + '&interval=1w&limit=200'; // Weekly max for ATH

  Promise.all([
    fetch(urlK).then(function(r){return r.json();}),
    fetch(url24).then(function(r){return r.json();}),
    fetch(urlMax).then(function(r){return r.json();})
  ]).then(function(res){
    var klines = res[0], stats = res[1], maxKlines = res[2];
    // Calculate real ATH from full history
    if(maxKlines && maxKlines.length && !maxKlines.code){
      var maxHighs = maxKlines.map(function(k){return parseFloat(k[2]);});
      globalATH = Math.max.apply(null, maxHighs);
    }
    if(!klines || !klines.length || klines.code){
      show('<div class="err">❌ Symbol not found on Binance.<br>Try: BTC, ETH, XRP, SOL, BNB, ADA, AVAX, DOT...<br><br>Note: Use Binance symbols only (no USDT suffix needed)</div>');
      return;
    }
    priceData = klines.map(function(k){
      return {
        date: new Date(k[0]),
        open:  parseFloat(k[1]),
        high:  parseFloat(k[2]),
        low:   parseFloat(k[3]),
        price: parseFloat(k[4]),
        vol:   parseFloat(k[5])
      };
    });
    volData = priceData.map(function(d){return d.vol;});
    renderPage(stats);
  }).catch(function(e){
    show('<div class="err">❌ API Error: ' + e.message + '<br>Check your internet connection and try again.</div>');
  });
}

// ── INDICATORS ─────────────────────────────────────────────────
function calcRSI(prices){
  var period=14;
  if(prices.length<period+1)return 50;
  var ag=0,al=0,i,d;
  for(i=1;i<=period;i++){d=prices[i]-prices[i-1];if(d>0)ag+=d;else al+=Math.abs(d);}
  ag/=period;al/=period;
  for(i=period;i<prices.length;i++){
    d=prices[i]-prices[i-1];
    ag=(ag*13+(d>0?d:0))/14;
    al=(al*13+(d<0?Math.abs(d):0))/14;
  }
  return al===0?100:100-(100/(1+ag/al));
}

function calcEMA(prices,period){
  if(prices.length<period)return[];
  var k=2/(period+1),sum=0,i;
  for(i=0;i<period;i++)sum+=prices[i];
  var r=[sum/period];
  for(i=period;i<prices.length;i++)r.push(prices[i]*k+r[r.length-1]*(1-k));
  return r;
}

function calcMACD(prices){
  if(prices.length<35)return{cross:false,turning:false,hist:0,histLine:[]};
  var ef=calcEMA(prices,12),es=calcEMA(prices,26);
  var ml=[],i;
  for(i=0;i<es.length;i++)ml.push(ef[i+14]-es[i]);
  if(ml.length<9)return{cross:false,turning:false,hist:0,histLine:[]};
  var sl=calcEMA(ml,9),diff=ml.length-sl.length,hist=[];
  for(i=0;i<sl.length;i++)hist.push(ml[i+diff]-sl[i]);
  var h=hist[hist.length-1]||0,ph=hist[hist.length-2]||0;
  return{cross:h>0&&ph<=0,turning:h>ph,hist:h,prev:ph,histLine:hist};
}

function calcStoch(prices,period){
  period=period||14;
  if(prices.length<period)return 50;
  var sl=prices.slice(-period);
  var high=Math.max.apply(null,sl),low=Math.min.apply(null,sl);
  if(high===low)return 50;
  return((prices[prices.length-1]-low)/(high-low))*100;
}

function calcEWO(prices){
  if(prices.length<35)return 0;
  var m5=0,m35=0,i;
  for(i=prices.length-5;i<prices.length;i++)m5+=prices[i];
  for(i=prices.length-35;i<prices.length;i++)m35+=prices[i];
  return m5/5-m35/35;
}

// ── WAVE DETECTION ─────────────────────────────────────────────
function findPivots(prices,minMove){
  minMove=minMove||0.10;
  var n=prices.length,win=Math.max(3,Math.floor(n/20)),pivots=[],i,sl,mx,mn;
  for(i=win;i<n-win;i++){
    sl=prices.slice(i-win,i+win+1);
    mx=Math.max.apply(null,sl);mn=Math.min.apply(null,sl);
    if(prices[i]===mx&&prices[i]>prices[i-1]&&prices[i]>prices[i+1])
      pivots.push({idx:i,price:prices[i],type:'peak'});
    else if(prices[i]===mn&&prices[i]<prices[i-1]&&prices[i]<prices[i+1])
      pivots.push({idx:i,price:prices[i],type:'trough'});
  }
  var st=prices[0]<prices[Math.min(10,n-1)]?'trough':'peak';
  pivots.unshift({idx:0,price:prices[0],type:st});
  pivots.push({idx:n-1,price:prices[n-1],type:'current'});
  var sig=[pivots[0]],k,prev,curr,move;
  for(k=1;k<pivots.length;k++){
    prev=sig[sig.length-1];curr=pivots[k];
    if(prev.type===curr.type){
      if(curr.type==='peak'&&curr.price>prev.price)sig[sig.length-1]=curr;
      else if(curr.type==='trough'&&curr.price<prev.price)sig[sig.length-1]=curr;
      continue;
    }
    move=Math.abs((curr.price-prev.price)/prev.price);
    if(move>=minMove)sig.push(curr);
  }
  return sig;
}

function validateEW(pv){
  var issues=[];
  if(pv.length>=3){
    var w1r=Math.abs(pv[1].price-pv[0].price);
    if(w1r>0){
      var w2r=Math.abs(pv[2].price-pv[1].price)/w1r*100;
      if(pv[2].price<pv[0].price)issues.push('W2>100% W1');
      else if(w2r<38)issues.push('W2 shallow('+w2r.toFixed(0)+'%)');
    }
  }
  if(pv.length>=4){var w1s=Math.abs(pv[1].price-pv[0].price),w3s=Math.abs(pv[3].price-pv[2].price);if(w3s<w1s)issues.push('W3<W1');}
  if(pv.length>=5&&pv[4].price<pv[1].price)issues.push('W4 overlaps W1');
  return{valid:issues.length===0,issues:issues};
}

function detectEntry(pv, prices, rsiVal){
  if(pv.length<3)return'';
  
  // W2 bottom
  var w1r=Math.abs(pv[1].price-pv[0].price);
  if(w1r>0){var w2r=Math.abs(pv[2].price-pv[1].price)/w1r*100;if(w2r>=38&&w2r<=100)return'W2';}
  
  // W4 bottom
  if(pv.length>=5){
    var w3r=Math.abs(pv[3].price-pv[2].price);
    if(w3r>0){var w4r=Math.abs(pv[4].price-pv[3].price)/w3r*100;if(w4r>=23&&w4r<=38&&pv[4].price>pv[1].price)return'W4';}
  }
  
  // Wave C bottom — ABC correction complete
  if(prices && pv.length>=4){
    var wc = detectWaveCBottom(pv, prices, rsiVal||50);
    if(wc.detected) return 'Wave C';
  }
  
  return'';
}

function checkAlternation(pv){
  if(pv.length<5)return{valid:true,note:'Need W4'};
  var w1=Math.abs(pv[1].price-pv[0].price),w3=Math.abs(pv[3].price-pv[2].price);
  if(!w1||!w3)return{valid:true,note:'Cannot calc'};
  var w2r=Math.abs(pv[2].price-pv[1].price)/w1*100;
  var w4r=Math.abs(pv[4].price-pv[3].price)/w3*100;
  var alt=(w2r>50&&w4r<40)||(w2r<40&&w4r>40)||Math.abs(w2r-w4r)>15;
  return{valid:alt,note:alt?'Alternation ✓':'Similar depth',w2r:w2r,w4r:w4r};
}

function detectCandlestick(prices){
  if(prices.length<3)return{pattern:'None',bullish:false};
  var p1=prices[prices.length-1],p2=prices[prices.length-2],p3=prices[prices.length-3];
  if(p2<p3&&p1>p2&&(p1-p2)>(p3-p2)*0.5)return{pattern:'Bullish Engulfing',bullish:true};
  if(p2<p3*0.97&&p1>p2*1.02)return{pattern:'Hammer',bullish:true};
  if(p3>p2&&p2<p1&&p1>(p3+p2)/2)return{pattern:'Morning Star',bullish:true};
  if(Math.abs(p1-p2)/p2<0.005&&p2<p3*0.98)return{pattern:'Doji Reversal',bullish:true};
  if(p1<p2&&p2<p3)return{pattern:'Downtrend',bullish:false};
  return{pattern:'No pattern',bullish:false};
}

// ── WAVE SYMMETRY CHECK ───────────────────────────────────────
// W1, W3, W5 should be proportional
// W2, W4 corrective waves should alternate in depth/duration
function checkWaveSymmetry(waves) {
  if (waves.length < 5) return { valid: true, score: 0, note: 'Need 5 waves', details: [] };
  var details = [], score = 0, total = 0;

  // W1, W3, W5 sizes
  var w1 = Math.abs(waves[1].price - waves[0].price);
  var w3 = waves.length >= 4 ? Math.abs(waves[3].price - waves[2].price) : 0;
  var w5 = waves.length >= 6 ? Math.abs(waves[5].price - waves[4].price) : 0;

  // Rule 1: W3 should be largest impulse wave
  if (w3 > 0 && w1 > 0) {
    var w3_vs_w1 = w3 / w1;
    var ok = w3_vs_w1 >= 1.0;
    total++; if (ok) score++;
    details.push({ label: 'W3 > W1', ok: ok, detail: (w3_vs_w1*100).toFixed(0) + '% of W1' });
  }

  // Rule 2: W5 should be smaller than W3 (unless extended)
  if (w5 > 0 && w3 > 0) {
    var w5_vs_w3 = w5 / w3;
    var ok2 = w5_vs_w3 <= 1.2; // W5 can be up to 120% of W3
    total++; if (ok2) score++;
    details.push({ label: 'W5 ≤ W3', ok: ok2, detail: (w5_vs_w3*100).toFixed(0) + '% of W3' });
  }

  // Rule 3: W2 and W4 durations should differ (alternation)
  var w2_size = waves.length >= 3 ? Math.abs(waves[2].price - waves[1].price) : 0;
  var w4_size = waves.length >= 5 ? Math.abs(waves[4].price - waves[3].price) : 0;
  if (w2_size > 0 && w4_size > 0) {
    var ratio = Math.abs(w2_size - w4_size) / Math.max(w2_size, w4_size);
    var ok3 = ratio >= 0.15; // At least 15% difference
    total++; if (ok3) score++;
    details.push({ label: 'W2≠W4 Size', ok: ok3, detail: (ratio*100).toFixed(0) + '% difference' });
  }

  // Rule 4: W1 and W5 should be similar size (if W3 is extended)
  if (w5 > 0 && w1 > 0 && w3 > w1 * 1.5) {
    var w5_vs_w1 = w5 / w1;
    var ok4 = w5_vs_w1 >= 0.5 && w5_vs_w1 <= 2.0;
    total++; if (ok4) score++;
    details.push({ label: 'W1≈W5', ok: ok4, detail: (w5_vs_w1*100).toFixed(0) + '% of W1' });
  }

  var pct = total > 0 ? score / total * 100 : 50;
  return { valid: pct >= 60, score: pct, details: details, note: pct >= 80 ? 'Symmetry excellent' : pct >= 60 ? 'Symmetry good' : 'Symmetry poor' };
}

// ── BLUE BOX ENTRY ZONE ───────────────────────────────────────
// High-probability entry zone based on Fibonacci + EW structure
// Blue box = overlap between 0.618 retrace of W1 and 1.0 retrace of W1
function calcBlueBox(waves) {
  if (waves.length < 3) return null;
  var w0 = waves[0].price, w1 = waves[1].price, w2 = waves[2].price;
  var w1_range = Math.abs(w1 - w0);
  var direction = w1 > w0 ? 1 : -1;

  // Blue box for W2: between 0.618 and 0.786 retracement of W1
  var fib618 = direction > 0 ? w1 - w1_range * 0.618 : w1 + w1_range * 0.618;
  var fib786 = direction > 0 ? w1 - w1_range * 0.786 : w1 + w1_range * 0.786;

  var boxTop    = Math.max(fib618, fib786);
  var boxBottom = Math.min(fib618, fib786);

  var current = waves[waves.length-1].price;
  var inBox = current >= boxBottom && current <= boxTop;

  // Also check W4 blue box if we have enough waves
  var w4Box = null;
  if (waves.length >= 5) {
    var w3_start = waves[2].price, w3_end = waves[3].price;
    var w3_range = Math.abs(w3_end - w3_start);
    var dir3 = w3_end > w3_start ? 1 : -1;
    var f4_382 = dir3 > 0 ? w3_end - w3_range * 0.382 : w3_end + w3_range * 0.382;
    var f4_618 = dir3 > 0 ? w3_end - w3_range * 0.618 : w3_end + w3_range * 0.618;
    w4Box = {
      top: Math.max(f4_382, f4_618),
      bottom: Math.min(f4_382, f4_618),
      inBox: current >= Math.min(f4_382, f4_618) && current <= Math.max(f4_382, f4_618)
    };
  }

  return {
    w2Box: { top: boxTop, bottom: boxBottom, inBox: inBox },
    w4Box: w4Box,
    inAnyBox: inBox || (w4Box && w4Box.inBox),
    label: inBox ? 'In W2 Blue Box ✓' : (w4Box && w4Box.inBox) ? 'In W4 Blue Box ✓' : 'Outside Blue Box'
  };
}

// ── STOCHASTIC MOMENTUM INDEX (SMI) ──────────────────────────
// Better than regular Stochastic — smoother, less noise
// SMI = (close - midpoint) / (half range) * 100
function calcSMI(prices, period) {
  period = period || 14;
  if (prices.length < period) return 0;
  var result = [];
  for (var i = period - 1; i < prices.length; i++) {
    var slice = prices.slice(i - period + 1, i + 1);
    var high = Math.max.apply(null, slice);
    var low  = Math.min.apply(null, slice);
    var mid  = (high + low) / 2;
    var range = high - low;
    var smi  = range > 0 ? ((prices[i] - mid) / (range / 2)) * 100 : 0;
    result.push(smi);
  }
  // Smooth with EMA
  var smoothed = calcEMA(result, 3);
  return smoothed.length > 0 ? smoothed[smoothed.length - 1] : 0;
}

function calcSMIFull(prices, period) {
  period = period || 14;
  var result = [];
  for (var i = period - 1; i < prices.length; i++) {
    var slice = prices.slice(i - period + 1, i + 1);
    var high = Math.max.apply(null, slice);
    var low  = Math.min.apply(null, slice);
    var mid  = (high + low) / 2;
    var range = high - low;
    result.push(range > 0 ? ((prices[i] - mid) / (range / 2)) * 100 : 0);
  }
  return calcEMA(result, 3);
}

// ── TRUNCATED WAVE 5 DETECTION ────────────────────────────────
// W5 fails to exceed W3 high — signals exhaustion and major reversal
function detectTruncatedW5(waves, prices) {
  if (waves.length < 6) return { detected: false, note: 'Need W5 data' };

  var w3_high = waves[3].price;
  var w5_high = waves[5] ? waves[5].price : waves[waves.length-1].price;
  var current = prices[prices.length - 1];

  // Truncated W5: W5 peak is lower than W3 peak (bullish structure)
  var truncated = w5_high < w3_high && w5_high > waves[4].price;

  // RSI divergence confirms truncation
  var rsi_w3 = calcRSI(prices.slice(0, Math.min(waves[3].idx + 1, prices.length)));
  var rsi_w5 = calcRSI(prices.slice(0, Math.min((waves[5] ? waves[5].idx : prices.length - 1) + 1, prices.length)));
  var rsi_diverge = rsi_w5 < rsi_w3;

  var strong = truncated && rsi_diverge;

  return {
    detected: truncated,
    strong: strong,
    note: strong ? '⚠️ Truncated W5 — Major reversal imminent' :
          truncated ? 'Possible truncated W5' : 'No truncation',
    w3_price: w3_high,
    w5_price: w5_high
  };
}

// ── FIBONACCI W1 RETRACE ──────────────────────────────────────
function calcFibRetrace(pivots) {
  if (pivots.length < 3) return { retrace: 0, valid: false, label: 'No data' };
  var w1Range = Math.abs(pivots[1].price - pivots[0].price);
  if (w1Range === 0) return { retrace: 0, valid: false, label: 'Invalid W1' };
  var w2Range = Math.abs(pivots[2].price - pivots[1].price);
  var retrace = (w2Range / w1Range) * 100;
  var valid = retrace >= 38.2 && retrace <= 100;
  var label = '';
  if (retrace < 38.2)        label = 'Shallow (<38.2%)';
  else if (retrace <= 50.0)  label = '0.382 Fib Zone';
  else if (retrace <= 61.8)  label = '0.500 Fib Zone';
  else if (retrace <= 78.6)  label = '0.618 Golden Ratio ✓';
  else if (retrace <= 100)   label = '0.786 Deep Fib';
  else                        label = 'W2 > W1 (Invalid)';
  return { retrace: retrace, valid: valid, label: label,
           golden: retrace >= 38.2 && retrace <= 78.6 };
}

function calcW4Fib(pivots) {
  if (pivots.length < 5) return { retrace: 0, valid: false, label: 'Need W4' };
  var w3Range = Math.abs(pivots[3].price - pivots[2].price);
  if (w3Range === 0) return { retrace: 0, valid: false, label: 'Invalid W3' };
  var w4Range = Math.abs(pivots[4].price - pivots[3].price);
  var retrace = (w4Range / w3Range) * 100;
  var valid = retrace >= 23.6 && retrace <= 50.0;
  return { retrace: retrace, valid: valid,
           label: valid ? 'W4 Fib ' + retrace.toFixed(0) + '% of W3' : 'W4 outside Fib' };
}


// ── C=A EQUALITY RULE — Price + Time (fatinhijjawi method) ────
// 'متساوية' = equal in BOTH price length AND time duration
function calcCEqualsA(pivots, current) {
  if (pivots.length < 4) return { inZone: false, target: 0, label: 'Need more data' };
  for (var i = pivots.length-4; i >= 0; i--) {
    var p0=pivots[i], p1=pivots[i+1], p2=pivots[i+2], p3=pivots[i+3];
    if (!(p0.type==='peak' && p1.type==='trough' && p2.type==='peak' && p3.type==='trough')) continue;
    var waveA = Math.abs(p0.price - p1.price);
    if (waveA === 0) continue;
    var cStart = p2.price;
    var caTarget = cStart - waveA;
    var caExt = cStart - waveA * 1.618;
    var caRatio = (cStart - current) / waveA * 100;
    var proxCA = Math.abs(current - caTarget) / Math.abs(caTarget) * 100;
    var proxExt = Math.abs(current - caExt) / Math.abs(caExt) * 100;
    // TIME equality
    var aTime = p1.idx - p0.idx;
    var cTime = p3.idx - p2.idx;
    var timeRatio = aTime > 0 ? cTime / aTime * 100 : 0;
    var timeEqual = timeRatio >= 80 && timeRatio <= 120;
    var timeNote = 'Time: ' + timeRatio.toFixed(0) + '% of Wave A';
    if (proxCA <= 5 && timeEqual) return { inZone: true, target: caTarget, ratio: caRatio, label: 'C=A Price+Time ✓ (' + timeNote + ')' };
    if (proxCA <= 5) return { inZone: true, target: caTarget, ratio: caRatio, label: 'C=A Price ✓ | ' + timeNote };
    if (proxExt <= 5 && timeEqual) return { inZone: true, target: caExt, ratio: caRatio, label: 'C=1.618xA Price+Time ✓' };
    if (proxExt <= 5) return { inZone: true, target: caExt, ratio: caRatio, label: 'C=1.618xA Price ✓ | ' + timeNote };
    if (caRatio >= 80 && caRatio <= 120) return { inZone: true, target: caTarget, ratio: caRatio, label: 'Near C=A (' + caRatio.toFixed(0) + '% price | ' + timeNote + ')' };
    return { inZone: false, target: caTarget, ratio: caRatio, label: 'C=A at ' + fp(caTarget) + ' | ' + timeNote };
  }
  return { inZone: false, target: 0, ratio: 0, label: 'No ABC found' };
}

function detectWXY(pivots) {
  if (pivots.length < 7) return { detected: false, note: 'Need more data' };
  try {
    var wSize = Math.abs(pivots[2].price - pivots[0].price);
    if (wSize === 0) return { detected: false, note: 'Invalid' };
    var xRet = Math.abs(pivots[3].price - pivots[2].price) / wSize * 100;
    if (xRet >= 38 && xRet <= 78) return { detected: true, note: 'W-X-Y مركب (X=' + xRet.toFixed(0) + '%)' };
    return { detected: false, note: 'Simple ABC' };
  } catch(e) { return { detected: false, note: 'Cannot determine' }; }
}


// ── W-X-Y-X-Z TRIPLE COMBINATION (fatinhijjawi X1=X2 rule) ────
function detectWXYXZ(pivots, current) {
  if (pivots.length < 6) return { detected: false, label: 'Need more pivots' };
  var best = null;
  for (var i = 0; i <= pivots.length - 6; i++) {
    var p0=pivots[i], p1=pivots[i+1], p2=pivots[i+2],
        p3=pivots[i+3], p4=pivots[i+4], p5=pivots[i+5];
    if (!(p0.type==='peak' && p1.type==='trough' && p2.type==='peak' &&
          p3.type==='trough' && p4.type==='peak' && p5.type==='trough')) continue;
    // X1: p1->p2, X2: p3->p4
    var x1p = Math.abs(p2.price - p1.price);
    var x1t = p2.idx - p1.idx;
    var x2p = Math.abs(p4.price - p3.price);
    var x2t = p4.idx - p3.idx;
    if (x1p === 0 || x1t === 0) continue;
    var priceRatio = x2p / x1p * 100;
    var timeRatio  = x2t / x1t * 100;
    var priceEq = priceRatio >= 80 && priceRatio <= 120;
    var timeEq  = timeRatio  >= 75 && timeRatio  <= 125;
    var bothEq  = priceEq && timeEq;
    var zPrice  = p5.price;
    var nearZ   = Math.abs(current - zPrice) / zPrice * 100 <= 8;
    if (priceEq || timeEq) {
      best = {
        detected:   true,
        bothEqual:  bothEq,
        priceRatio: priceRatio,
        timeRatio:  timeRatio,
        zPrice:     zPrice,
        nearZ:      nearZ,
        label: 'WXYXZ X1=X2 ' + (bothEq ? 'Price+Time ✓' : priceEq ? 'Price ✓' : 'Time ✓') +
               ' (' + priceRatio.toFixed(0) + '% price | ' + timeRatio.toFixed(0) + '% time)'
      };
      if (bothEq && nearZ) break;
    }
  }
  return best || { detected: false, label: 'No WXYXZ found' };
}


function verifyWaves(waves,prices,vols){
  if(!waves||waves.length<3)return{score:0,passed:0,total:0,results:[],confidence:'LOW'};
  var res=[],tot=0,pass=0;
  function rsiAt(idx){return calcRSI(prices.slice(0,Math.min(idx+1,prices.length)));}
  function volAt(idx){if(!vols||!vols.length)return 0;var s=Math.max(0,idx-3),e=Math.min(vols.length-1,idx+3),sum=0,n=0;for(var j=s;j<=e;j++){sum+=vols[j]||0;n++;}return n?sum/n:0;}
  if(waves.length>=3){var w1r=Math.abs(waves[1].price-waves[0].price),w2r=w1r>0?Math.abs(waves[2].price-waves[1].price)/w1r*100:0,ok=w2r>=38&&w2r<=78.6;tot++;if(ok)pass++;res.push({wave:'W2',check:'Fib 38-78%',ok:ok,detail:w2r.toFixed(0)+'% retrace'});}
  if(waves.length>=4){var w1s=Math.abs(waves[1].price-waves[0].price),w3s=Math.abs(waves[3].price-waves[2].price),ok2=w3s>=w1s;tot++;if(ok2)pass++;res.push({wave:'W3',check:'Ext >100%',ok:ok2,detail:(w1s>0?w3s/w1s*100:0).toFixed(0)+'% of W1'});}
  if(waves.length>=5){var w3s2=Math.abs(waves[3].price-waves[2].price),w4r2=w3s2>0?Math.abs(waves[4].price-waves[3].price)/w3s2*100:0,ok3=w4r2>=23&&w4r2<=50;tot++;if(ok3)pass++;res.push({wave:'W4',check:'Fib 23-50%',ok:ok3,detail:w4r2.toFixed(0)+'% retrace'});}
  if(waves.length>=3){var r2=rsiAt(waves[2].idx),ok4=r2<50;tot++;if(ok4)pass++;res.push({wave:'W2',check:'RSI Oversold',ok:ok4,detail:'RSI:'+r2.toFixed(0)});}
  if(waves.length>=4){var r3=rsiAt(waves[3].idx),ok5=r3>55;tot++;if(ok5)pass++;res.push({wave:'W3',check:'RSI Strong',ok:ok5,detail:'RSI:'+r3.toFixed(0)});}
  if(waves.length>=4&&vols&&vols.length){var v1=volAt(waves[1].idx),v3=volAt(waves[3].idx),ok6=v3>=v1*0.7;tot++;if(ok6)pass++;res.push({wave:'W3',check:'Vol Strong',ok:ok6,detail:ok6?'Strong':'Weak'});}
  if(waves.length>=5&&vols&&vols.length){var v3b=volAt(waves[3].idx),v4=volAt(waves[4].idx),ok7=v4<=v3b*1.2;tot++;if(ok7)pass++;res.push({wave:'W4',check:'Vol Decline',ok:ok7,detail:ok7?'Declining':'Too high'});}
  var pct=tot>0?pass/tot*100:0,conf=pct>=80?'HIGH':pct>=60?'MEDIUM':pct>=40?'LOW':'VERY LOW';
  return{score:pct,passed:pass,total:tot,results:res,confidence:conf};
}

// ── RENDER ─────────────────────────────────────────────────────
function renderPage(stats){
  var prices=priceData.map(function(d){return d.price;});
  var highs=priceData.map(function(d){return d.high||d.price;});
  var lows=priceData.map(function(d){return d.low||d.price;});
  var current=prices[prices.length-1];
  // ATH logic:
  // SWING = real ATH from full history (globalATH)
  // SCALP = ATH from the 14-day window (local highs)
  var ath = (mode === 'swing' && globalATH > 0) ? globalATH : Math.max.apply(null,highs);
  var atl=Math.min.apply(null,lows);
  var chg=stats?parseFloat(stats.priceChangePercent||0):0;
  var name=NAMES[coinSym]||coinSym;
  var pctATH=((current-ath)/ath)*100;

  var rsiVal=calcRSI(prices);
  var macdRes=calcMACD(prices);
  var stoch=calcStoch(prices);
  var ewoVal=calcEWO(prices);

  var sens=mode==='scalp'?0.05:days<=90?0.06:days<=365?0.10:0.15;  // 5% min for 4H scalp
  var pivots=findPivots(prices,sens);
  var ewRes=validateEW(pivots);
  var labels=['W1','W2','W3','W4','W5','Wave A','Wave B','Wave C'];
  var waves=pivots.slice(0,8).map(function(p,i){
    return{label:labels[i]||('P'+(i+1)),price:p.price,type:p.type,idx:p.idx,
      date:priceData[p.idx]?priceData[p.idx].date:new Date(),
      color:p.type==='peak'?'#22c55e':p.type==='trough'?'#ef4444':'#f0b429'};
  });

  var entry=detectEntry(pivots, prices, rsiVal);
  var alt=checkAlternation(pivots);
  var candle=detectCandlestick(prices);
  var verif=verifyWaves(waves,prices,volData);
  var symmetry=checkWaveSymmetry(waves);
  var blueBox=calcBlueBox(waves);
  var smi=calcSMI(prices);
  var smiFull=calcSMIFull(prices);
  var truncW5=detectTruncatedW5(waves,prices);

  // Signal levels
  var slPct=mode==='scalp'?0.03:0.05;
  var tp1Pct=mode==='scalp'?0.03:0.05;
  var tp2Pct=mode==='scalp'?0.05:0.10;
  var tp3Pct=mode==='scalp'?0.08:0.15;
  var tp4Pct=mode==='scalp'?0.12:0.20;

  var sl=current*(1-slPct);
  var tp1=current*(1+tp1Pct);
  var tp2=current*(1+tp2Pct);
  var tp3=current*(1+tp3Pct);
  var tp4=current*(1+tp4Pct);

  // MA50 for trend
  var ma50=0,i;
  if(prices.length>=50){for(i=prices.length-50;i<prices.length;i++)ma50+=prices[i];ma50/=50;}
  else ma50=current;
  var daily_bull=current>ma50||pctATH<-50;

  // Checklist
  var vol_dec=false,vol_exp=false;
  if(volData.length>=10){
    var r5=0,p5=0;
    for(i=volData.length-5;i<volData.length;i++)r5+=volData[i];
    for(i=volData.length-10;i<volData.length-5;i++)p5+=volData[i];
    vol_dec=(r5/5)<(p5/5);
    vol_exp=volData[volData.length-1]>r5/5;
  }

  var checks=[
    {l:'Daily Trend Bullish',ok:daily_bull,cat:'TF'},
    {l:'MA50 Trend Confirmed',ok:current>ma50,cat:'TF'},
    {l:'5-Wave Impulse Detected',ok:waves.length>=5,cat:'EW'},
    {l:'EW Rules Valid',ok:ewRes.valid,cat:'EW'},
    {l:'Wave Count Verified ('+verif.score.toFixed(0)+'%)',ok:verif.score>=60,cat:'EW'},
    {l:'W2 or W4 Entry Zone',ok:entry!==''&&entry!=='Wave C',cat:'EW'},
    {l:'Wave C Bottom Detected',ok:entry==='Wave C',cat:'EW'},
    {l:'W2 Fib Retrace: '+fibW1.label,ok:fibW1.valid,cat:'Fib'},
    {l:'Golden Ratio Zone (38-78%)',ok:fibW1.golden,cat:'Fib'},
    {l:'W2 or W4 Fib Entry',ok:fibW1.valid||fibW4.valid,cat:'Fib'},
    {l:'C=A Zone: '+caResult.label,ok:caResult.inZone,cat:'Fib'},
    {l:'WXYXZ X1=X2: '+(wxyxzResult.detected?wxyxzResult.label:'Not detected'),ok:wxyxzResult.detected&&wxyxzResult.bothEqual,cat:'EW'},
    {l:'RSI Below 45 ('+rsiVal.toFixed(0)+')',ok:rsiVal<45,cat:'Mom'},
    {l:'Stochastic Below 25 ('+stoch.toFixed(0)+')',ok:stoch<25,cat:'Mom'},
    {l:'MACD Bullish',ok:macdRes.cross||macdRes.turning,cat:'Mom'},
    {l:'EWO Signal',ok:ewoVal!==0,cat:'Mom'},
    {l:'Volume Declining',ok:vol_dec,cat:'Vol'},
    {l:'Volume Expanding',ok:vol_exp,cat:'Vol'},
    {l:'ABC Structure',ok:waves.length>=6,cat:'Struct'},
    {l:'Alternation: '+alt.note,ok:alt.valid,cat:'Struct'},
    {l:'Candlestick: '+candle.pattern,ok:candle.bullish,cat:'Struct'},
    {l:'Wave Symmetry: '+symmetry.note,ok:symmetry.valid,cat:'Struct'},
    {l:'Blue Box Entry: '+( blueBox?blueBox.label:'No box'),ok:blueBox?blueBox.inAnyBox:false,cat:'Struct'},
    {l:'SMI Oversold ('+smi.toFixed(0)+')',ok:smi<-40,cat:'Mom'},
    {l:'No Truncated W5',ok:!truncW5.detected,cat:'EW'},
  ];

  var score=0;
  for(i=0;i<checks.length;i++)if(checks[i].ok)score++;

  var statusTxt,statusCol;
  if(wxyxzResult.detected&&wxyxzResult.bothEqual&&score>=10){statusTxt='🔥🔥 WXYXZ HIGHEST CONFIDENCE — '+mode.toUpperCase();statusCol='#22c55e';}
  else if(score>=14){statusTxt=(mode==='scalp'?'⚡':'📈')+' STRONG SIGNAL — '+mode.toUpperCase();statusCol='#22c55e';}
  else if(score>=11){statusTxt='🟡 WATCH — '+mode.toUpperCase()+' Setup Forming';statusCol='#f0b429';}
  else if(score>=8){statusTxt='🟠 DEVELOPING — Not Ready Yet';statusCol='#f97316';}
  else{statusTxt='🔴 NO SIGNAL — Wait for Setup';statusCol='#ef4444';}

  var confTxt;
  if(score>=14)confTxt='HIGH CONFIDENCE — Full position';
  else if(score>=11)confTxt='MEDIUM-HIGH — 75% position';
  else if(score>=8)confTxt='MEDIUM — 50% position';
  else confTxt='LOW — Skip this trade';

  var altTxt='';
  if(!ewRes.valid)altTxt='Alternate: ABC zigzag correction in progress';
  else if(pctATH<-70)altTxt='Alternate: Extended W2 — deep accumulation';
  else if(pctATH<-40)altTxt='Alternate: W4 correction within W3';

  var h='';
  var modeLabel = mode==='scalp' ? 'SCALP (4H · 90 Days)' : 'SWING (' + (days===1000?'MAX':days+'D') + ')';
  h+='<div style="text-align:center;font-size:11px;color:var(--muted);letter-spacing:2px;margin-bottom:12px">'+name+' ('+coinSym+'/USDT) · '+modeLabel+'</div>';
  h+='<div class="card"><div class="ph"><div><div class="ct">LIVE PRICE — BINANCE</div><div class="pbig">'+fp(current)+'</div><div style="font-size:11px;color:'+(chg>=0?'var(--green)':'var(--red)')+';margin-top:2px">'+fpc(chg)+' 24H</div></div>';
  h+='<div style="text-align:right;font-size:10px;color:var(--muted);line-height:2">';
  h+='<div>ATH: <span style="color:var(--gold)">'+fp(ath)+'</span></div>';
  h+='<div>From ATH: <span style="color:var(--red)">'+fpc(pctATH)+'</span></div>';
  h+='<div>RSI: <span style="color:'+(rsiVal<30?'var(--green)':rsiVal>70?'var(--red)':'var(--orange)')+'">'+rsiVal.toFixed(1)+'</span></div>';
  h+='<div>Stoch: <span style="color:'+(stoch<20?'var(--green)':stoch>80?'var(--red)':'var(--orange)')+'">'+stoch.toFixed(0)+'</span></div>';
  if(entry){
    var entryColor = entry==='Wave C' ? '#3b82f6' : 'var(--green)';
    var entryIcon  = entry==='Wave C' ? '🔵' : '✅';
    h+='<div>Zone: <span style="color:'+entryColor+'">'+entryIcon+' '+entry+' Bottom</span></div>';
  }
  h+='</div></div></div>';

  h+='<div class="card" style="padding:10px"><div class="ct">PRICE + WAVES + SIGNAL LEVELS</div><canvas id="priceChart"></canvas></div>';
  h+='<div class="card" style="padding:8px"><canvas id="rsiChart"></canvas></div>';
  h+='<div class="card" style="padding:8px"><canvas id="macdChart"></canvas></div>';
  h+='<div class="card" style="padding:8px"><canvas id="stochChart"></canvas></div>';
  h+='<div class="card" style="padding:8px"><canvas id="smiChart"></canvas></div>';
  h+='<div class="card" style="padding:8px"><canvas id="volChart"></canvas></div>';

  h+='<div class="sb" style="background:'+statusCol+'18;border:1px solid '+statusCol+'44;color:'+statusCol+'">'+statusTxt+'</div>';
  if(altTxt)h+='<div style="padding:8px 12px;border-radius:5px;font-size:10px;margin-bottom:8px;border:1px solid #f0b42933;color:#f0b429;background:#f0b42908">'+altTxt+'</div>';

  h+='<div class="card"><div class="ct">SIGNAL LEVELS — '+mode.toUpperCase()+'</div><div class="g2">';
  h+='<div class="si" style="border-color:#22c55e33;grid-column:1/-1"><div class="sl">ENTRY ZONE</div><div class="sv" style="color:var(--green)">'+fp(current*0.99)+' – '+fp(current*1.01)+'</div></div>';
  var tpLabel=mode==='scalp'?['+3%','+5%','+8%','+12%']:[ '+5%','+10%','+15%','+20%'];
  var slLabel=mode==='scalp'?'-3%':'-5%';
  [[tp1,tpLabel[0]],[tp2,tpLabel[1]],[tp3,tpLabel[2]],[tp4,tpLabel[3]]].forEach(function(t,idx){
    h+='<div class="si" style="border-color:#f0b42933"><div class="sl">TP'+(idx+1)+' ('+t[1]+')</div><div class="sv" style="color:var(--gold)">'+fp(t[0])+'</div></div>';
  });
  h+='<div class="si" style="border-color:#ef444433;grid-column:1/-1"><div class="sl">STOP LOSS ('+slLabel+')</div><div class="sv" style="color:var(--red)">'+fp(sl)+'</div></div>';
  h+='</div></div>';

  h+='<div class="card"><div class="ct">WAVE COUNT</div>';
  for(i=0;i<waves.length;i++){var w=waves[i];var dt=w.date?w.date.toLocaleDateString('en-US',{month:'short',year:'numeric'}):'';h+='<div class="wr"><span style="color:'+w.color+';font-weight:900;min-width:60px">'+w.label+'</span><span style="color:var(--muted);font-size:9px">'+dt+'</span><span style="font-weight:700">'+fp(w.price)+'</span><span style="font-size:9px;color:'+w.color+'">'+( w.type==='peak'?'▲ TOP':w.type==='trough'?'▼ BOT':'● NOW')+'</span></div>';}
  h+=(!ewRes.valid?'<div style="font-size:10px;color:var(--red);margin-top:8px;padding:6px;background:#ef444411;border-radius:4px">⚠️ '+ewRes.issues.join(' · ')+'</div>':'<div style="font-size:10px;color:var(--green);margin-top:8px">✅ All EW Rules Valid</div>');
  h+='<div style="margin-top:10px"><div style="font-size:9px;letter-spacing:2px;color:var(--muted);margin-bottom:6px">WAVE VERIFICATION — '+verif.passed+'/'+verif.total+'</div>';
  h+='<div class="sbar"><div class="sfill" style="width:'+verif.score.toFixed(0)+'%;background:'+(verif.score>=80?'var(--green)':verif.score>=60?'var(--gold)':'var(--red)')+'"></div></div>';
  h+='<div style="margin-top:6px;font-size:10px;color:'+(verif.score>=80?'var(--green)':verif.score>=60?'var(--gold)':'var(--red)')+'">'+verif.confidence+' ('+verif.score.toFixed(0)+'%)</div>';
  for(var vi=0;vi<verif.results.length;vi++){var vr=verif.results[vi];h+='<div style="display:flex;gap:8px;padding:4px 6px;border-radius:3px;margin-top:3px;background:'+(vr.ok?'#22c55e08':'#ef444408')+'"><span>'+(vr.ok?'✅':'❌')+'</span><span style="color:var(--gold);min-width:40px;font-size:9px">'+vr.wave+'</span><span style="color:var(--muted);font-size:9px">'+vr.check+': '+vr.detail+'</span></div>';}
  h+='</div></div>';

  h+='<div class="card"><div class="ct">18-POINT CHECKLIST — '+score+'/'+checks.length+'</div>';
  h+='<div class="sbar"><div class="sfill" style="width:'+(score/checks.length*100).toFixed(0)+'%;background:'+(score>=14?'var(--green)':score>=11?'var(--gold)':score>=8?'var(--orange)':'var(--red)')+'"></div></div>';
  h+='<div style="margin:6px 0 10px;font-size:10px;color:var(--muted)">';
  var cats=['TF','EW','Price','Fib','Mom','Vol','Struct'];
  for(var c=0;c<cats.length;c++){var cat=cats[c];var ok=0,tot=0;for(i=0;i<checks.length;i++){if(checks[i].cat===cat){tot++;if(checks[i].ok)ok++;}}h+='<span style="color:'+(ok===tot?'var(--green)':ok>0?'var(--gold)':'var(--red)')+';margin-right:8px">'+cat+' '+ok+'/'+tot+'</span>';}
  h+='</div>';
  for(i=0;i<checks.length;i++){var ck=checks[i];h+='<div class="ci" style="background:'+(ck.ok?'#22c55e0d':'#ef44440d')+';border:1px solid '+(ck.ok?'#22c55e22':'#ef444422')+'"><span style="font-size:13px;min-width:20px">'+(ck.ok?'✅':'❌')+'</span><span style="color:'+(ck.ok?'var(--text)':'var(--muted)')+';flex:1">'+ck.l+'</span><span style="font-size:9px;color:var(--muted)">'+ck.cat+'</span></div>';}
  h+='<div style="margin-top:10px;padding:10px;border-radius:6px;text-align:center;font-size:12px;font-weight:700;background:'+(score>=14?'#22c55e11':score>=11?'#f0b42911':score>=8?'#f9731611':'#ef444411')+';border:1px solid '+(score>=14?'#22c55e33':score>=11?'#f0b42933':score>=8?'#f9731633':'#ef444433')+';color:'+(score>=14?'var(--green)':score>=11?'var(--gold)':score>=8?'var(--orange)':'var(--red)')+'">'+confTxt+'</div></div>';

  // Professional Tools Section
  h += '<div class="card"><div class="ct">PROFESSIONAL TOOLS</div>';

  // Blue Box
  if (blueBox) {
    h += '<div style="padding:8px;border-radius:5px;margin-bottom:8px;background:'+(blueBox.inAnyBox?'#3b82f611':'#0d142188')+';border:1px solid '+(blueBox.inAnyBox?'#3b82f6':'#1e293b')+'">';
    h += '<div style="font-size:9px;letter-spacing:2px;color:#3b82f6;margin-bottom:4px">🔵 BLUE BOX ENTRY ZONE</div>';
    if (blueBox.w2Box) {
      h += '<div style="font-size:10px;color:'+(blueBox.w2Box.inBox?'#3b82f6':'var(--muted)')+'">W2 Zone: '+fp(blueBox.w2Box.bottom)+' – '+fp(blueBox.w2Box.top)+(blueBox.w2Box.inBox?' ✅ IN ZONE':'')+' </div>';
    }
    if (blueBox.w4Box) {
      h += '<div style="font-size:10px;color:'+(blueBox.w4Box.inBox?'#3b82f6':'var(--muted)')+'">W4 Zone: '+fp(blueBox.w4Box.bottom)+' – '+fp(blueBox.w4Box.top)+(blueBox.w4Box.inBox?' ✅ IN ZONE':'')+' </div>';
    }
    h += '<div style="font-size:11px;font-weight:700;margin-top:4px;color:'+(blueBox.inAnyBox?'#3b82f6':'var(--muted)')+'">'+blueBox.label+'</div>';
    h += '</div>';
  }

  // Wave Symmetry
  h += '<div style="padding:8px;border-radius:5px;margin-bottom:8px;background:'+(symmetry.valid?'#22c55e08':'#ef444408')+';border:1px solid '+(symmetry.valid?'#22c55e22':'#ef444422')+'">';
  h += '<div style="font-size:9px;letter-spacing:2px;color:var(--muted);margin-bottom:4px">📐 WAVE SYMMETRY</div>';
  h += '<div class="sbar"><div class="sfill" style="width:'+symmetry.score.toFixed(0)+'%;background:'+(symmetry.score>=80?'var(--green)':symmetry.score>=60?'var(--gold)':'var(--red)')+'"></div></div>';
  h += '<div style="margin-top:4px">';
  for (var si=0;si<symmetry.details.length;si++) {
    var sd=symmetry.details[si];
    h += '<div style="font-size:9px;color:'+(sd.ok?'var(--green)':'var(--red)')+';margin-top:2px">'+(sd.ok?'✅':'❌')+' '+sd.label+': '+sd.detail+'</div>';
  }
  h += '</div>';
  h += '<div style="font-size:10px;color:'+(symmetry.valid?'var(--green)':'var(--red)')+';margin-top:4px;font-weight:700">'+symmetry.note+' ('+symmetry.score.toFixed(0)+'%)</div>';
  h += '</div>';

  // SMI
  h += '<div style="padding:8px;border-radius:5px;margin-bottom:8px;background:'+(smi<-40?'#22c55e08':smi>40?'#ef444408':'#0d142188')+';border:1px solid '+(smi<-40?'#22c55e22':smi>40?'#ef444422':'#1e293b')+'">';
  h += '<div style="font-size:9px;letter-spacing:2px;color:var(--muted);margin-bottom:4px">📊 STOCHASTIC MOMENTUM INDEX</div>';
  h += '<div style="display:flex;align-items:center;gap:8px">';
  h += '<div style="flex:1;height:6px;border-radius:3px;background:var(--bg3);overflow:hidden"><div style="height:100%;width:'+Math.min(100,Math.max(0,(smi+100)/2)).toFixed(0)+'%;background:'+(smi<-40?'var(--green)':smi>40?'var(--red)':'var(--orange)')+'"></div></div>';
  h += '<span style="font-size:11px;font-weight:900;color:'+(smi<-40?'var(--green)':smi>40?'var(--red)':'var(--orange)')+'">'+smi.toFixed(1)+(smi<-40?' ✅ Oversold':smi>40?' ⚠️ Overbought':' Neutral')+'</span>';
  h += '</div></div>';

  // Truncated W5
  if (truncW5.detected) {
    h += '<div style="padding:8px;border-radius:5px;margin-bottom:8px;background:#f0b42911;border:1px solid #f0b42933">';
    h += '<div style="font-size:9px;letter-spacing:2px;color:var(--muted);margin-bottom:4px">⚠️ TRUNCATED WAVE 5</div>';
    h += '<div style="font-size:11px;color:var(--gold)">'+truncW5.note+'</div>';
    h += '<div style="font-size:9px;color:var(--muted);margin-top:3px">W3 peak: '+fp(truncW5.w3_price)+' · W5 peak: '+fp(truncW5.w5_price)+'</div>';
    if (truncW5.strong) h += '<div style="font-size:10px;color:var(--red);margin-top:4px;font-weight:700">🚨 Do NOT enter — Major reversal expected</div>';
    h += '</div>';
  }

  // WXYXZ display — highest confidence signal
  if (wxyxzResult.detected) {
    var wxColor = wxyxzResult.bothEqual ? 'var(--green)' : 'var(--gold)';
    var wxBg = wxyxzResult.bothEqual ? '#22c55e11' : '#f0b42911';
    var wxBorder = wxyxzResult.bothEqual ? '#22c55e33' : '#f0b42933';
    h += '<div style="padding:10px;border-radius:6px;margin-bottom:8px;background:'+wxBg+';border:2px solid '+wxBorder+'">';
    h += '<div style="font-size:9px;letter-spacing:2px;color:var(--muted);margin-bottom:4px">🔥 W-X-Y-X-Z TRIPLE COMBINATION</div>';
    h += '<div style="font-size:11px;font-weight:700;color:'+wxColor+'">'+wxyxzResult.label+'</div>';
    h += '<div style="font-size:9px;color:var(--muted);margin-top:4px">X1 price: '+wxyxzResult.priceRatio.toFixed(0)+'% of X2 | Time: '+wxyxzResult.timeRatio.toFixed(0)+'%</div>';
    h += '<div style="font-size:9px;color:'+wxColor+';margin-top:3px">Z wave target: '+fp(wxyxzResult.zPrice)+(wxyxzResult.nearZ?' — ✅ IN ZONE NOW':'')+' </div>';
    if (wxyxzResult.bothEqual) h += '<div style="font-size:10px;color:var(--green);font-weight:700;margin-top:4px">🔥🔥 HIGHEST CONFIDENCE — X1=X2 Price+Time Confirmed</div>';
    h += '</div>';
  }

  // C=A Zone display
  h += '<div style="padding:8px;border-radius:5px;margin-bottom:8px;background:'+(caResult.inZone?'#22c55e08':'#0d142188')+';border:1px solid '+(caResult.inZone?'#22c55e22':'#1e293b')+'">';
  h += '<div style="font-size:9px;letter-spacing:2px;color:var(--muted);margin-bottom:4px">🎯 C=A EQUALITY RULE</div>';
  h += '<div style="font-size:11px;color:'+(caResult.inZone?'var(--green)':'var(--muted)')+'">'+caResult.label+'</div>';
  if (caResult.target > 0) h += '<div style="font-size:9px;color:var(--muted);margin-top:3px">C=A target: '+fp(caResult.target)+' | '+caResult.ratio.toFixed(0)+'% complete</div>';
  h += '</div>';



  h += '</div>';

  h+='<div class="card"><div class="ct">YOUR WAVE STRUCTURE</div><div style="font-size:10px;color:var(--muted);line-height:2"><div>Grand: W1($0.01→$69K) W2($69K→$15.4K) W3($15.4K→ongoing)</div><div>W3: W1ofW3($15.4K→$126.2K) W2ofW3(correcting)</div><div>W2ofW3: A($126.2K→$74.5K) B($74.5K→$95.8K) C(unfolding)</div><div style="margin-top:4px;color:var(--sub)">Re-entry: Miss W2? Wait for W4 (23–38% retrace of W3)</div></div></div>';

  show(h);

  setTimeout(function(){
    drawPrice(prices,highs,lows,waves,sl,[tp1,tp2,tp3,tp4]);
    drawRSI(prices);
    drawMACD(macdRes.histLine);
    drawStoch(prices);
    drawSMI(smiFull);
    drawVol(volData);
  },50);
}

// ── CHARTS ─────────────────────────────────────────────────────
function makeCanvas(id,H){
  var c=document.getElementById(id);if(!c)return null;
  var ctx=c.getContext('2d'),dpr=window.devicePixelRatio||1,W=c.offsetWidth;
  c.width=W*dpr;c.height=H*dpr;c.style.height=H+'px';ctx.scale(dpr,dpr);
  ctx.fillStyle='#080c14';ctx.fillRect(0,0,W,H);
  return{ctx:ctx,W:W,H:H};
}

function drawPrice(prices,highs,lows,waves,sl,tps){
  var cv=makeCanvas('priceChart',280);if(!cv)return;
  var ctx=cv.ctx,W=cv.W,H=cv.H;
  var P={t:16,r:55,b:24,l:58},cW=W-P.l-P.r,cH=H-P.t-P.b;
  var mn=Math.min.apply(null,lows)*0.97,mx=Math.max.apply(null,highs)*1.03,rng=mx-mn||1;
  function xS(i){return P.l+(i/(prices.length-1))*cW;}
  function yS(p){return P.t+cH-((p-mn)/rng)*cH;}

  for(var i=0;i<=5;i++){var y=P.t+(i/5)*cH,pr=mx-(i/5)*rng;ctx.strokeStyle='#1e293b';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(P.l,y);ctx.lineTo(P.l+cW,y);ctx.stroke();ctx.fillStyle='#475569';ctx.font='9px monospace';ctx.textAlign='right';ctx.fillText(fp(pr),P.l-3,y+3);}
  var step=Math.max(1,Math.floor(priceData.length/5));
  for(i=0;i<priceData.length;i+=step){var d=priceData[i].date;var lbl=mode==='scalp'?d.toLocaleDateString('en-US',{month:'short',day:'numeric'}):d.toLocaleDateString('en-US',{month:'short',year:'2-digit'});ctx.fillStyle='#334155';ctx.font='8px monospace';ctx.textAlign='center';ctx.fillText(lbl,xS(i),H-4);}

  // SL
  var slY=yS(sl);if(slY>=P.t&&slY<=P.t+cH){ctx.strokeStyle='#ef444466';ctx.lineWidth=1;ctx.setLineDash([4,3]);ctx.beginPath();ctx.moveTo(P.l,slY);ctx.lineTo(P.l+cW,slY);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#ef4444';ctx.font='bold 8px monospace';ctx.textAlign='left';ctx.fillText('SL',P.l+cW+2,slY+3);}
  var tpLabels=['TP1','TP2','TP3','TP4'];
  for(var t=0;t<tps.length;t++){var tpY=yS(tps[t]);if(tpY<P.t||tpY>P.t+cH)continue;ctx.strokeStyle='#22c55e44';ctx.lineWidth=0.8;ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(P.l,tpY);ctx.lineTo(P.l+cW,tpY);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#22c55e';ctx.font='bold 8px monospace';ctx.textAlign='left';ctx.fillText(tpLabels[t],P.l+cW+2,tpY+3);}

  // Area
  var gr=ctx.createLinearGradient(0,P.t,0,P.t+cH);gr.addColorStop(0,'rgba(240,180,41,0.18)');gr.addColorStop(1,'rgba(240,180,41,0.01)');
  ctx.beginPath();for(i=0;i<prices.length;i++){i===0?ctx.moveTo(xS(i),yS(prices[i])):ctx.lineTo(xS(i),yS(prices[i]));}
  ctx.lineTo(xS(prices.length-1),P.t+cH);ctx.lineTo(xS(0),P.t+cH);ctx.closePath();ctx.fillStyle=gr;ctx.fill();
  ctx.beginPath();ctx.strokeStyle='#f0b429';ctx.lineWidth=2;for(i=0;i<prices.length;i++){i===0?ctx.moveTo(xS(i),yS(prices[i])):ctx.lineTo(xS(i),yS(prices[i]));}ctx.stroke();

  // Waves
  if(waves.length>1){ctx.beginPath();ctx.strokeStyle='rgba(240,180,41,0.4)';ctx.lineWidth=1;ctx.setLineDash([3,3]);for(i=0;i<waves.length;i++){i===0?ctx.moveTo(xS(waves[i].idx),yS(waves[i].price)):ctx.lineTo(xS(waves[i].idx),yS(waves[i].price));}ctx.stroke();ctx.setLineDash([]);}
  for(i=0;i<waves.length;i++){var w=waves[i],x=xS(w.idx),y=yS(w.price),top=w.type==='peak',off=top?-22:22;ctx.beginPath();ctx.arc(x,y,4,0,Math.PI*2);ctx.fillStyle=w.color;ctx.fill();ctx.fillStyle=w.color;ctx.fillRect(x-17,y+off-9,34,16);ctx.fillStyle='#000';ctx.font='bold 8px monospace';ctx.textAlign='center';ctx.fillText(w.label,x,y+off+3);ctx.fillStyle=w.color;ctx.font='7px monospace';ctx.fillText(fp(w.price),x,y+off+(top?-13:19));}
}

function drawRSI(prices){
  var cv=makeCanvas('rsiChart',65);if(!cv)return;
  var ctx=cv.ctx,W=cv.W,H=cv.H,P={t:4,r:40,b:16,l:48},cW=W-P.l-P.r,cH=H-P.t-P.b;
  var vals=[],i;for(i=14;i<prices.length;i++)vals.push(calcRSI(prices.slice(0,i+1)));
  if(!vals.length)return;
  ctx.fillStyle='#ef444408';ctx.fillRect(P.l,P.t,cW,cH*(1-70/100));
  ctx.fillStyle='#22c55e08';ctx.fillRect(P.l,P.t+cH*(1-30/100),cW,cH*30/100);
  [30,50,70].forEach(function(v){var y=P.t+cH*(1-v/100);ctx.strokeStyle='#1e293b';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(P.l,y);ctx.lineTo(P.l+cW,y);ctx.stroke();ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';ctx.fillText(v,P.l-3,y+3);});
  function xS(i){return P.l+(i/(vals.length-1))*cW;}function yS(v){return P.t+cH*(1-v/100);}
  ctx.beginPath();ctx.strokeStyle='#f97316';ctx.lineWidth=1.5;for(i=0;i<vals.length;i++){i===0?ctx.moveTo(xS(i),yS(vals[i])):ctx.lineTo(xS(i),yS(vals[i]));}ctx.stroke();
  var last=vals[vals.length-1];ctx.fillStyle=last<30?'#22c55e':last>70?'#ef4444':'#f97316';ctx.font='bold 9px monospace';ctx.textAlign='left';ctx.fillText('RSI '+last.toFixed(1),P.l+cW+2,P.t+cH/2+3);
  ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';ctx.fillText('RSI',P.l-3,P.t+8);
}

function drawMACD(hist){
  var cv=makeCanvas('macdChart',65);if(!cv||!hist||!hist.length)return;
  var ctx=cv.ctx,W=cv.W,H=cv.H,P={t:4,r:40,b:16,l:48},cW=W-P.l-P.r,cH=H-P.t-P.b;
  var mx=Math.max.apply(null,hist.map(Math.abs))*1.1||1,yMid=P.t+cH/2,i;
  function xS(i){return P.l+(i/(hist.length-1))*cW;}function yS(v){return yMid-(v/mx)*(cH/2);}
  ctx.strokeStyle='#334155';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(P.l,yMid);ctx.lineTo(P.l+cW,yMid);ctx.stroke();
  var bw=Math.max(1,cW/hist.length-0.5);
  for(i=0;i<hist.length;i++){var x=xS(i),y=yS(hist[i]);ctx.fillStyle=hist[i]>=0?'#22c55e66':'#ef444466';ctx.fillRect(x-bw/2,Math.min(y,yMid),bw,Math.abs(y-yMid));}
  var last=hist[hist.length-1]||0;ctx.fillStyle=last>=0?'#22c55e':'#ef4444';ctx.font='bold 9px monospace';ctx.textAlign='left';ctx.fillText('MACD',P.l+cW+2,P.t+cH/2+3);
  ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';ctx.fillText('MACD',P.l-3,P.t+8);
}

function drawStoch(prices){
  var cv=makeCanvas('stochChart',65);if(!cv)return;
  var ctx=cv.ctx,W=cv.W,H=cv.H,P={t:4,r:40,b:16,l:48},cW=W-P.l-P.r,cH=H-P.t-P.b;
  var vals=[],i,period=14;
  for(i=period;i<=prices.length;i++){
    var sl=prices.slice(i-period,i);
    var high=Math.max.apply(null,sl),low=Math.min.apply(null,sl);
    vals.push(high===low?50:((prices[i-1]-low)/(high-low))*100);
  }
  if(!vals.length)return;
  ctx.fillStyle='#22c55e08';ctx.fillRect(P.l,P.t+cH*0.8,cW,cH*0.2);
  ctx.fillStyle='#ef444408';ctx.fillRect(P.l,P.t,cW,cH*0.2);
  [20,50,80].forEach(function(v){var y=P.t+cH*(1-v/100);ctx.strokeStyle='#1e293b';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(P.l,y);ctx.lineTo(P.l+cW,y);ctx.stroke();ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';ctx.fillText(v,P.l-3,y+3);});
  function xS(i){return P.l+(i/(vals.length-1))*cW;}function yS(v){return P.t+cH*(1-v/100);}
  ctx.beginPath();ctx.strokeStyle='#a855f7';ctx.lineWidth=1.5;for(i=0;i<vals.length;i++){i===0?ctx.moveTo(xS(i),yS(vals[i])):ctx.lineTo(xS(i),yS(vals[i]));}ctx.stroke();
  var last=vals[vals.length-1];ctx.fillStyle=last<20?'#22c55e':last>80?'#ef4444':'#a855f7';ctx.font='bold 9px monospace';ctx.textAlign='left';ctx.fillText('STOCH '+last.toFixed(0),P.l+cW+2,P.t+cH/2+3);
  ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';ctx.fillText('STOCH',P.l-3,P.t+8);
}

function drawSMI(vals){
  var cv=makeCanvas('smiChart',65);if(!cv||!vals||!vals.length)return;
  var ctx=cv.ctx,W=cv.W,H=cv.H,P={t:4,r:40,b:16,l:48},cW=W-P.l-P.r,cH=H-P.t-P.b;
  var mn=-100,mx=100,mid=P.t+cH/2,i;
  function xS(i){return P.l+(i/(vals.length-1))*cW;}
  function yS(v){return P.t+cH/2-(v/100)*(cH/2);}
  // Zones
  ctx.fillStyle='#22c55e08';ctx.fillRect(P.l,P.t+cH*0.7,cW,cH*0.3);
  ctx.fillStyle='#ef444408';ctx.fillRect(P.l,P.t,cW,cH*0.3);
  // Lines
  [-40,0,40].forEach(function(v){
    var y=yS(v);
    ctx.strokeStyle='#1e293b';ctx.lineWidth=0.5;
    ctx.beginPath();ctx.moveTo(P.l,y);ctx.lineTo(P.l+cW,y);ctx.stroke();
    ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';
    ctx.fillText(v,P.l-3,y+3);
  });
  // Line
  ctx.beginPath();ctx.strokeStyle='#06b6d4';ctx.lineWidth=1.5;
  for(i=0;i<vals.length;i++){i===0?ctx.moveTo(xS(i),yS(vals[i])):ctx.lineTo(xS(i),yS(vals[i]));}
  ctx.stroke();
  var last=vals[vals.length-1]||0;
  ctx.fillStyle=last<-40?'#22c55e':last>40?'#ef4444':'#06b6d4';
  ctx.font='bold 9px monospace';ctx.textAlign='left';
  ctx.fillText('SMI '+last.toFixed(0),P.l+cW+2,P.t+cH/2+3);
  ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';
  ctx.fillText('SMI',P.l-3,P.t+8);
}

function drawVol(vols){
  var cv=makeCanvas('volChart',50);if(!cv||!vols.length)return;
  var ctx=cv.ctx,W=cv.W,H=cv.H,P={t:4,r:40,b:16,l:48},cW=W-P.l-P.r,cH=H-P.t-P.b;
  var maxV=Math.max.apply(null,vols)||1,bw=Math.max(1,cW/vols.length-0.5),i;
  for(i=0;i<vols.length;i++){var x=P.l+(i/(vols.length-1))*cW,hh=(vols[i]/maxV)*cH,up=i>0&&priceData[i]&&priceData[i-1]&&priceData[i].price>=priceData[i-1].price;ctx.fillStyle=up?'#22c55e44':'#ef444444';ctx.fillRect(x-bw/2,P.t+cH-hh,bw,hh);}
  ctx.fillStyle='#475569';ctx.font='8px monospace';ctx.textAlign='right';ctx.fillText('VOL',P.l-3,P.t+8);
}

// ── WIRE BUTTONS ───────────────────────────────────────────────
document.getElementById('gobtn').onclick = function(){doSearch();};
document.getElementById('btn-btc').onclick = function(){loadSym('BTC');};
document.getElementById('btn-xrp').onclick = function(){loadSym('XRP');};
document.getElementById('btn-eth').onclick = function(){loadSym('ETH');};
document.getElementById('btn-sol').onclick = function(){loadSym('SOL');};
document.getElementById('btn-bnb').onclick = function(){loadSym('BNB');};
document.getElementById('btn-ada').onclick = function(){loadSym('ADA');};
document.getElementById('m-swing').onclick = function(){setMode('swing');};
document.getElementById('m-scalp').onclick = function(){setMode('scalp');};
document.getElementById('tf-30').onclick = function(){days=30;setTF(30,'tf-30');};
document.getElementById('tf-90').onclick = function(){days=90;setTF(90,'tf-90');};
document.getElementById('tf-180').onclick = function(){days=180;setTF(180,'tf-180');};
document.getElementById('tf-365').onclick = function(){days=365;setTF(365,'tf-365');};
document.getElementById('tf-730').onclick = function(){days=730;setTF(730,'tf-730');};
document.getElementById('tf-max').onclick = function(){days=1000;setTF(1000,'tf-max');};
document.getElementById('inp').onkeypress = function(e){if(e.key==='Enter')doSearch();};

// Auto-load BTC
loadSym('BTC');
</script>
</body>
</html>
