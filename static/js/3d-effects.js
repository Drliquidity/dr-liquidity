/* ============================================
   DR LIQUIDITY — 3D Effects (CSS-based)
   - Mouse-tilt cards
   - Scroll-triggered 3D reveals
   - Page transitions
   - Parallax hero text
   ============================================ */
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // ===== Mouse-tilt cards =====
  document.querySelectorAll('.tilt-card').forEach((card) => {
    const inner = card.querySelector('.tilt-inner') || card;
    const shine = card.querySelector('.tilt-shine');
    let raf = null;
    let rect = null;

    const updateRect = () => {
      rect = card.getBoundingClientRect();
    };

    card.addEventListener('mouseenter', () => {
      updateRect();
      card.style.transition = 'none';
    });

    card.addEventListener('mousemove', (e) => {
      if (!rect) updateRect();
      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cx = rect.width / 2;
        const cy = rect.height / 2;
        const rotateY = ((x - cx) / cx) * 8;   // max 8deg
        const rotateX = -((y - cy) / cy) * 8;  // max 8deg

        card.style.transform = `perspective(1000px) rotateY(${rotateY}deg) rotateX(${rotateX}deg) scale3d(1.02, 1.02, 1.02)`;

        if (shine) {
          shine.style.setProperty('--mx', `${(x / rect.width) * 100}%`);
          shine.style.setProperty('--my', `${(y / rect.height) * 100}%`);
        }
      });
    });

    card.addEventListener('mouseleave', () => {
      if (raf) cancelAnimationFrame(raf);
      card.style.transition = 'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.5s ease';
      card.style.transform = 'perspective(1000px) rotateY(0) rotateX(0) scale3d(1, 1, 1)';
    });

    window.addEventListener('scroll', updateRect, { passive: true });
  });

  // ===== Scroll-triggered 3D reveals =====
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          // Optional: unobserve after first reveal
          // revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -80px 0px' }
  );

  document.querySelectorAll('.reveal-3d, .reveal-3d-left, .reveal-3d-right, .reveal-3d-pop').forEach((el) => {
    revealObserver.observe(el);
  });

  // ===== Hero parallax (mouse-follow on text layers) =====
  const heroSection = document.querySelector('[data-parallax-hero]');
  if (heroSection) {
    const layers = heroSection.querySelectorAll('[data-parallax-depth]');
    let heroMouse = { x: 0, y: 0 };
    let heroX = 0, heroY = 0;

    heroSection.addEventListener('mousemove', (e) => {
      const rect = heroSection.getBoundingClientRect();
      heroMouse.x = (e.clientX - rect.left) / rect.width - 0.5;
      heroMouse.y = (e.clientY - rect.top) / rect.height - 0.5;
    });

    function animateHero() {
      heroX += (heroMouse.x - heroX) * 0.08;
      heroY += (heroMouse.y - heroY) * 0.08;
      layers.forEach((layer) => {
        const depth = parseFloat(layer.dataset.parallaxDepth) || 0;
        const x = heroX * depth;
        const y = heroY * depth;
        layer.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      });
      requestAnimationFrame(animateHero);
    }
    animateHero();
  }

  // ===== Page transition on internal link click =====
  document.querySelectorAll('a[href]').forEach((link) => {
    const href = link.getAttribute('href');
    if (
      !href ||
      href.startsWith('#') ||
      href.startsWith('http') ||
      href.startsWith('mailto:') ||
      link.target === '_blank' ||
      link.hasAttribute('data-no-transition')
    ) return;

    link.addEventListener('click', (e) => {
      // Allow modifier-clicks
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      document.body.classList.add('fade-out');
      setTimeout(() => {
        window.location.href = href;
      }, 250);
    });
  });

  // ===== Stagger children on load =====
  document.querySelectorAll('.stagger-in').forEach((container) => {
    // already handled via CSS animation
  });

  // ===== Smooth-scroll for in-page anchors with 3D offset =====
  document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach((a) => {
    a.addEventListener('click', (e) => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ===== Auto-add reveal classes to common patterns =====
  // Sections
  document.querySelectorAll('main > section').forEach((sec, i) => {
    if (!sec.classList.contains('reveal-3d') && i > 0) {
      sec.classList.add('reveal-3d');
      revealObserver.observe(sec);
    }
  });

  // Firm cards / articles / posts
  document.querySelectorAll('.stat-card, [data-reveal-card]').forEach((el) => {
    el.classList.add('reveal-3d-pop');
    revealObserver.observe(el);
  });

  // ===== Animated counter (counts up when in view) =====
  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          const end = parseFloat(el.dataset.counter) || 0;
          const duration = parseInt(el.dataset.counterDuration) || 2000;
          const decimals = parseInt(el.dataset.counterDecimals) || 0;
          const prefix = el.dataset.counterPrefix || '';
          const suffix = el.dataset.counterSuffix || '';
          const startTime = performance.now();

          function step(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // easeOutExpo
            const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const value = end * eased;
            el.textContent = prefix + value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
            if (progress < 1) requestAnimationFrame(step);
          }
          requestAnimationFrame(step);
          counterObserver.unobserve(el);
        }
      });
    },
    { threshold: 0.3 }
  );

  document.querySelectorAll('.counter[data-counter]').forEach((el) => {
    counterObserver.observe(el);
  });

  // ===== Mouse magnetic effect on buttons =====
  document.querySelectorAll('.btn-3d, .magnetic').forEach((btn) => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.transform = '';
    });
  });
})();
