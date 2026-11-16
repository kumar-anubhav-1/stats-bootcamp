/* Quiz engine: renders <div class="quiz" data-quiz="ID"></div> from assets/data/quizzes.json.
   Types: mcq, tf_reason, spot_error, scenario, navigator, ai_review (single choice), multi, numeric, open (self-marked). */
(function () {
  const S = window.SDSB;

  function correctOf(q) { return q.options.filter((o) => o.correct).map((o) => o.id); }

  function renderQuestion(q, idx, quizId) {
    const card = document.createElement("div");
    card.className = "sdsb-q";
    card.dataset.qid = q.id;
    const tags = [q.track === "L" ? "Leader" : "Basic → Advanced", "difficulty " + q.difficulty, q.type.replace("_", " "), q.node || ""].filter(Boolean)
      .map((t) => `<span class="sdsb-tag">${S.esc(t)}</span>`).join(" ");
    let body = `<div class="sdsb-q-head"><b>Q${idx + 1}.</b> ${tags}</div><div class="sdsb-q-prompt">${q.prompt_html}</div>`;
    const single = ["mcq", "tf_reason", "spot_error", "scenario", "navigator", "ai_review"].includes(q.type);
    if (single || q.type === "multi") {
      const opts = q.shuffle === false ? q.options : S.shuffle(q.options);
      body += `<div class="sdsb-opts">` + opts.map((o) => `<label class="sdsb-opt" data-oid="${o.id}"><input type="${single ? "radio" : "checkbox"}" name="${quizId}-${q.id}" value="${o.id}"> <span>${o.html}</span></label>`).join("") + `</div>`;
      if (q.type === "multi") body += `<div class="sdsb-hint">Select all that apply.</div>`;
    } else if (q.type === "numeric") {
      body += `<div class="sdsb-num"><input type="number" step="any" placeholder="your answer"> <span class="sdsb-unit">${S.esc(q.unit || "")}</span></div>`;
    } else if (q.type === "open") {
      body += `<textarea class="sdsb-open" rows="4" placeholder="Write your answer, then reveal the model answer and mark yourself honestly."></textarea>`;
    }
    body += `<div class="sdsb-actions"><button class="md-button sdsb-check">${q.type === "open" ? "Reveal model answer" : "Check"}</button>${q.hint_html ? ' <button class="md-button sdsb-hintbtn">Hint</button>' : ""}</div>`;
    body += `<div class="sdsb-hinttext" hidden>${q.hint_html || ""}</div><div class="sdsb-feedback" hidden></div>`;
    card.innerHTML = body;
    const fb = card.querySelector(".sdsb-feedback");
    const hb = card.querySelector(".sdsb-hintbtn");
    if (hb) hb.onclick = () => (card.querySelector(".sdsb-hinttext").hidden = false);
    card.querySelector(".sdsb-check").onclick = () => {
      let ok = null;
      let html = "";
      if (single || q.type === "multi") {
        const chosen = [...card.querySelectorAll("input:checked")].map((i) => i.value);
        if (!chosen.length) { fb.hidden = false; fb.innerHTML = "Choose an answer first."; return; }
        const corr = correctOf(q);
        ok = chosen.length === corr.length && chosen.every((c) => corr.includes(c));
        card.querySelectorAll(".sdsb-opt").forEach((l) => {
          const o = q.options.find((x) => x.id === l.dataset.oid);
          l.classList.toggle("is-correct", !!o.correct);
          l.classList.toggle("is-wrong", chosen.includes(o.id) && !o.correct);
        });
        const whys = q.options.filter((o) => chosen.includes(o.id) && o.why_html).map((o) => `<li>${o.why_html}</li>`).join("");
        html = whys ? `<ul class="sdsb-whys">${whys}</ul>` : "";
      } else if (q.type === "numeric") {
        const v = parseFloat(card.querySelector("input").value);
        if (isNaN(v)) { fb.hidden = false; fb.innerHTML = "Enter a number."; return; }
        const tol = q.tolerance_abs !== undefined ? q.tolerance_abs : Math.abs(q.answer) * (q.tolerance_rel || 0.02);
        ok = Math.abs(v - q.answer) <= tol + 1e-12;
        html = `<p>Accepted answer: <b>${q.answer}</b>${q.unit ? " " + S.esc(q.unit) : ""} (± ${+tol.toFixed(4)}).</p>`;
      } else if (q.type === "open") {
        html = `<div class="sdsb-model"><b>Model answer</b>${q.model_html}</div>` + (q.rubric_html ? `<div class="sdsb-rubric"><b>Rubric</b>${q.rubric_html}</div>` : "") +
          `<div class="sdsb-self">Mark yourself: <button class="md-button" data-s="2">Full</button> <button class="md-button" data-s="1">Partial</button> <button class="md-button" data-s="0">Missed</button></div>`;
      }
      fb.hidden = false;
      const verdict = ok === null ? "" : ok ? `<div class="sdsb-ok">${S.esc(q.correct_label || "Correct.")}</div>` : `<div class="sdsb-no">${S.esc(q.incorrect_label || "Not quite.")}</div>`;
      fb.innerHTML = verdict + html + (q.explanation_html ? `<div class="sdsb-expl">${q.explanation_html}</div>` : "");
      if (q.type === "open") {
        fb.querySelectorAll("[data-s]").forEach((b) => (b.onclick = () => { card.dataset.score = b.dataset.s / 2; fb.querySelector(".sdsb-self").innerHTML = "Recorded."; card.dispatchEvent(new Event("answered", { bubbles: true })); }));
      } else {
        card.dataset.score = ok ? 1 : 0;
        card.querySelector(".sdsb-check").disabled = true;
        card.dispatchEvent(new Event("answered", { bubbles: true }));
      }
    };
    return card;
  }

  function mount(el, quiz) {
    el.innerHTML = "";
    const id = quiz.id;
    const head = document.createElement("div");
    head.className = "sdsb-quiz-head";
    const best = S.get("quiz." + id, null);
    head.innerHTML = `<b>${S.esc(quiz.title)}</b> · ${quiz.questions.length} questions · pass mark ${quiz.pass_mark}%` + (best ? ` · your best: <b>${best.best}%</b>` : "");
    el.appendChild(head);
    const qs = quiz.questions.map((q) => (q.variants && q.variants.length && el.dataset.attempt > 0 ? Object.assign({}, q, q.variants[(el.dataset.attempt - 1) % q.variants.length]) : q));
    qs.forEach((q, i) => el.appendChild(renderQuestion(q, i, id)));
    const foot = document.createElement("div");
    foot.className = "sdsb-quiz-foot";
    foot.innerHTML = `<span class="sdsb-score">Answered 0 / ${qs.length}</span> <button class="md-button sdsb-retry">Retry (new order${qs.some((q) => q.variants) ? " and variants" : ""})</button>`;
    el.appendChild(foot);
    el.addEventListener("answered", () => {
      const cards = [...el.querySelectorAll(".sdsb-q")];
      const done = cards.filter((c) => c.dataset.score !== undefined);
      const score = done.reduce((s, c) => s + parseFloat(c.dataset.score), 0);
      const pct = Math.round((100 * score) / cards.length);
      foot.querySelector(".sdsb-score").innerHTML = `Answered ${done.length} / ${cards.length} · score ${pct}%` + (done.length === cards.length ? (pct >= quiz.pass_mark ? " · <b>passed</b>" : " · below pass mark — review the explanations and retry") : "");
      if (done.length === cards.length) {
        const prev = S.get("quiz." + id, { best: 0, attempts: 0 });
        S.set("quiz." + id, { best: Math.max(prev.best, pct), last: pct, attempts: prev.attempts + 1, passed: Math.max(prev.best, pct) >= quiz.pass_mark, at: new Date().toISOString() });
        const per = {};
        cards.forEach((c) => (per[c.dataset.qid] = parseFloat(c.dataset.score)));
        S.set("quizq." + id, per);
      }
    });
    foot.querySelector(".sdsb-retry").onclick = () => { el.dataset.attempt = (+el.dataset.attempt || 0) + 1; mount(el, quiz); };
  }

  S.onPage(() => {
    const els = document.querySelectorAll(".quiz[data-quiz]");
    if (!els.length) return;
    S.load("quizzes.json").then((bank) => {
      els.forEach((el) => {
        const quiz = bank[el.dataset.quiz];
        if (!quiz) { el.innerHTML = `<em>Quiz ${S.esc(el.dataset.quiz)} not found.</em>`; return; }
        el.dataset.attempt = 0;
        mount(el, quiz);
      });
    });
  });
})();
