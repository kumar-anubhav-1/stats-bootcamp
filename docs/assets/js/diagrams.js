/* Mermaid diagrams at natural (readable) size with horizontal scroll, re-rendered on every page (instant navigation safe). */
(function () {
  let n = 0;
  function render() {
    if (!window.mermaid) return;
    const dark = document.body.getAttribute("data-md-color-scheme") === "slate";
    window.mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "loose",
      flowchart: { useMaxWidth: false, htmlLabels: true, padding: 12 }, mindmap: { useMaxWidth: false },
      themeVariables: { fontSize: "15px" } });
    const nodes = [];
    document.querySelectorAll("pre.sbm").forEach((pre) => {
      const wrap = document.createElement("div");
      wrap.className = "sbm-wrap";
      const d = document.createElement("div");
      d.className = "sbm-diagram";
      d.id = "sbm-" + (n++);
      d.textContent = (pre.querySelector("code") || pre).textContent;
      wrap.appendChild(d);
      pre.replaceWith(wrap);
      nodes.push(d);
    });
    if (nodes.length) window.mermaid.run({ nodes }).then(() => {
      nodes.forEach((d) => {
        const w = d.parentElement, svg = d.querySelector("svg");
        if (!svg) return;
        const natural = parseFloat(svg.style.maxWidth) || svg.getBBox().width;
        if (natural > w.clientWidth * 1.15) {
          const h = document.createElement("div"); h.className = "sbm-hint"; h.textContent = "Click the diagram to zoom to full size (scroll sideways); click again to fit.";
          w.appendChild(h);
          d.addEventListener("click", () => w.classList.toggle("natural"));
        }
      });
    }).catch((e) => console.warn("diagram", e));
  }
  if (window.SDSB) window.SDSB.onPage(render); else document.addEventListener("DOMContentLoaded", render);
})();
