/* Progress page, lesson checklists, confidence scorecard and instructor view. */
(function () {
  const S = window.SDSB;

  function lessonChecks() {
    document.querySelectorAll(".lesson-done[data-lesson]").forEach((el) => {
      const id = el.dataset.lesson;
      const done = S.get("done." + id, false);
      el.innerHTML = `<label class="lesson-check"><input type="checkbox" ${done ? "checked" : ""}> Mark lesson ${S.esc(id)} complete</label>`;
      el.querySelector("input").onchange = (e) => S.set("done." + id, e.target.checked);
    });
  }

  function progressPage() {
    const app = document.getElementById("progress-app");
    if (!app) return;
    Promise.all([S.load("quizzes.json"), S.load("lessons.json")]).then(([bank, lessons]) => {
      const rows = lessons.map((l) => {
        const qz = Object.values(bank).filter((q) => q.lesson === l.id);
        const qcell = qz.map((q) => { const r = S.get("quiz." + q.id, null); return `${S.esc(q.track === "L" ? "Leader" : q.track === "F" ? "Basic → Advanced" : "Mixed")}: ${r ? r.best + "%" + (r.passed ? " ✓" : "") : "—"}`; }).join("<br>");
        return `<tr><td>${l.id}</td><td>${l.url ? `<a href="${S.siteRoot}${l.url}">${S.esc(l.title)}</a>` : S.esc(l.title)}</td><td>${S.get("done." + l.id, false) ? "✓" : ""}</td><td>${qcell || "—"}</td></tr>`;
      }).join("");
      const found = Object.keys(S.get("hunt.found", {})).length;
      app.innerHTML = `<p><b>Anomaly Hunt:</b> ${found} of 42 found.</p>
        <table><thead><tr><th>Lesson</th><th>Title</th><th>Done</th><th>Best quiz scores</th></tr></thead><tbody>${rows}</tbody></table>
        <p><button class="md-button" id="pg-export">Export my progress (JSON)</button> <label class="md-button">Import <input type="file" id="pg-import" accept=".json" hidden></label></p>
        <p class="sdsb-hint">Progress is stored only in this browser. Export it to move devices or to send to your instructor.</p>`;
      document.getElementById("pg-export").onclick = () => {
        const name = prompt("Your name or learner id (included in the file):", S.get("learner", "")) || "anonymous";
        S.set("learner", name);
        const blob = new Blob([JSON.stringify({ learner: name, exported: new Date().toISOString(), data: S.allKeys() }, null, 1)], { type: "application/json" });
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `progress_${name.replace(/\W+/g, "_")}.json`; a.click();
      };
      document.getElementById("pg-import").onchange = (e) => {
        const f = e.target.files[0]; if (!f) return;
        f.text().then((t) => { const d = JSON.parse(t).data || {}; Object.entries(d).forEach(([k, v]) => { try { localStorage.setItem(k, v); } catch (x) {} }); location.reload(); });
      };
    });
  }

  function instructorView() {
    const app = document.getElementById("instructor-app");
    if (!app) return;
    app.innerHTML = `<p><label class="md-button">Load learner progress files <input type="file" multiple accept=".json" hidden></label></p><div id="inst-out"></div>`;
    app.querySelector("input").onchange = async (e) => {
      const bank = await S.load("quizzes.json");
      const files = await Promise.all([...e.target.files].map((f) => f.text().then(JSON.parse)));
      const stats = {};
      const learners = [];
      files.forEach((f) => {
        const d = f.data || {};
        learners.push({ name: f.learner, hunt: Object.keys(JSON.parse(d["sdsb.hunt.found"] || "{}")).length });
        Object.entries(d).filter(([k]) => k.startsWith("sdsb.quizq.")).forEach(([k, v]) => {
          const qid = k.slice(11);
          Object.entries(JSON.parse(v)).forEach(([q, s]) => { const key = qid + " / " + q; (stats[key] = stats[key] || []).push(s); });
        });
      });
      const rows = Object.entries(stats).sort((a, b) => avg(a[1]) - avg(b[1])).map(([k, v]) => {
        const [qz, q] = k.split(" / ");
        const qq = bank[qz] && bank[qz].questions.find((x) => x.id === q);
        return `<tr><td>${S.esc(k)}</td><td>${v.length}</td><td>${Math.round(100 * avg(v))}%</td><td>${qq ? S.esc(qq.prompt_text.slice(0, 90)) : ""}</td></tr>`;
      }).join("");
      document.getElementById("inst-out").innerHTML = `<p>${files.length} learners loaded.</p>
        <table><thead><tr><th>Learner</th><th>Anomalies found</th></tr></thead><tbody>${learners.map((l) => `<tr><td>${S.esc(l.name)}</td><td>${l.hunt}</td></tr>`).join("")}</tbody></table>
        <h4>Per-question difficulty (hardest first)</h4><table><thead><tr><th>Quiz / question</th><th>Attempts</th><th>% correct</th><th>Prompt</th></tr></thead><tbody>${rows}</tbody></table>`;
    };
    function avg(a) { return a.reduce((s, x) => s + x, 0) / a.length; }
  }

  function scorecard() {
    const app = document.getElementById("scorecard-app");
    if (!app) return;
    Promise.all([S.load("scorecard.json"), S.load("quizzes.json")]).then(([sc, bank]) => {
      const points = sc.checkpoints;
      function demonstrated(group) {
        const qs = Object.values(bank).filter((q) => group.lessons.includes(q.lesson));
        const scores = qs.map((q) => S.get("quiz." + q.id, null)).filter(Boolean).map((r) => r.best);
        const found = S.get("hunt.found", {});
        const anom = group.anomalies.filter((a) => found[a]).length;
        if (!scores.length && !anom) return null;
        const q = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length / 20 : 0;
        return Math.min(5, Math.round((q + (group.anomalies.length ? (2 * anom) / group.anomalies.length : 0)) * 10) / 10);
      }
      let html = `<table class="sc-table"><thead><tr><th>Competency</th>${points.map((p) => `<th>${p}</th>`).join("")}<th>Evidence</th><th>Self (latest) vs demonstrated</th></tr></thead><tbody>`;
      sc.groups.forEach((g) => {
        const r = S.get("sc." + g.id, {});
        const latest = points.map((p) => r[p]).filter((x) => x).pop();
        const dem = demonstrated(g);
        html += `<tr><td><b>${S.esc(g.name)}</b><div class="sdsb-hint">${S.esc(g.lessons.join(", "))}</div></td>` +
          points.map((p) => `<td><select data-g="${g.id}" data-p="${p}"><option></option>${[1, 2, 3, 4, 5].map((v) => `<option ${r[p] == v ? "selected" : ""}>${v}</option>`).join("")}</select></td>`).join("") +
          `<td><input class="sc-ev" data-g="${g.id}" value="${S.esc(r.evidence || "")}" placeholder="exercise id, anomaly, recipe run"></td>
           <td><div class="sc-bars"><div class="sc-self" style="width:${(latest || 0) * 20}%">${latest || "–"}</div><div class="sc-dem" style="width:${(dem || 0) * 20}%">${dem === null ? "no evidence yet" : dem}</div></div></td></tr>`;
      });
      html += "</tbody></table>";
      app.innerHTML = html;
      app.querySelectorAll("select").forEach((s) => (s.onchange = () => { const r = S.get("sc." + s.dataset.g, {}); r[s.dataset.p] = +s.value || null; S.set("sc." + s.dataset.g, r); scorecard(); }));
      app.querySelectorAll(".sc-ev").forEach((i) => (i.onchange = () => { const r = S.get("sc." + i.dataset.g, {}); r.evidence = i.value; S.set("sc." + i.dataset.g, r); }));
    });
  }

  S.onPage(() => { lessonChecks(); progressPage(); instructorView(); scorecard(); });
})();
