// web/app.js — LS Position Monitor (static, GitHub Pages)
// live.json을 주기적으로 읽어 KPI/섹션 테이블을 렌더합니다.

const LIVE_URL = "./live.json";   // GitHub Pages에선 같은 경로로 호스팅됨

// 숫자 포매터
const fmt = new Intl.NumberFormat("ko-KR");
const n = x => fmt.format(Math.round(Number(x) || 0));
const pct = x => {
  const v = Number(x) || 0;
  return (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%";
};

// 그룹명을 DOM id로 안전하게 변환 (공백/한글/특수문자 → '_')
function safeId(text) {
  return "rows-" + String(text)
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/gi, "_");
}

// 30초마다 새로고침
const REFRESH_MS = 30_000;

async function loadOnce() {
  // 캐시 우회를 위해 쿼리 파라미터 추가
  const res = await fetch(`${LIVE_URL}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
  const data = await res.json();
  render(data);
}

function render(data) {
  try {
    // 요약 KPI
    const sumEl = document.getElementById("summary");
    const cls = data.total_pnl >= 0 ? "gain" : "loss";
    sumEl.innerHTML = `
      <div class="flex flex-wrap items-center gap-6">
        <div class="text-sm text-gray-500">총 L/S 손익</div>
        <div class="text-2xl font-bold num ${cls}">${n(data.total_pnl)}</div>
        <div class="text-sm text-gray-500">총 EXPOSURE</div>
        <div class="text-xl font-bold num">${n(data.total_exposure)}</div>
        <div class="chip num ${cls}">${pct(data.total_pnl_ratio)}</div>
      </div>
    `;

    // 푸터
    const asOfEl = document.getElementById("asOf");
    const ccyEl = document.getElementById("ccy");
    if (asOfEl) asOfEl.textContent = data.as_of || "-";
    if (ccyEl) ccyEl.textContent = data.currency || "-";

    // 섹션(그룹) 묶기
    const byGroup = {};
    for (const p of data.positions || []) {
      const g = p.group || p.symbol;
      (byGroup[g] ??= []).push(p);
    }

    // 렌더 컨테이너
    const container = document.getElementById("sections");
    container.innerHTML = "";

    Object.entries(byGroup).forEach(([group, items]) => {
      // 그룹 합계
      let mvSum = 0, pnlSum = 0;
      for (const p of items) { mvSum += Number(p.mv) || 0; pnlSum += Number(p.pnl) || 0; }
      const ratio = mvSum !== 0 ? pnlSum / Math.abs(mvSum) : 0;
      const grpCls = pnlSum >= 0 ? "gain" : "loss";

      // 섹션 프레임
      const section = document.createElement("div");
      section.className = "section";
      const rowsId = safeId(group);
      section.innerHTML = `
        <div class="flex items-center justify-between mb-2">
          <div class="font-semibold">${group}</div>
          <div class="flex items-center gap-3">
            <span class="num ${grpCls}">${pct(ratio)}</span>
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
          <div id="${rowsId}"></div>
        </div>
      `;

      // 항목 렌더
      const rows = section.querySelector(`#${rowsId}`);
      for (const p of items) {
        const rowCls = (Number(p.pnl) || 0) >= 0 ? "gain" : "loss";
        const sideChip = (p.side || "").toUpperCase() === "SHORT"
          ? `<span class="chip border-red-300 text-red-600">SHORT</span>`
          : `<span class="chip border-green-300 text-green-600">LONG</span>`;
        const ratio = (Number(p.mv) || 0) !== 0 ? (Number(p.pnl) || 0) / Math.abs(Number(p.mv) || 0) : 0;

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
          <div class="text-right num ${rowCls}">${pct(ratio)}</div>
        `;
        rows.appendChild(row);
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
  loadOnce().catch(err => {
    console.error("auto-refresh error:", err);
  });
}, REFRESH_MS);
