/* Interactive Statistics Navigator: <div id="navigator-app"></div>. Deep links: #N-TEST-2G-MEAN */
(function () {
  const S = window.SDSB;
  S.onPage(() => {
    const app = document.getElementById("navigator-app");
    if (!app) return;
    S.load("navigator.json").then((nav) => {
      const nodes = nav.nodes, starts = nav.starts, lessons = nav.lessons;
      let path = [];
      const lessonLink = (l) => (lessons[l] ? `<a href="${S.siteRoot}${lessons[l]}">${l}</a>` : `<span title="built in Step 3">${l}</span>`);
      const list = (xs) => (xs && xs.length ? "<ul>" + xs.map((x) => `<li>${S.esc(x)}</li>`).join("") + "</ul>" : "<p>—</p>");
      function resolve(id) { return starts[id] || id; }
      function render() {
        const cur = path.length ? path[path.length - 1] : "ROOT";
        const n = cur === "ROOT" ? nav.master : nodes[cur];
        const crumbs = ['<a href="#" data-go="-1">Start</a>'].concat(path.map((p, i) => `<a href="#" data-go="${i}">${S.esc(nodes[p].title || nodes[p].t || nodes[p].q)}</a>`)).join(" › ");
        let html = `<div class="nav-crumbs">${crumbs}</div>`;
        if (n.q) {
          html += `<h3>${S.esc(n.q)}</h3><div class="nav-opts">` + n.opts.map((o) => `<button class="md-button nav-opt" data-next="${o.next}">${S.esc(o.label)}</button>`).join("") + "</div>";
        } else {
          html += `<div class="nav-leaf"><div class="nav-node-id">${cur}</div><h3>${S.esc(n.t)}</h3>
            <p><b>Use when:</b> ${S.esc(n.use)}</p>
            <div class="nav-grid"><div><b>Assumptions to check</b>${list(n.check)}</div><div><b>If a check fails</b>${list(n.fail)}</div>
            <div><b>Alternatives worth trying</b>${list(n.alt)}</div><div><b>Common pitfalls</b>${list(n.pit)}</div></div>
            <p><b>Typical business action:</b> ${S.esc(n.act)}</p>
            <p><b>Lessons:</b> ${(n.lessons || []).map(lessonLink).join(", ")}${n.recipe ? ` · <b>Recipe:</b> <code>${n.recipe}</code>` : ""}${n.concepts ? ` · <b>Concepts:</b> ${n.concepts.join(", ")}` : ""}</p>
            ${n.scenarios && n.scenarios.length ? `<p><b>Scenarios:</b> ${n.scenarios.map((s) => S.esc(s)).join(" · ")}</p>` : ""}</div>`;
        }
        if (path.length) html += `<p><button class="md-button" data-back="1">← Back</button> <button class="md-button" data-go="-1">Start over</button></p>`;
        app.innerHTML = html;
        app.querySelectorAll("[data-next]").forEach((b) => (b.onclick = () => { path.push(resolve(b.dataset.next)); history.replaceState(null, "", "#" + path[path.length - 1]); render(); }));
        app.querySelectorAll("[data-go]").forEach((a) => (a.onclick = (e) => { e.preventDefault(); path = path.slice(0, +a.dataset.go + 1); history.replaceState(null, "", path.length ? "#" + path[path.length - 1] : "#"); render(); }));
        const back = app.querySelector("[data-back]");
        if (back) back.onclick = () => { path.pop(); render(); };
      }
      const h = decodeURIComponent(location.hash.slice(1));
      if (h && nodes[h]) path = nav.paths[h] || [h];
      render();
    });
  });
})();
