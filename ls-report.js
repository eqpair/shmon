// live.json 경로: 루트 index.html + web/ 아래 live.json일 때
async function loadReport() {
    try {
        const res = await fetch("./web/live.json?_=" + Date.now());
        if (!res.ok) throw new Error("fetch failed: " + res.status);
        const data = await res.json();

        const body = document.getElementById("report-body");
        body.innerHTML = "";

        data.positions.forEach(pos => {
            // 숫자 보정
            const avg = Number(pos.avg_price) || 0;
            const qty = Number(pos.qty) || 0;
            const last = Number(pos.last_price) || 0;

            // 🔁 프론트에서 재계산 (서버 값 신뢰하지 않음)
            const cost = avg * qty;        // 매입금액
            const mv = last * qty;       // 평가금액
            const pnl = mv - cost;        // 손익 (LONG 기준; SHORT면 서버에서 last가 음수 아님 -> 여기선 일괄 계산)
            const ratio = cost ? (pnl / cost) : 0;  // 손익률

            // 손익 표기 (정수 + 천단위)
            const pnlFmt = Math.round(pnl).toLocaleString("ko-KR");
            const pnlColor =
                pnl > 0 ? "text-red-600 font-bold"
                    : pnl < 0 ? "text-blue-600 font-bold"
                        : "text-gray-600";

            // 손익률 표기 (소수 1자리)
            const pnlRatioFmt = (ratio * 100).toFixed(1) + "%";
            const pnlRatioColor =
                ratio > 0 ? "text-red-600 font-bold"
                    : ratio < 0 ? "text-blue-600 font-bold"
                        : "text-gray-600";

            // DIR (L/S 표시 - 동그라미 배경) — 기존 디자인 유지 (롱: 초록 원 L)
            const dirBadge = `
        <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-600 font-bold">
          ${String(pos.side || "").startsWith("L") ? "L" : "S"}
        </span>
      `;

            const row = `
        <tr class="border-b">
          <td class="px-2 py-2 text-gray-800 font-medium">${pos.name}</td>
          <td class="px-2 py-2 text-center">${dirBadge}</td>
          <td class="px-2 py-2 text-right">${Math.round(avg).toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right text-green-700 font-bold">${last.toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right">${qty.toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right">${Math.round(cost).toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right">${mv.toLocaleString("ko-KR")}</td>
          <td class="px-2 py-2 text-right ${pnlColor}">${pnlFmt}</td>
          <td class="px-2 py-2 text-right ${pnlRatioColor}">${pnlRatioFmt}</td>
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
            (Number(data.total_exposure) || 0).toLocaleString("ko-KR");

        // Total PnL (+/- 색상 적용, 정수 표기)
        const totalPnL = Number(data.total_pnl) || 0;
        const totalPnLElem = document.getElementById("totalPnL");
        totalPnLElem.textContent =
            (totalPnL > 0 ? "+" : "") + Math.round(totalPnL).toLocaleString("ko-KR");
        totalPnLElem.className =
            totalPnL > 0 ? "text-red-600 font-bold"
                : totalPnL < 0 ? "text-blue-600 font-bold"
                    : "text-gray-600 font-bold";

    } catch (err) {
        console.error(err);
        const body = document.getElementById("report-body");
        body.innerHTML =
            `<tr><td colspan="9" class="text-center text-red-500 py-4">데이터 로드 실패: ${err}</td></tr>`;
    }
} 

// 최초 실행 + 30초마다 갱신
loadReport();
setInterval(loadReport, 30000);
