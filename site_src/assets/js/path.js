/* Learning-path choice: "B" = Basic → Advanced, "L" = Leader. Opens the matching tab on every page. */
(function () {
  const LABEL = { B: "Basic → Advanced", L: "Leader" };
  function apply() {
    const p = window.SDSB.get("path", null);
    document.querySelectorAll(".path-chooser button[data-path]").forEach((b) => {
      b.classList.toggle("md-button--primary", b.dataset.path === p || (!p && b.dataset.path === "B"));
      b.onclick = () => { window.SDSB.set("path", b.dataset.path); apply(); };
    });
    if (!p) return;
    const want = LABEL[p];
    const done = new Set();
    document.querySelectorAll(".tabbed-set").forEach((set) => {
      const labels = set.querySelectorAll(":scope > .tabbed-labels > label");
      labels.forEach((lab) => {
        if (lab.textContent.trim() === want) {
          const input = document.getElementById(lab.htmlFor);
          if (input && !input.checked) { input.checked = true; input.dispatchEvent(new Event("change", { bubbles: true })); }
          done.add(set);
        }
      });
    });
    const badge = document.getElementById("sdsb-path-badge");
    if (badge) badge.textContent = "Your path: " + want;
  }
  window.SDSB.onPage(apply);
})();
