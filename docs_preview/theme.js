// mockaime preview chrome (v2): dark by default, current-page nav marker,
// page title band, and a site footer. Decoration only.
(function () {
  try { if (!localStorage.getItem('theme')) document.documentElement.setAttribute('data-theme', 'dark'); } catch (e) {}

  // pages whose title gets the hero band
  var HERO = ['index.html','practice.html','past_tests.html','search.html','inbox.html','past_aime.html','past_amc8.html','past_amc10.html','past_amc12.html','login.html'];

  function page() {
    var p = location.pathname.split('/').pop();
    return p === '' ? 'index.html' : p;
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  function run() {
    var here = page();
    var nav = document.querySelector('nav');
    if (nav) {
      var brand = nav.querySelector('div > a');
      if (brand) {
        for (var i = 0; i < brand.childNodes.length; i++) {
          var n = brand.childNodes[i];
          if (n.nodeType === 3 && /mock\s*aime/i.test(n.textContent)) {
            var w = el('span');
            w.innerHTML = 'mockaime<span class="ma-tld">.com</span>';
            brand.replaceChild(w, n);
            break;
          }
        }
      }
      nav.querySelectorAll('a').forEach(function (a, idx) {
        if (idx === 0) return;
        var target = (a.getAttribute('href') || '').split('/').pop();
        var isPast = here.indexOf('past_') === 0 && target === 'past_tests.html';
        if (target === here || isPast) a.classList.add('ma-active');
      });
    }

    var h1 = document.querySelector('body h1');
    if (h1 && HERO.indexOf(here) !== -1 && !h1.closest('.ma-hero')) {
      var hero = el('header', 'ma-hero');
      var inner = el('div', 'ma-hero-inner');
      var left = el('div');
      hero.appendChild(inner);
      inner.appendChild(left);
      if (nav && nav.parentNode === document.body) nav.insertAdjacentElement('afterend', hero);
      else h1.parentNode.insertBefore(hero, h1);
      left.appendChild(h1);
    }

    if (!document.querySelector('.ma-footer') && !/^admin/.test(here)) {
      var foot = el('footer', 'ma-footer');
      foot.innerHTML =
        '<div class="ma-footer-inner">' +
          '<div><div class="ma-footer-brand"><img src="256px_transparentBG.png" alt="">mockaime<span>.com</span></div>' +
          '</div>' +
          '<div class="ma-footer-links">' +
            '<div><strong>Practice</strong><a href="index.html">Mock test</a><a href="practice.html">Practice</a><a href="search.html">Search</a></div>' +
            '<div><strong>Archive</strong><a href="past_aime.html">AIME</a><a href="past_amc12.html">AMC 12</a><a href="past_amc10.html">AMC 10</a><a href="past_amc8.html">AMC 8</a></div>' +
            '<div><strong>Account</strong><a href="profile.html">Profile</a><a href="inbox.html">Inbox</a><a href="login.html">Log in</a></div>' +
          '</div>' +
        '</div>';
      var legacy = document.querySelector('footer:not(.ma-footer)');
      document.body.appendChild(foot);
      if (legacy) { legacy.classList.add('ma-footer-credit'); foot.appendChild(legacy); }
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();
