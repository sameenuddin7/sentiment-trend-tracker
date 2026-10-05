// D3.js line chart. Reads SENTIMENT_DATA (defined above by sentiment_tracker.py).
(function () {
  const GREEN = "#1b8a5a", RED = "#c93a2f";
  let mode = "monthly";
  const tip = d3.select("#tooltip");

  function draw() {
    const rows = SENTIMENT_DATA[mode].map(d => ({ ...d, date: d3.isoParse(d.start) }));
    const host = document.getElementById("chart");
    host.innerHTML = "";
    const W = host.clientWidth || 800, H = Math.max(320, Math.min(460, W * 0.5));
    const m = { top: 20, right: 24, bottom: 40, left: 52 };
    const iw = W - m.left - m.right, ih = H - m.top - m.bottom;

    const svg = d3.select(host).append("svg").attr("width", W).attr("height", H)
      .attr("role", "img").attr("aria-label", "Average sentiment over time");
    const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

    const x = d3.scaleTime().domain(d3.extent(rows, d => d.date)).range([0, iw]);
    const ext = d3.extent(rows, d => d.avg), pad = 0.4;
    const y = d3.scaleLinear().domain([Math.min(ext[0], 0) - pad, Math.max(ext[1], 0) + pad]).range([ih, 0]);

    g.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(6).tickSize(-iw).tickFormat(""));
    g.append("g").attr("class", "axis").attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).ticks(mode === "monthly" ? rows.length : 8)
        .tickFormat(d3.timeFormat(mode === "monthly" ? "%b %y" : "%d %b")));
    g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(6));
    g.append("text").attr("class", "ylabel").attr("transform", "rotate(-90)")
      .attr("x", -ih / 2).attr("y", -38).attr("text-anchor", "middle").text("Average sentiment score");

    // Neutral baseline
    g.append("line").attr("class", "zero").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0));

    // Line coloured green above 0 and red below 0 via a hard-stop gradient
    const off = Math.min(1, Math.max(0, y(0) / ih));
    const grad = svg.append("defs").append("linearGradient").attr("id", "signGrad")
      .attr("gradientUnits", "userSpaceOnUse").attr("x1", 0).attr("x2", 0).attr("y1", 0).attr("y2", ih);
    [[0, GREEN], [off, GREEN], [off, RED], [1, RED]].forEach(([o, c]) =>
      grad.append("stop").attr("offset", o).attr("stop-color", c));

    g.append("path").datum(rows).attr("fill", "none").attr("stroke", "url(#signGrad)")
      .attr("stroke-width", 2.5).attr("stroke-linejoin", "round")
      .attr("d", d3.line().x(d => x(d.date)).y(d => y(d.avg)).curve(d3.curveMonotoneX));

    // Outlier rings
    g.selectAll(".ring").data(rows.filter(d => d.outlier)).join("circle").attr("class", "ring")
      .attr("cx", d => x(d.date)).attr("cy", d => y(d.avg)).attr("r", 10)
      .attr("fill", "none").attr("stroke", RED).attr("stroke-width", 1.5).attr("stroke-dasharray", "3 2");

    // Points + tooltip
    g.selectAll(".pt").data(rows).join("circle").attr("class", "pt")
      .attr("cx", d => x(d.date)).attr("cy", d => y(d.avg)).attr("r", mode === "monthly" ? 5 : 3.5)
      .attr("fill", d => d.avg >= 0 ? GREEN : RED).attr("stroke", "#fff").attr("stroke-width", 1.5)
      .attr("tabindex", 0)
      .on("mousemove focus", (ev, d) => {
        const box = host.getBoundingClientRect();
        const px = ev.clientX ? ev.clientX - box.left : x(d.date) + m.left;
        const py = ev.clientY ? ev.clientY - box.top : y(d.avg) + m.top;
        tip.style("opacity", 1).style("left", Math.min(px + 14, W - 190) + "px").style("top", py - 10 + "px")
          .html(`<b>${d.period}</b><br>Average: <b style="color:${d.avg >= 0 ? GREEN : RED}">${d.avg.toFixed(2)}</b>` +
            `<br>${d.count} reviews<br>z-score: ${d.z}` + (d.outlier ? `<br><b style="color:${RED}">Unusually negative period</b>` : ""));
      })
      .on("mouseleave blur", () => tip.style("opacity", 0));

    // Outlier labels
    g.selectAll(".olabel").data(rows.filter(d => d.outlier)).join("text").attr("class", "olabel")
      .attr("x", d => x(d.date)).attr("y", d => y(d.avg) + 24).attr("text-anchor", "middle")
      .attr("fill", RED).text("outlier");

    renderFacts();
  }

  function renderFacts() {
    const s = SENTIMENT_DATA.stats[mode];
    const out = SENTIMENT_DATA[mode].filter(d => d.outlier);
    document.getElementById("facts").innerHTML =
      `<div><dt>Reviews analysed</dt><dd>${SENTIMENT_DATA.totalReviews}</dd></div>` +
      `<div><dt>Mean of period averages</dt><dd>${s.mean.toFixed(2)}</dd></div>` +
      `<div><dt>Outlier rule</dt><dd>z &le; ${s.threshold}</dd></div>`;
    document.getElementById("outliers").innerHTML = out.length
      ? out.map(d => `<li><b>${d.period}</b> averaged ${d.avg.toFixed(2)} across ${d.count} reviews (z = ${d.z})</li>`).join("")
      : "<li>No unusually negative periods found.</li>";
  }

  document.querySelectorAll("[data-mode]").forEach(b => b.addEventListener("click", () => {
    mode = b.dataset.mode;
    document.querySelectorAll("[data-mode]").forEach(x => x.setAttribute("aria-pressed", x === b));
    draw();
  }));
  window.addEventListener("resize", draw);
  draw();
})();
