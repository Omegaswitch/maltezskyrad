// Opening outline trace of the armorial bearing (switch: "openingTrace" in content/site.json).
// Plays once per browser session, never with reduced motion; any key or tap ends it early.
(function () {
  var d = document.documentElement;
  d.classList.add("js");
  try {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (sessionStorage.getItem("intro-seen")) return;
    sessionStorage.setItem("intro-seen", "1");
  } catch (e) {
    return; // storage blocked: skip rather than replay on every page
  }
  d.classList.add("intro-on");
  var off = function () { d.classList.remove("intro-on"); };
  setTimeout(off, 2100);
  addEventListener("keydown", off, { once: true });
  addEventListener("pointerdown", off, { once: true });
})();
