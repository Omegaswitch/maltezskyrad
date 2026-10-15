// maltezskyrad.cz — progressive enhancement only; every page works without this file.
(function () {
  // ---- main menu (mobile) and submenus
  var toggle = document.querySelector(".menu-toggle");
  var menu = document.getElementById("menu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
      menu.classList.toggle("open", open);
    });
  }
  document.querySelectorAll(".sub-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var li = btn.parentElement;
      var open = !li.classList.contains("open");
      li.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", String(open));
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    document.querySelectorAll(".has-sub.open").forEach(function (li) {
      li.classList.remove("open");
      var b = li.querySelector(".sub-toggle");
      if (b) b.setAttribute("aria-expanded", "false");
    });
    if (document.activeElement && document.activeElement.closest(".sub")) {
      var top = document.activeElement.closest(".has-sub").querySelector("a");
      if (top) top.focus();
    }
  });

  // ---- images: skeleton until loaded, then a short fade
  document.querySelectorAll("img.ph-img").forEach(function (img) {
    var done = function () { img.classList.add("is-loaded"); };
    if (img.complete) done();
    else { img.addEventListener("load", done, { once: true }); img.addEventListener("error", done, { once: true }); }
  });

  // ---- AddCal calendar: load the vendor script only when a calendar is near the viewport
  var widgets = document.querySelectorAll(".cal-widget");
  if (!widgets.length) return;
  var SRC = "https://cdn.addcal.co/embed/v3/calendar.min.js";
  var requested = false;

  function watch(w) {
    var host = w.querySelector("addcal-calendar");
    var started = Date.now();
    (function poll() {
      var root = host && (host.shadowRoot || host);
      if (root && root.querySelector(".addcal-calendar-container, .addcal-calendar-header, .addcal-event")) {
        w.setAttribute("data-state", "ready");
        return;
      }
      if (Date.now() - started > 15000) { w.setAttribute("data-state", "failed"); return; }
      setTimeout(poll, 250);
    })();
  }

  function load() {
    if (requested) return;
    requested = true;
    var s = document.createElement("script");
    s.src = SRC;
    s.async = true;
    s.onerror = function () { widgets.forEach(function (w) { w.setAttribute("data-state", "failed"); }); };
    document.head.appendChild(s);
    widgets.forEach(watch);
  }

  var io = new IntersectionObserver(function (entries) {
    if (entries.some(function (e) { return e.isIntersecting; })) { io.disconnect(); load(); }
  }, { rootMargin: "600px 0px" });
  widgets.forEach(function (w) { io.observe(w); });
})();
