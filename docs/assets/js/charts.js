/* Interactive charts: <div class="sb-chart" data-chart="id"> → Plotly figure from assets/data/charts/id.json (Plotly loaded on demand). */
(function () {
  const here = document.currentScript ? document.currentScript.src : "";
  const vendor = here ? new URL("../vendor/plotly.min.js", here).href : "assets/vendor/plotly.min.js";
  let loading = null;
  function plotly() {
    if (window.Plotly) return Promise.resolve(window.Plotly);
    if (!loading) loading = new Promise((ok, no) => { const s = document.createElement("script"); s.src = vendor; s.onload = () => ok(window.Plotly); s.onerror = no; document.head.appendChild(s); });
    return loading;
  }
  function render() {
    const els = document.querySelectorAll(".sb-chart[data-chart]:not([data-done])");
    if (!els.length) return;
    plotly().then((P) => {
      els.forEach((el) => {
        el.setAttribute("data-done", "1");
        window.SDSB.load("charts/" + el.dataset.chart + ".json").then((f) => {
          delete f.layout.template;
          theme(f.layout);
          if (el.clientWidth < 600) {
            const t = (f.layout.title && f.layout.title.text) || "";
            f.layout.title = { text: wrap(t, 46), font: { size: 11 } };
            f.layout.margin = Object.assign({}, f.layout.margin, { t: 30 + 14 * (wrap(t, 46).split("<br>").length) });
            f.config = Object.assign({}, f.config, { displayModeBar: false });
            f.layout.legend = Object.assign({}, f.layout.legend, { orientation: "h", x: 0, y: 1.0, yanchor: "bottom", font: { size: 10 } });
            f.layout.margin.t += 40;
            if (f.layout.sliders) { f.layout.margin = Object.assign({}, f.layout.margin, { b: 175 }); f.layout.sliders.forEach((sl) => { sl.pad = { t: 75 }; sl.currentvalue = Object.assign({}, sl.currentvalue, { font: { size: 11 } }); }); }
          }
          el.__fig = f;
          (f.layout.updatemenus || []).forEach((u) => { if (u.type === "buttons") { u.y = -0.22; u.yanchor = "top"; u.x = 0; u.xanchor = "left"; u.pad = { t: 8 };
            f.layout.margin = Object.assign({}, f.layout.margin, { b: Math.max((f.layout.margin || {}).b || 0, 120) }); } });
          P.newPlot(el, f.data, f.layout, f.config || { responsive: true, displaylogo: false });
          if (el.dataset.caption) { const c = document.createElement("p"); c.className = "sb-chart-caption"; c.textContent = "▲ " + el.dataset.caption; el.after(c); }
        }).catch(() => { el.textContent = "Chart unavailable — run python -m tools.build_site"; });
      });
    });
  }
  function wrap(t, n) { const w = t.split(" "); let line = "", out = []; w.forEach((x) => { if ((line + " " + x).trim().length > n) { out.push(line.trim()); line = x; } else line += " " + x; }); out.push(line.trim()); return out.filter(Boolean).join("<br>"); }
  function theme(lay) {
    const dark = document.body.getAttribute("data-md-color-scheme") === "slate";
    const fg = dark ? "#CBD5E1" : "#0F172A", grid = dark ? "#26304F" : "#E2E8F0";
    lay.paper_bgcolor = "rgba(0,0,0,0)"; lay.plot_bgcolor = "rgba(0,0,0,0)";
    lay.font = Object.assign({}, lay.font, { color: fg, family: "Inter, system-ui, sans-serif" });
    Object.keys(lay).filter((k) => /^[xy]axis\d*$/.test(k)).forEach((k) => { lay[k] = Object.assign({ gridcolor: grid, zerolinecolor: grid, linecolor: grid }, lay[k]); });
    if (!lay.xaxis) lay.xaxis = { gridcolor: grid, zerolinecolor: grid }; if (!lay.yaxis) lay.yaxis = { gridcolor: grid, zerolinecolor: grid };
    if (lay.scene) ["xaxis", "yaxis", "zaxis"].forEach((a) => { lay.scene[a] = Object.assign({}, lay.scene[a], { gridcolor: grid, backgroundcolor: "rgba(0,0,0,0)", color: fg }); });
    if (lay.title && lay.title.font) lay.title.font.color = fg;
  }
  new MutationObserver(() => {
    if (!window.Plotly) return;
    document.querySelectorAll(".sb-chart[data-done]").forEach((el) => { if (el.__fig) { theme(el.__fig.layout); window.Plotly.react(el, el.__fig.data, el.__fig.layout, el.__fig.config); } });
  }).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
  window.SDSB.onPage(render);
})();
