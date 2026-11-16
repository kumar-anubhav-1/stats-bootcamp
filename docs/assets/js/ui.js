/* Interface polish: lesson-meta chips, reading progress bar, completion ticks in the sidebar, path-coloured tabs. */
(function () {
  const S = window.SDSB;
  function chips() {
    document.querySelectorAll("p.lesson-meta:not(.sb-meta)").forEach((p) => {
      const parts = p.innerHTML.split(" · ").map((t) => t.trim()).filter(Boolean);
      p.innerHTML = parts.map((t) => {
        const cls = /^Basic/.test(t) ? "sb-chip sb-chip-b" : /^Leader/.test(t) ? "sb-chip sb-chip-l" : "sb-chip";
        const icon = /^Day/.test(t) ? "📅 " : /^Basic/.test(t) ? "🎓 " : /^Leader/.test(t) ? "🧭 " : /^Prereq/.test(t) ? "🔗 " : /^Recipe/.test(t) ? "🧰 " : "";
        return `<span class="${cls}">${icon}${t}</span>`;
      }).join("");
      p.classList.add("sb-meta");
    });
  }
  function bar() {
    let b = document.getElementById("sb-progress");
    if (!b) { b = document.createElement("div"); b.id = "sb-progress"; document.body.appendChild(b); }
    const upd = () => { const h = document.documentElement.scrollHeight - innerHeight; b.style.width = (h > 0 ? (100 * scrollY) / h : 0) + "%"; };
    window.removeEventListener("scroll", window.__sbBar || (() => {}));
    window.__sbBar = upd; window.addEventListener("scroll", upd, { passive: true }); upd();
  }
  function ticks() {
    document.querySelectorAll(".md-nav__link[href]").forEach((a) => {
      const m = a.getAttribute("href").match(/day-(\d+)\/L(\d+)-(\d+)\/?$/);
      if (m) a.classList.toggle("sb-done", !!S.get(`done.L${+m[2]}.${+m[3]}`, false));
    });
  }
  function tabs() {
    document.querySelectorAll(".tabbed-set").forEach((set) => {
      const labs = set.querySelectorAll(":scope > .tabbed-labels > label");
      const box = set.querySelector(":scope > .tabbed-labels");
      if (!box) return;
      const paint = () => {
        const i = [...set.querySelectorAll(":scope > input")].findIndex((x) => x.checked);
        const t = labs[i] ? labs[i].textContent.trim() : "";
        box.classList.toggle("sb-path-b", t === "Basic → Advanced");
        box.classList.toggle("sb-path-l", t === "Leader");
      };
      labs.forEach((l) => { const t = l.textContent.trim(); if (t === "Basic → Advanced") l.classList.add("sb-tab-b"); if (t === "Leader") l.classList.add("sb-tab-l"); });
      set.querySelectorAll(":scope > input").forEach((x) => x.addEventListener("change", () => setTimeout(paint, 0)));
      paint();
    });
  }
  function run() { chips(); bar(); ticks(); tabs(); document.querySelectorAll(".lesson-done input").forEach((x) => x.addEventListener("change", () => setTimeout(ticks, 50))); }
  S.onPage(() => setTimeout(run, 0));
})();
