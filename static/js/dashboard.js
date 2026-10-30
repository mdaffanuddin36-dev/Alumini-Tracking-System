// Dashboard UI helpers: compact-mode toggle and marquee animation
(function(){
  const body = document.body;
  const toggleId = 'dashboard-compact-toggle';
  const storageKey = 'dashboard_compact_mode';

  function applyMode(compact){
    if(compact) body.classList.add('compact');
    else body.classList.remove('compact');
  }

  function initToggle(){
    const btn = document.getElementById(toggleId);
    if(!btn) return;
    const current = localStorage.getItem(storageKey) === '1';
    applyMode(current);
    btn.addEventListener('click', function(){
      const now = !document.body.classList.contains('compact');
      applyMode(now);
      localStorage.setItem(storageKey, now ? '1' : '0');
      btn.innerText = now ? 'Compact: ON' : 'Compact: OFF';
    });
    btn.innerText = current ? 'Compact: ON' : 'Compact: OFF';
  }

  // Simple marquee -> horizontal auto-scroll for elements with class .marquee-text
  function initMarquee(){
    const marquees = document.querySelectorAll('.marquee-text');
    marquees.forEach(el => {
      // create simple animation by translating the element
      let speed = 40; // px per 10s
      let pos = 0;
      const width = el.scrollWidth;
      function step(){
        pos -= 1;
        if(Math.abs(pos) > width) pos = el.parentElement.clientWidth;
        el.style.transform = `translateX(${pos}px)`;
        requestAnimationFrame(step);
      }
      // only start if overflow
      if(el.scrollWidth > el.parentElement.clientWidth) requestAnimationFrame(step);
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    initToggle();
    initMarquee();

    // lazy image placeholders
    document.querySelectorAll('img.card-img-top').forEach(img => {
      if(!img.complete){
        img.classList.add('img-placeholder');
        img.addEventListener('load', ()=> img.classList.remove('img-placeholder'));
      }
    });
  });
})();

// Equalize card heights for pixel-perfect uniform boxes on larger screens
(function(){
  function isDesktop() { return window.innerWidth >= 768; }

  function equalizeCards(selector){
    if(!isDesktop()){
      // reset
      document.querySelectorAll(selector).forEach(el => el.style.height = '');
      return;
    }
    const cards = Array.from(document.querySelectorAll(selector)).filter(el => el.offsetParent !== null);
    if(cards.length === 0) return;
    // reset heights
    cards.forEach(c => c.style.height = '');
    // compute max
    const heights = cards.map(c => c.getBoundingClientRect().height);
    const max = Math.max(...heights);
    cards.forEach(c => c.style.height = Math.round(max) + 'px');
  }

  function runEqualize(){
    equalizeCards('.events-row .event-card');
    equalizeCards('.posts-row .post-card');
  }

  // debounce helper
  function debounce(fn, wait){
    let t;
    return function(){
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, arguments), wait);
    }
  }

  const debRun = debounce(runEqualize, 120);

  window.addEventListener('resize', debRun);
  window.addEventListener('load', runEqualize);
  document.addEventListener('DOMContentLoaded', runEqualize);

  // re-run when compact toggle changes - observe body class changes
  const obs = new MutationObserver(debounce(runEqualize, 80));
  obs.observe(document.body, { attributes: true, attributeFilter: ['class'] });

})();
