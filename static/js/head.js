// Marks JS as available before first paint, so the mobile menu starts closed.
document.documentElement.classList.add("js");

// A change of language gets its own, calmer page transition (see "lang" in site.css).
addEventListener("pagereveal", function (e) {
  var from = e.viewTransition && window.navigation && navigation.activation && navigation.activation.from;
  if (!from) return;
  var lang = function (u) { var m = new URL(u).pathname.match(/^\/(en|fr|it|de)\//); return m ? m[1] : "cs"; };
  if (lang(from.url) !== lang(location.href)) e.viewTransition.types.add("lang");
});
