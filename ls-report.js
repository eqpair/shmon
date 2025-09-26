async function loadData() {
    const res = await fetch("live.json?_=" + Date.now());
    const data = await res.json();

    // 한국시간 변환
    const utcDate = new Date(data.as_of);
    const kstDate = new Date(utcDate.getTime() + 9 * 60 * 60 * 1000);
    document.getElementById("lastUpdated").innerText = kstDate.toLocaleString("ko-KR");

    const tbody = document.getElementById("report-body");
    tbody.innerHTML = "";

    let totalCost = 0;

    data.positions.forEach(p => {
        const cost = Math.round(p.avg_price * p.qty); // 매입금액 정수
        totalCost += cost;

        // DIR 아이콘 (L/S)
        const dirBadge =
            p.side === "LONG"
                ? `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-500 text-white text-xs font-bold">L</span>`
                : `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-red-500 text-white text-xs font-bold">S</span>`;

        const tr = document.createElement("tr");
        tr.innerHTML = `
      <td class="px-3 py-2 text-left">${p.name}</td>
      <td class="px-3 py-2 text-center">${dirBadge}</td>
      <td class="px-3 py-2">${p.qty.toLocaleString()}</td>
      <td class="px-3 py-2">${Math.round(p.avg_price).toLocaleString()}</td>
      <td class="px-3 py-2">${cost.toLocaleString()}</td>
      <td class="px-3 py-2 font-bold text-green-600">${p.last_price.toLocaleString()}</td>
      <td class="px-3 py-2">${p.mv.toLocaleString()}</td>
      <td class="px-3 py-2 ${p.pnl >= 0 ? "text-blue-600 font-bold" : "text-red-600 font-bold"}">${p.pnl.toLocaleString()}</td>
      <td class="px-3 py-2 ${p.pnl_ratio >= 0 ? "text-blue-600 font-bold" : "text-red-600 font-bold"}">${(p.pnl_ratio * 100).toFixed(2)}%</td>
    `;
        tbody.appendChild(tr);
    });

    // 합계 반영
    document.getElementById("totalExposure").innerText = data.total_exposure.toLocaleString();
    document.getElementById("totalPnL").innerText =
        (data.total_pnl >= 0 ? "+" : "") + data.total_pnl.toLocaleString();
    document.getElementById("totalPnL").className =
        data.total_pnl >= 0 ? "text-blue-600 font-bold" : "text-red-600 font-bold";
}

loadData();
setInterval(loadData, 30000); // 30초마다 갱신
