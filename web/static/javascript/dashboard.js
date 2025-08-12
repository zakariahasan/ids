// Combined inline scripts extracted on 2025-08-12 12:11:46 UTC
// Order preserved. Source: dashboard HTML.

// ---- script #1 ----
let autoRefresh = false;
    let refreshInterval = null;

    function toggleAutoRefresh() {
      autoRefresh = !autoRefresh;
      document.getElementById("autoRefreshState").innerText = autoRefresh ? "On" : "Off";
      if (autoRefresh) {
        refreshInterval = setInterval(draw, 10000);
      } else {
        clearInterval(refreshInterval);
      }
    }

    function downloadCSV() {
      const rows = [["Source IP", "Burst Start", "Burst End", "Scans in Burst"]];
      document.querySelectorAll("#burstTable tbody tr").forEach(tr => {
        const cells = Array.from(tr.children).map(td => td.textContent);
        rows.push(cells);
      });
      const csv = rows.map(r => r.join(",")).join("\n");
      const blob = new Blob([csv], { type: "text/csv" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "burst_data.csv";
      link.click();
    }

    function downloadCharts() {
      document.querySelectorAll("canvas").forEach((canvas, i) => {
        const link = document.createElement("a");
        link.download = `chart_${i + 1}.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
      });
    }

    async function loadJSON(url) {
      const r = await fetch(url);
      return r.json();
    }

    async function draw() {
      const hourly        = await loadJSON('/api/dashboard/alerts_by_hour');
      const top           = await loadJSON('/api/dashboard/top_sources');
      const ddos          = await loadJSON('/api/dashboard/ddos_last_10m');
      const bursts        = await loadJSON('/api/dashboard/scan_bursts');
      const hours = Object.keys(hourly).sort();
      const synData = hours.map(h => hourly[h]['SYN'] || 0);
      new Chart(document.getElementById('hourlyChart'), {
  type: 'bar',
  data: { labels: hours, datasets: [
    { label: 'SYN Alerts', data: synData }
  ]},
  options: { plugins: { title: { display: true, text: 'Hourly Alerts (last 24 h)' } },
  scales: {
    y: {
      beginAtZero: true,
      suggestedMax: 10
    }
  } }
});

      new Chart(document.getElementById('topAttackers'), {
        type: 'pie',
        data: {
          labels: top.map(r => r.src_ip), datasets: [{ data: top.map(r => r.total_alerts) }]
        },
        options: { plugins: { title: { display: true, text: 'Top 10 Source IPs' } },
  scales: {
    y: {
      beginAtZero: true,
      suggestedMax: 10
    }
  } }
      });

      const ddosLabels = ddos.map(r => new Date(r.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }));
const ddosVals = ddos.map(r => r.count);
      new Chart(document.getElementById('ddosWindow'), {
        type: 'line',
        data: { labels: ddosLabels, datasets: [{ label: 'DDoS (10-min window)', data: ddosVals, fill: false }] },
        options: { plugins: { title: { display: true, text: 'Rolling 10-Minute DDoS Count' } },
  scales: {
    y: {
      beginAtZero: true,
      suggestedMax: 10
    }
  } }
      });

      const tbody = document.querySelector('#burstTable tbody');
      tbody.innerHTML = '';
      bursts.forEach(b => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${b.src_ip}</td><td>${b.burst_start}</td><td>${b.burst_end}</td><td>${b.scans_in_burst}</td>`;
        tbody.appendChild(tr);
      });

      updateSummary(hourly, pkt_per_hour);
    }

    function updateSummary(hourly, pkt_per_hour) {
      const synTotal = Object.values(hourly).reduce((sum, h) => sum + (h["SYN"] || 0), 0);
      const ddosTotal = Object.values(hourly).reduce((sum, h) => sum + (h["DDoS"] || 0), 0);
      document.querySelector("#summaryPortScan span").innerText = synTotal;
      document.querySelector("#summaryDDoS span").innerText = ddosTotal;
      }

    function toggleTheme() {
      const body = document.body;
      const isDark = body.classList.toggle("dark-mode");
      document.getElementById("toggleTheme").textContent = isDark ? "☀️ Enable Light Mode" : "🌙 Enable Dark Mode";
      localStorage.setItem("theme", isDark ? "dark" : "light");
    }

    (function applySavedTheme() {
      const saved = localStorage.getItem("theme");
      if (saved === "dark") {
        document.body.classList.add("dark-mode");
        document.getElementById("toggleTheme").textContent = "☀️ Enable Light Mode";
      }
    })();
/**
 * Draw a dual-axis chart:
 *   - Bars  : total bytes in last 10 min
 *   - Line  : packet count in last 10 min
 */
document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/dashboard/top_bandwidth')
    .then(r => r.json())
    .then(data => {
      const labels = data.map(d => d.host_ip);
      const bytes  = data.map(d => d.bytes_last_10m);
      const pkts   = data.map(d => d.pkts_last_10m);

      const ctx = document.getElementById('bandwidthChart').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Bytes (last 10 min)',
              data: bytes,
              yAxisID: 'y-bytes',
              borderWidth: 1
            },
            {
              label: 'Packets (last 10 min)',
              data: pkts,
              yAxisID: 'y-pkts',
              type: 'line',
              tension: 0.3,
              fill: false,
              borderWidth: 2,
              pointRadius: 3
            }
          ]
        },
        options: {
          responsive: true,
          interaction: { mode: 'index', intersect: false },
          scales: {
            'y-bytes': {
              position: 'left',
              beginAtZero: true,
              title: { display: true, text: 'Bytes' }
            },
            'y-pkts': {
              position: 'right',
              beginAtZero: true,
              grid: { drawOnChartArea: false },   // keep the two axes visually distinct
              title: { display: true, text: 'Packets' }
            }
          }
        }
      });
    })
    .catch(console.error);
});
/* ─── Chart #2 – average pkt size + total pkts (all-time) ─────────── */
fetch('/api/dashboard/avg_pkt_size')
  .then(r => r.json())
  .then(data => {
    const labels   = data.map(d => d.host_ip);
    const avgSize  = data.map(d => d.avg_pkt_size_bytes);
    const totalPkt = data.map(d => d.total_pkts);

    const ctx = document.getElementById('pktSizeChart').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Avg Pkt Size (bytes)', data: avgSize,  yAxisID: 'y-size', borderWidth: 1 },
          { label: 'Total Packets',        data: totalPkt, yAxisID: 'y-pkts', type: 'line',
            tension: 0.3, fill: false, borderWidth: 2, pointRadius: 3 }
        ]
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        scales: {
          'y-size': { position: 'left',  beginAtZero: true,
                      title:{display:true,text:'Avg Pkt Size (bytes)'} },
          'y-pkts': { position: 'right', beginAtZero: true, grid:{drawOnChartArea:false},
                      title:{display:true,text:'Total Packets'} }
        }
      }
    });
  })
  .catch(console.error);
/* ── Chart #3 – heavy outgoing bias (last hour) ───────────────────── */
fetch('/api/dashboard/heavy_outgoing')
  .then(r => r.json())
  .then(data => {
    const labels   = data.map(d => d.host_ip);
    const inPkts   = data.map(d => d.in_pkts);
    const outPkts  = data.map(d => d.out_pkts);
    const ratio    = data.map(d => d.out_in_ratio);

    new Chart(document.getElementById('heavyOutgoingChart').getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Outgoing Pkts',
            data:  outPkts,
            yAxisID: 'y-pkts',
            backgroundColor: 'rgba(54, 162, 235, 0.65)',    // blue, 65 % opacity
            borderColor:     'rgba(54, 162, 235, 1)',
            borderWidth: 1
          },
          {
            label: 'Incoming Pkts',
            data:  inPkts,
            yAxisID: 'y-pkts',
            backgroundColor: 'rgba(255, 99, 132, 0.55)',    // red, 55 % opacity
            borderColor:     'rgba(255, 99, 132, 1)',
            borderWidth: 1
          },
          {
            label: 'Out/In Ratio',
            data:  ratio,
            yAxisID: 'y-ratio',
            type:  'line',
            tension: 0.35,
            fill:   false,
            borderWidth: 2,
            pointRadius: 4,
            borderDash: [4, 3],                             // dotted line
            borderColor: '#666',
            pointBackgroundColor: '#666'
          }
        ]
      },
      options: {
        responsive: true,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: ctx =>
                ctx.dataset.label === 'Out/In Ratio'
                  ? `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)}×`
                  : `${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString()} pkts`
            }
          },
          legend: { position: 'top' }
        },
        scales: {
          'y-pkts': {
            position: 'left',
            beginAtZero: true,
            title: { display: true, text: 'Packets' }
          },
          'y-ratio': {
            position: 'right',
            beginAtZero: true,
            grid: { drawOnChartArea: false },
            title: { display: true, text: 'Out/In Ratio' }
          }
        }
      }
    });
  })
  .catch(console.error);
/* ── Chart #4 – port fan-out (unique dst ports) ────────────────────── */
fetch('/api/dashboard/port_fanout')
  .then(r => r.json())
  .then(data => {
    const labels = data.map(d => d.host_ip);
    const ports  = data.map(d => d.unique_dst_ports);

    new Chart(document.getElementById('fanoutChart').getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Unique Destination Ports (last 2 h)',
          data: ports,
          backgroundColor: 'rgba(75, 192, 192, 0.65)',
          borderColor:     'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          tooltip: {
            callbacks: {
              label: ctx =>
                `${ctx.parsed.y.toLocaleString()} ports`
            }
          },
          legend: { position: 'top' }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Unique dst ports' }
          }
        }
      }
    });
  })
  .catch(console.error);
 /* ── Chart – new-source spikes (last 12 h) ─────────────────────────── */
fetch('/api/dashboard/new_source_spike')
  .then(r => r.json())
  .then(data => {
    // label = "<host> @ HH:MM"
    const labels = data.map(d => {
      const t = new Date(d.interval_start);
      return `${d.host_ip} @ ${t.getHours().toString().padStart(2,'0')}:${t
        .getMinutes().toString().padStart(2,'0')}`;
    });
    const jumps  = data.map(d => d.new_src_jump);

    new Chart(document.getElementById('srcSpikeChart').getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'New Source IPs vs previous interval',
          data:  jumps,
          backgroundColor: 'rgba(255, 159, 64, 0.65)',   // orange
          borderColor:     'rgba(255, 159, 64, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          tooltip: {
            callbacks: {
              label: ctx =>
                `${ctx.parsed.y.toLocaleString()} new src IPs`
            }
          },
          legend: { position: 'top' }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'New source IPs' }
          }
        }
      }
    });
  })
  .catch(console.error);
/* ── Chart – total pkts every 30 min (all hosts) ─────────────────── */
fetch('/api/dashboard/rolling_pkt_30m_total')
  .then(r => r.json())
  .then(data => {
    const labels = data.map(d => {
		const dt = new Date(d.interval_end);
		return  `${dt.getDate()} ${dt.toLocaleString('default', { month: 'short' })} ` +
				`${dt.getHours().toString().padStart(2,'0')}:` +
				`${dt.getMinutes().toString().padStart(2,'0')}`;
});
    const totals = data.map(d => d.total_pkts);

    new Chart(document.getElementById('rollingPktTotalChart'), {
      type: 'line',
      data: { 
        labels,
        datasets: [{
          label: 'Total packets in previous 30 min',
          data: totals,
          borderColor: '#ff6384',
          backgroundColor: '#ff6384',
          fill: false,
          tension: 0.3,
          pointRadius: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend:  { display: false },
          tooltip: { callbacks: {
            label: ctx => ctx.parsed.y.toLocaleString() + ' pkts'
          }}
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Packets / 30 min' }
          }
        }
      }
    });
  })
  .catch(console.error); 
  
    draw();