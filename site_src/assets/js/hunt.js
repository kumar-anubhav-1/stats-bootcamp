/* Anomaly Hunt scoreboard: <div id="hunt-app"></div> */
(function () {
  const S = window.SDSB;
  S.onPage(() => {
    const app = document.getElementById("hunt-app");
    if (!app) return;
    S.load("hunt.json").then((hunt) => {
      function render() {
        const found = S.get("hunt.found", {});
        const n = Object.keys(found).length;
        let html = `<div class="hunt-score"><div class="hunt-bar"><div style="width:${(100 * n) / hunt.items.length}%"></div></div>
          <b>You have found ${n} of ${hunt.items.length} planted issues.</b></div>`;
        ["Retail", "Finance"].forEach((dom) => {
          html += `<h3>${dom}</h3><div class="hunt-grid">`;
          hunt.items.filter((i) => i.domain === dom).forEach((it) => {
            const ok = found[it.id];
            html += `<div class="hunt-card ${ok ? "is-found" : ""}" data-id="${it.id}">
              <div class="hunt-id">${it.id} · ${S.esc(it.unlocks_in)}</div>
              <div class="hunt-clue">${it.clue_html}</div>
              ${ok ? `<div class="hunt-found">Found: <b>${S.esc(it.title)}</b></div>` :
                `<div class="hunt-input"><input type="number" step="any" placeholder="${S.esc(it.ask)}"> <button class="md-button">Submit</button>
                 <a href="#" class="hunt-hint">hint</a></div><div class="hunt-msg"></div>`}
            </div>`;
          });
          html += "</div>";
        });
        app.innerHTML = html;
        app.querySelectorAll(".hunt-card:not(.is-found)").forEach((card) => {
          const it = hunt.items.find((x) => x.id === card.dataset.id);
          card.querySelector("button").onclick = () => {
            const v = parseFloat(card.querySelector("input").value);
            const msg = card.querySelector(".hunt-msg");
            if (isNaN(v)) { msg.textContent = "Enter the number your analysis produced."; return; }
            if (v >= it.lo && v <= it.hi) {
              const f = S.get("hunt.found", {}); f[it.id] = { value: v, at: new Date().toISOString() }; S.set("hunt.found", f); render();
            } else msg.textContent = "Not within the expected range. Re-check grain, filters and duplicates — then try again.";
          };
          card.querySelector(".hunt-hint").onclick = (e) => { e.preventDefault(); card.querySelector(".hunt-msg").innerHTML = `Navigator: <a href="${S.siteRoot}navigator/#${it.node}">${it.node}</a>. ${S.esc(it.hint || "")}`; };
        });
      }
      render();
    });
  });
})();
