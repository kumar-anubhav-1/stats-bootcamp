/* Shared helpers: data loading relative to the site root, local progress store. */
(function () {
  const here = document.currentScript ? document.currentScript.src : "";
  const base = here ? new URL("../data/", here).href : "assets/data/";
  const siteRoot = here ? new URL("../../", here).href : "/";
  const cache = {};
  window.SDSB = {
    siteRoot,
    load(name) {
      if (!cache[name]) cache[name] = fetch(base + name).then((r) => r.json());
      return cache[name];
    },
    get(key, dflt) {
      try { const v = localStorage.getItem("sdsb." + key); return v === null ? dflt : JSON.parse(v); } catch (e) { return dflt; }
    },
    set(key, val) {
      try { localStorage.setItem("sdsb." + key, JSON.stringify(val)); } catch (e) { /* storage unavailable */ }
    },
    allKeys() {
      const out = {};
      try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith("sdsb.")) out[k] = localStorage.getItem(k); } } catch (e) {}
      return out;
    },
    esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); },
    shuffle(a) { const b = a.slice(); for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; },
    onPage(fn) {
      if (window.document$ && window.document$.subscribe) window.document$.subscribe(fn);
      else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
      else fn();
    },
  };
})();
