// web/app.js — Position Monitor (static, GitHub Pages)

const LIVE_URL = "./live.json";
const REFRESH_MS = 30_000;

// 숫자 포매터
const fmt = new Intl.NumberFormat("ko-KR");
const n = x => fmt.format(Math.round(Number(x) || 0));
const pct = x => {
  const v = Number(x) || 0;
  return (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%";
};

async function loadOnce() {
  // 캐시 우회 쿼리로 최신 파일 읽기
  const res = await fetch(`${LIVE_URL}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
  const data = await res.json();
  render(data);
}

function render(data) {
  try {
    // 상단 KPI
    const sumEl = document.getElementById("summary");
    const kpiCls = (Number(data.total_pnl) || 0) >= 0 ? "gain" : "loss";
    sumEl.innerHTML = `
      <div class="flex flex-wrap items-center gap-6">
        <div class="text-sm text-gray-500">총 L/S 손익</div>
        <div class="text-2xl font-bold num ${kpiCls}">${n(data.total_pnl)}</div>
        <div class="text-sm text-gray-500">총 EXPOSURE</div>
        <div class="text-xl font-bold num">${n(data.total_exposure)}</div>
        <div class="chip num ${kpiCls}">${pct(data.total_pnl_ratio)}</div>
      </div>
    `;

    // 푸터
    const asOfEl = document.getElementById("asOf");
    const ccyEl = document.getElementById("ccy");
    if (asOfEl) asOfEl.textContent = data.as_of || "-";
    if (ccyEl) ccyEl.textContent = data.currency || "-";

    // 그룹 묶기
    const byGroup = {};
    for (const p of data.positions || []) {
      const g = p.group || p.symbol;
      (byGroup[g] ??= []).push(p);
    }

    // 섹션 렌더
    const container = document.getElementById("sections");
    container.innerHTML = "";

    Object.entries(byGroup).forEach(([group, items]) => {
      // 그룹 합계
      let mvSum = 0, pnlSum = 0;
      for (const p of items) { mvSum += Number(p.mv) || 0; pnlSum += Number(p.pnl) || 0; }
      const ratio = mvSum !== 0 ? pnlSum / Math.abs(mvSum) : 0;
      const grpCls = pnlSum >= 0 ? "gain" : "loss";

      // 섹션 컨테이너
      const section = document.createElement("div");
      section.className = "section";

      // 섹션 헤더
      const header = document.createElement("div");
      header.className = "flex items-center justify-between mb-2";
      header.innerHTML = `
        <div class="font-semibold">${group}</div>
        <div class="flex items-center gap-3">
          <span class="num ${grpCls}">${pct(ratio)}</span>
          <span class="text-sm text-gray-500 num">${n(pnlSum)}</span>
        </div>
      `;
      section.appendChild(header);

      // 카드 패널
      const panel = document.createElement("div");
      panel.className = "panel";
      section.appendChild(panel);

      // 헤더 행
      const headRow = document.createElement("div");
      headRow.className = "row text-xs text-gray-500 mb-2";
      headRow.innerHTML = `
        <div>종목</div><div>포지션</div><div class="text-right">수량</div>
        <div class="text-right">평단</div><div class="text-right">현재가</div>
        <div class="text-right">평가금액</div><div class="text-right">손익</div>
        <div class="text-right">손익률</div>
      `;
      panel.appendChild(headRow);

      // ----- 여기서부터 id 사용 안 함! -----
      const rowsContainer = document.createElement("div");
      panel.appendChild(rowsContainer);

      // 각 포지션 렌더
      for (const p of items) {
        const rowCls = (Number(p.pnl) || 0) >= 0 ? "gain" : "loss";
        const sideChip = (p.side || "").toUpperCase() === "SHORT"
          ? `<span class="chip border-red-300 text-red-600">SHORT</span>`
          : `<span class="chip border-green-300 text-green-600">LONG</span>`;
        const r = (Number(p.mv) || 0) !== 0 ? (Number(p.pnl) || 0) / Math.abs(Number(p.mv) || 0) : 0;

        const row = document.createElement("div");
        row.className = "row text-sm";
        row.innerHTML = `
          <div>${p.name || p.symbol}</div>
          <div>${sideChip}</div>
          <div class="text-right num">${n(p.qty)}</div>
          <div class="text-right num">${n(p.avg_price)}</div>
          <div class="text-right num">${n(p.last_price)}</div>
          <div class="text-right num">${n(p.mv)}</div>
          <div class="text-right num ${rowCls}">${n(p.pnl)}</div>
          <div class="text-right num ${rowCls}">${pct(r)}</div>
        `;
        rowsContainer.appendChild(row);
      }

      container.appendChild(section);
    });
  } catch (e) {
    console.error(e);
    const el = document.getElementById("summary");
    el.innerHTML = `<div class="panel text-red-600">데이터 렌더 오류: ${String(e)}</div>`;
  }
}

// 최초 로드 + 30초마다 재로딩
loadOnce().catch(err => {
  console.error(err);
  const el = document.getElementById("summary");
  el.innerHTML = `<div class="panel text-red-600">데이터 로드 실패: live.json이 없거나 손상됐습니다.</div>`;
});
setInterval(() => {
  loadOnce().catch(err => console.error("auto-refresh error:", err));
}, REFRESH_MS);
