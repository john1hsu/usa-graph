(function () {
  "use strict";
  var data = JSON.parse(document.getElementById("kg-data").textContent);

  // ---------- search filters the article list ----------
  var q = document.getElementById("q");
  var nores = document.getElementById("nores");
  var bySlug = {};
  (data.search || []).forEach(function (r) {
    bySlug[r.s] = (r.t + " " + r.a + " " + r.m).toLowerCase();
  });
  function applyFilter() {
    var term = q.value.trim().toLowerCase();
    var any = false;
    document.querySelectorAll(".domain").forEach(function (sec) {
      var shown = 0;
      sec.querySelectorAll("li").forEach(function (li) {
        var hit = !term || bySlug[li.dataset.s].indexOf(term) !== -1;
        li.hidden = !hit;
        if (hit) shown++;
      });
      sec.hidden = shown === 0;
      if (shown) any = true;
    });
    nores.hidden = any;
  }
  if (q) q.addEventListener("input", applyFilter);
})();
