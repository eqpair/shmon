const LIVE_URL = "./web/live.json";
const REFRESH_MS = 30_000;

const fmt = new Intl.NumberFormat("ko-KR");
const n = x => fmt.format(Math.round(Number(x) || 0));
const pct = x => {
    const v = Number(x) || 0;
    return (v >= 0 ? "+" : "") + (v * 100).toFixed(2) + "%";
};
const pClass = v => v >= 0 ? "profit-plus" : "profit-minus";

async function load() {
    const res = await fetch(`${LIVE_URL}?t=${Date.now()}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
    const data = await res.json();
    render(data);
}

function render(data) {
    // Header
    document.getElementById("lastUpdated").textContent = data.as_of || "-";
    document.getElementById("totalExposure").textContent = "₩" + n(data.total_exposure);

    const totalPnL = document.getElementById("totalPnL");
    totalPnL.textContent = "₩" + n(data.total_pnl);
    totalPnL.className = data.total_pnl >= 0 ? "profit-plus" : "profit-minus";

    // Table
    const tbody = document.getElementById("report-body");
    tbody.innerHTML = "";

    for (const p of (data.positions || [])) {
        const pnl = Number(p.pnl) || 0;
        const ratio = Number(p.pnl_ratio) || 0;

        const tr = document.createElement("tr");
        const cost = p.avg_price * p.qty;

        tr.innerHTML = `
  <td class="px-3 py-2 text-left">${p.name}</td>
  <td class="px-3 py-2">${p.side}</td>
  <td class="px-3 py-2">${p.qty.toLocaleString()}</td>
  <td class="px-3 py-2">${p.avg_price.toLocaleString()}</td>
  <td class="px-3 py-2">${cost.toLocaleString()}</td>
  <td class="px-3 py-2 font-bold text-green-600">${p.last_price.toLocaleString()}</td> <!-- 🔹 초록색 굵게 -->
  <td class="px-3 py-2">${p.mv.toLocaleString()}</td>
  <td class="px-3 py-2 ${p.pnl >= 0 ? 'text-blue-600 font-bold' : 'text-red-600 font-bold'}">${p.pnl.toFixed(0).toLocaleString()}</td>
  <td class="px-3 py-2 ${p.pnl_ratio >= 0 ? 'text-blue-600 font-bold' : 'text-red-600 font-bold'}">${(p.pnl_ratio * 100).toFixed(2)}%</td>
`;


        tbody.appendChild(tr);
    }
}

load().catch(err => {
    document.getElementById("report-body").innerHTML =
        `<tr><td colspan="8" style="text-align:center;color:#dc2626;">데이터 로드 실패: ${String(err)}</td></tr>`;
});
setInterval(() => { load().catch(console.error); }, REFRESH_MS);
