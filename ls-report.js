async function loadReport() {
    try {
        const res = await fetch("./web/live.json?_=" + Date.now());
        if (!res.ok) throw new Error("fetch failed: " + res.status);
        const data = await res.json();

        const body = document.getElementById("report-body");
        body.innerHTML = "";

        data.positions.forEach(pos => {
            // 매입금액 = qty * avg_price
            const cost = pos.qty * pos.avg_price;

            // 손익 포맷 (소수점 제거 + 천단위 콤마)
            const pnl = pos.pnl.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
            const pnlColor =
                pos.pnl > 0 ? "text-red-600 font-bold"
                    : pos.pnl < 0 ? "text-blue-600 font-bold"
                        : "text-gray-600";

            // 손익률 포맷 (소수점 1자리)
            const pnlRatio = (pos.pnl_ratio * 100).toFixed(1) + "%";
            const pnlRatioColor =
                pos.pnl_ratio > 0 ? "text-red-600 font-bold"
                    : pos.pnl_ratio < 0 ? "text-blue-600 font-bold"
                        : "text-gray-600";

            // DIR (L/S 표시 - 동그라미 배경)
            const dirBadge =
                `<span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-600 font-bold">
          ${pos.side.startsWith("L") ? "L" : "S"}
        </span>`;

            const row = `
        <tr class="border-b">
          <td class="px-2 py-2 text-gray-800 font-medium">${pos.name}</td>
          <td class="px-2 py-2 text-center">${dirBadge}</td>
          <td class="px-2 py-2 text-right">${Math.round(pos.avg_price).toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right text-green-700 font-bold">${pos.last_price.toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right">${pos.qty.toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right">${Math.round(cost).toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right">${pos.mv.toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right ${pnlColor}">${pnl}</td>
          <td class="px-2 py-2 text-right ${pnlRatioColor}">${pnlRatio}</td>
        </tr>
      `;
            body.insertAdjacentHTML("beforeend", row);
        });

        // 업데이트 시각 (한국시간)
        const updated = new Date(data.as_of);
        document.getElementById("lastUpdated").textContent =
            updated.toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });

        // Total Exposure
        document.getElementById("totalExposure").textContent =
            data.total_exposure.toLocaleString("ko-KR");

        // Total PnL (+/- 색상 적용)
        const totalPnL = data.total_pnl;
        const totalPnLElem = document.getElementById("totalPnL");
        totalPnLElem.textContent =
            (totalPnL > 0 ? "+" : "") +
            totalPnL.toLocaleString("ko-KR", { maximumFractionDigits: 0 });

        totalPnLElem.className =
            totalPnL > 0 ? "text-red-600 font-bold"
                : totalPnL < 0 ? "text-blue-600 font-bold"
                    : "text-gray-600 font-bold";

    } catch (err) {
        console.error(err);
        const body = document.getElementById("report-body");
        body.innerHTML = `<tr><td colspan="9" class="text-center text-red-500 py-4">데이터 로드 실패: ${err}</td></tr>`;
    }
}

// 최초 실행 + 30초마다 갱신
loadReport();
setInterval(loadReport, 30000);
