// Marks JS as available before first paint, so the mobile menu starts closed.
document.documentElement.classList.add("js");

// A page pre-rendered on hover was laid out at the top; when it is shown, honour the link's #fragment (e.g. #main).
addEventListener("pagereveal", function () {
  var t = location.hash && document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if (t) t.scrollIntoView();
});

// Moving within a section (side menu and section lists link to #main) slides the content instead of cross-fading the page.
function slideType(e, url) { if (e.viewTransition && url && new URL(url).hash === "#main") e.viewTransition.types.add("slide"); }
addEventListener("pageswap", function (e) { slideType(e, e.activation && e.activation.entry && e.activation.entry.url); });
addEventListener("pagereveal", function (e) { slideType(e, location.href); });
