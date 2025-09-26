const LIVE_URL = "./live.json";   // GitHub Pages에서 같은 경로

const fmt = new Intl.NumberFormat("ko-KR");
const n = x => fmt.format(Math.round(x));
const pct = x => (x >= 0 ? "+" : "") + (x * 100).toFixed(1) + "%";

async function loadOnce() {
    const res = await fetch(LIVE_URL, { cache: "no-store" });
    const data = await res.json();
    render(data);
}

function render(data) {
    // KPI
    const sum = document.getElementById("summary");
    const cls = data.total_pnl >= 0 ? "gain" : "loss";
    sum.innerHTML = `
    <div class="flex flex-wrap items-center gap-6">
      <div class="text-sm text-gray-500">총 L/S 손익</div>
      <div class="text-2xl font-bold num ${cls}">${n(data.total_pnl)}</div>
      <div class="text-sm text-gray-500">총 EXPOSURE</div>
      <div class="text-xl font-bold num">${n(data.total_exposure)}</div>
      <div class="chip num ${cls}">${pct(data.total_pnl_ratio)}</div>
    </div>
  `;
    document.getElementById("asOf").textContent = data.as_of || "-";
    document.getElementById("ccy").textContent = data.currency || "-";

    // 그룹 묶기
    const byGroup = {};
    for (const p of data.positions) {
        (byGroup[p.group || p.symbol] ??= []).push(p);
    }

    const container = document.getElementById("sections");
    container.innerHTML = "";
    Object.entries(byGroup).forEach(([group, items]) => {
        let mvSum = 0, pnlSum = 0;
        items.forEach(p => { mvSum += p.mv; pnlSum += p.pnl; });
        const ratio = mvSum !== 0 ? pnlSum / Math.abs(mvSum) : 0;
        const cls = pnlSum >= 0 ? "gain" : "loss";

        const section = document.createElement("div");
        section.className = "section";
        section.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <div class="font-semibold">${group}</div>
        <div class="flex items-center gap-3">
          <span class="num ${cls}">${pct(ratio)}</span>
          <span class="text-sm text-gray-500 num">${n(pnlSum)}</span>
        </div>
      </div>
      <div class="panel">
        <div class="row text-xs text-gray-500 mb-2">
          <div>종목</div><div>포지션</div><div class="text-right">수량</div>
          <div class="text-right">평단</div><div class="text-right">현재가</div>
          <div class="text-right">평가금액</div><div class="text-right">손익</div>
          <div class="text-right">손익률</div>
        </div>
        <div id="rows-${group}"></div>
      </div>
    `;

        const rows = section.querySelector(`#rows-${group}`);
        items.forEach(p => {
            const cls = p.pnl >= 0 ? "gain" : "loss";
            const sideChip = p.side === "SHORT"
                ? `<span class="chip border-red-300 text-red-600">SHORT</span>`
                : `<span class="chip border-green-300 text-green-600">LONG</span>`;
            const ratio = p.mv !== 0 ? p.pnl / Math.abs(p.mv) : 0;

            const row = document.createElement("div");
            row.className = "row text-sm";
            row.innerHTML = `
        <div>${p.name || p.symbol}</div>
        <div>${sideChip}</div>
        <div class="text-right num">${n(p.qty)}</div>
        <div class="text-right num">${n(p.avg_price)}</div>
        <div class="text-right num">${n(p.last_price)}</div>
        <div class="text-right num">${n(p.mv)}</div>
        <div class="text-right num ${cls}">${n(p.pnl)}</div>
        <div class="text-right num ${cls}">${pct(ratio)}</div>
      `;
            rows.appendChild(row);
        });

        container.appendChild(section);
    });
}

// 최초 로드 + 30초마다 재로딩
loadOnce().catch(console.error);
setInterval(loadOnce, 30000);
