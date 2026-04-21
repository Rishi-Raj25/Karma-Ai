// ============================================
// KARMA — Premium Interactive Experience
// ============================================

// ============================================
// Preloader
// ============================================
const preloader = document.getElementById('preloader');
const preloaderBar = document.getElementById('preloaderBar');
const preloaderStatus = document.getElementById('preloaderStatus');

const loadSteps = [
  { pct: 15, text: 'Loading assets...' },
  { pct: 35, text: 'Initializing AI engine...' },
  { pct: 55, text: 'Connecting to defense network...' },
  { pct: 75, text: 'Calibrating scam detection...' },
  { pct: 90, text: 'Almost ready...' },
  { pct: 100, text: 'Defense system online.' }
];

let loadIdx = 0;
const loadInterval = setInterval(() => {
  if (loadIdx < loadSteps.length) {
    preloaderBar.style.width = loadSteps[loadIdx].pct + '%';
    preloaderStatus.textContent = loadSteps[loadIdx].text;
    loadIdx++;
  } else {
    clearInterval(loadInterval);
    setTimeout(() => {
      preloader.classList.add('done');
      document.body.classList.add('loaded');
      // Start hero animations after preloader finishes
      initAfterLoad();
    }, 400);
  }
}, 350);

// ============================================
// Init After Load — all animations go here
// ============================================
function initAfterLoad() {
  // Initialize Lucide icons
  lucide.createIcons();

  // Register GSAP plugins
  gsap.registerPlugin(ScrollTrigger, TextPlugin);

  // ============================================
  // Confetti Particles (Google Antigravity style)
  // ============================================
  const confettiContainer = document.getElementById('heroConfetti');
  const heroEl = document.querySelector('.hero');
  const confettiPieces = [];

  if (confettiContainer && heroEl) {
    const colors = [
      '#C4F82A', '#C4F82A', // neon lime (dominant)
      '#7c3aed', '#818cf8', // purple / indigo
      '#3b82f6', '#60a5fa', // blue
      '#f472b6', '#fb7185'  // pink / rose
    ];
    const shapes = ['dot', 'dash', 'dot', 'dash', 'dot']; // more dots than dashes

    for (let i = 0; i < 70; i++) {
      const el = document.createElement('div');
      el.className = 'confetti-piece';
      const color = colors[Math.floor(Math.random() * colors.length)];
      const shape = shapes[Math.floor(Math.random() * shapes.length)];
      const size = Math.random() * 4 + 2; // 2-6px
      const baseX = Math.random() * 100; // % position
      const baseY = Math.random() * 100;
      const depth = Math.random() * 0.4 + 0.05; // parallax depth: 0.05 to 0.45
      const rotation = Math.random() * 360;

      if (shape === 'dot') {
        el.style.cssText = `
          width: ${size}px; height: ${size}px;
          background: ${color};
          border-radius: 50%;
          left: ${baseX}%; top: ${baseY}%;
          opacity: ${Math.random() * 0.5 + 0.3};
          transform: rotate(${rotation}deg);
        `;
      } else {
        const len = Math.random() * 14 + 6; // 6-20px
        el.style.cssText = `
          width: ${len}px; height: ${size * 0.6}px;
          background: ${color};
          border-radius: 2px;
          left: ${baseX}%; top: ${baseY}%;
          opacity: ${Math.random() * 0.45 + 0.25};
          transform: rotate(${rotation}deg);
        `;
      }

      confettiContainer.appendChild(el);
      confettiPieces.push({ el, baseX, baseY, depth, rotation });
    }

    // Mouse-follow parallax
    let heroRect = heroEl.getBoundingClientRect();
    window.addEventListener('resize', () => { heroRect = heroEl.getBoundingClientRect(); });

    heroEl.addEventListener('mousemove', (e) => {
      const rect = heroEl.getBoundingClientRect();
      const mx = ((e.clientX - rect.left) / rect.width - 0.5) * 2; // -1 to 1
      const my = ((e.clientY - rect.top) / rect.height - 0.5) * 2;

      // Confetti parallax
      confettiPieces.forEach(p => {
        const offsetX = mx * p.depth * 60;
        const offsetY = my * p.depth * 60;
        p.el.style.transform = `translate(${offsetX}px, ${offsetY}px) rotate(${p.rotation + mx * 15}deg)`;
      });

      // Split-screen grid parallax
      heroEl.style.setProperty('--hero-mx', `${mx * 15}px`);
      heroEl.style.setProperty('--hero-my', `${my * 10}px`);
    });

    // Reset on mouse leave
    heroEl.addEventListener('mouseleave', () => {
      confettiPieces.forEach(p => {
        p.el.style.transform = `rotate(${p.rotation}deg)`;
        p.el.style.transition = 'transform 0.6s ease';
        setTimeout(() => { p.el.style.transition = 'transform 0.08s linear'; }, 600);
      });

      // Reset split-screen grids
      heroEl.style.setProperty('--hero-mx', '0px');
      heroEl.style.setProperty('--hero-my', '0px');
    });
  }

  // ============================================
  // Section Confetti (How It Works + Stats)
  // ============================================
  document.querySelectorAll('[data-confetti-section]').forEach(container => {
    const sectionColors = [
      '#C4F82A', '#C4F82A',
      '#7c3aed', '#818cf8',
      '#3b82f6', '#60a5fa',
      '#f472b6', '#fb7185'
    ];
    const sectionShapes = ['dot', 'dash', 'dot', 'dash', 'dot'];

    for (let i = 0; i < 25; i++) {
      const el = document.createElement('div');
      el.className = 'confetti-piece';
      const color = sectionColors[Math.floor(Math.random() * sectionColors.length)];
      const shape = sectionShapes[Math.floor(Math.random() * sectionShapes.length)];
      const size = Math.random() * 3.5 + 1.5;
      const rotation = Math.random() * 360;

      if (shape === 'dot') {
        el.style.cssText = `
          width: ${size}px; height: ${size}px;
          background: ${color};
          border-radius: 50%;
          left: ${Math.random() * 100}%; top: ${Math.random() * 100}%;
          opacity: ${Math.random() * 0.35 + 0.15};
          transform: rotate(${rotation}deg);
        `;
      } else {
        const len = Math.random() * 12 + 5;
        el.style.cssText = `
          width: ${len}px; height: ${size * 0.5}px;
          background: ${color};
          border-radius: 2px;
          left: ${Math.random() * 100}%; top: ${Math.random() * 100}%;
          opacity: ${Math.random() * 0.3 + 0.12};
          transform: rotate(${rotation}deg);
        `;
      }
      container.appendChild(el);
    }
  });



  // ============================================
  // Cursor Ball (desktop only)
  // ============================================
  const cursorBall = document.getElementById('cursorBall');
  const cursorRing = document.getElementById('cursorRing');

  if (cursorBall && cursorRing && window.matchMedia('(pointer: fine)').matches) {
    let mouseX = 0, mouseY = 0;
    let ringX = 0, ringY = 0;

    document.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;

      // Ball follows instantly
      cursorBall.style.left = mouseX + 'px';
      cursorBall.style.top = mouseY + 'px';

      if (!cursorBall.classList.contains('visible')) {
        cursorBall.classList.add('visible');
        cursorRing.classList.add('visible');
      }
    });

    // Ring follows with smooth delay
    function animateRing() {
      ringX += (mouseX - ringX) * 0.15;
      ringY += (mouseY - ringY) * 0.15;
      cursorRing.style.left = ringX + 'px';
      cursorRing.style.top = ringY + 'px';
      requestAnimationFrame(animateRing);
    }
    animateRing();

    // Hover effect on interactive elements
    const hoverTargets = 'a, button, .btn-primary, .btn-outline, .nav-cta, .btn-cta-primary, .btn-cta-outline, .btn-play, .btn-listen, .btn-info, .feature-card, .stat-card, .call-card';
    document.querySelectorAll(hoverTargets).forEach(el => {
      el.addEventListener('mouseenter', () => {
        cursorBall.classList.add('hovering');
        cursorRing.classList.add('hovering');
      });
      el.addEventListener('mouseleave', () => {
        cursorBall.classList.remove('hovering');
        cursorRing.classList.remove('hovering');
      });
    });

    // Hide cursor on mouse leave from window
    document.addEventListener('mouseleave', () => {
      cursorBall.classList.remove('visible');
      cursorRing.classList.remove('visible');
    });
    document.addEventListener('mouseenter', () => {
      cursorBall.classList.add('visible');
      cursorRing.classList.add('visible');
    });
  }

  // ============================================
  // Navbar Scroll
  // ============================================
  const navbar = document.getElementById('navbar');
  const scrollIndicator = document.getElementById('scrollIndicator');

  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    // Hide scroll indicator after scrolling
    if (scrollIndicator) {
      scrollIndicator.classList.toggle('hidden', y > 200);
    }
  });

  // Active nav link tracking
  const sections = document.querySelectorAll('.section, .hero');
  const navLinks = document.querySelectorAll('.nav-link');

  const linkObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
        });
      }
    });
  }, { threshold: 0.3, rootMargin: '-80px 0px 0px 0px' });

  sections.forEach(s => linkObserver.observe(s));

  // Mobile Menu
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const navLinksContainer = document.getElementById('navLinks');

  mobileMenuBtn?.addEventListener('click', () => {
    mobileMenuBtn.classList.toggle('open');
    navLinksContainer.classList.toggle('open');
    document.body.style.overflow = navLinksContainer.classList.contains('open') ? 'hidden' : '';
  });

  navLinksContainer?.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      mobileMenuBtn.classList.remove('open');
      navLinksContainer.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // ============================================
  // Scroll to Top Button
  // ============================================
  const scrollTopBtn = document.getElementById('scrollTopBtn');
  if (scrollTopBtn) {
    window.addEventListener('scroll', () => {
      scrollTopBtn.classList.toggle('visible', window.scrollY > 600);
    });
    scrollTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ============================================
  // Hero Particles
  // ============================================
  function createParticles() {
    const container = document.getElementById('heroParticles');
    if (!container) return;

    for (let i = 0; i < 50; i++) {
      const particle = document.createElement('div');
      const size = Math.random() * 3 + 1;
      particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: rgba(var(--accent-rgb), ${Math.random() * 0.4 + 0.1});
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        pointer-events: none;
      `;
      container.appendChild(particle);

      gsap.to(particle, {
        y: `random(-80, 80)`,
        x: `random(-40, 40)`,
        opacity: `random(0.1, 0.6)`,
        duration: `random(4, 10)`,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: Math.random() * 3
      });
    }
  }

  createParticles();

  // ============================================
  // Hero GSAP Animations
  // ============================================
  function animateHero() {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    // Navbar entrance — staggered reveal
    tl.from('.navbar', { y: -100, opacity: 0, duration: 0.9 }, 0);
    tl.from('.nav-link', { y: -15, opacity: 0, duration: 0.4, stagger: 0.06, immediateRender: false }, 0.6);
    tl.from('.nav-cta', { scale: 0.8, opacity: 0, duration: 0.4, ease: 'back.out(1.5)', immediateRender: false }, 0.9);

    // Badge
    tl.to('.hero-badge', { opacity: 1, y: 0, duration: 0.8 }, 0.3);

    // Hindi tagline
    tl.to('.hero-tagline-hindi', { opacity: 1, y: 0, duration: 0.7 }, 0.5);

    // Energy Orb entrance
    tl.from('.orb-core', { scale: 0, opacity: 0, duration: 1.2, ease: 'expo.out' }, 0.5);
    tl.from('.orb-ring', { scale: 0, opacity: 0, duration: 1, stagger: 0.15, ease: 'expo.out' }, 0.7);
    tl.from('.orb-pulse', { scale: 0, opacity: 0, duration: 0.8 }, 1.0);

    // Title letters - stagger reveal
    tl.to('.title-word', {
      opacity: 1,
      y: 0,
      rotateX: 0,
      duration: 0.8,
      stagger: 0.08,
      ease: 'back.out(1.7)'
    }, 0.7);

    // Subtitle
    tl.to('.hero-subtitle', { opacity: 1, y: 0, duration: 0.7 }, 1.3);
    tl.to('.hero-desc', { opacity: 1, y: 0, duration: 0.7 }, 1.5);

    // Metrics
    tl.to('.hero-metrics', { opacity: 1, y: 0, duration: 0.8 }, 1.7);

    // Actions
    tl.to('.hero-actions', { opacity: 1, y: 0, duration: 0.8 }, 1.9);

    // Animate hero metric counters
    setTimeout(() => {
      document.querySelectorAll('.hero-metrics .metric-value').forEach(el => {
        const target = parseInt(el.getAttribute('data-target'));
        const prefix = el.getAttribute('data-prefix') || '';
        const suffix = el.getAttribute('data-suffix') || '';
        animateValue(el, 0, target, 2000, prefix, suffix);
      });
    }, 1700);
  }

  animateHero();

  // ============================================
  // Smooth Scroll
  // ============================================
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ============================================
  // Counter Animation
  // ============================================
  function animateValue(el, start, end, duration, prefix = '', suffix = '') {
    const startTime = performance.now();

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4); // easeOutQuart
      const current = Math.floor(start + (end - start) * eased);

      if (end >= 1000000) {
        el.textContent = prefix + (current / 100000).toFixed(1) + 'L+';
      } else if (end >= 10000) {
        el.textContent = prefix + current.toLocaleString() + '+';
      } else {
        el.textContent = prefix + current.toLocaleString() + (suffix ? suffix : '+');
      }

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }

  // ============================================
  // Section Wipe Transitions (horizontal reveal)
  // ============================================
  gsap.utils.toArray('.section-wipe').forEach((wipe, i) => {
    // Alternate wipe direction for variety
    const fromRight = i % 2 === 1;
    wipe.style.transformOrigin = fromRight ? 'right center' : 'left center';

    gsap.to(wipe, {
      scaleX: 0,
      duration: 1.2,
      ease: 'power3.inOut',
      scrollTrigger: {
        trigger: wipe.parentElement,
        start: 'top 85%',
        toggleActions: 'play none none none'
      }
    });
  });



  // ============================================
  // ScrollTrigger Animations
  // ============================================

  // How It Works — Steps
  gsap.utils.toArray('.step').forEach((step, i) => {
    gsap.to(step, {
      opacity: 1,
      x: 0,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: step,
        start: 'top 85%',
        toggleActions: 'play none none none'
      },
      delay: i * 0.15
    });
  });

  // Timeline line grow animation
  const timelineLine = document.querySelector('.timeline-line');
  if (timelineLine) {
    gsap.from(timelineLine, {
      scaleY: 0,
      transformOrigin: 'top center',
      duration: 1.5,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: '.steps-timeline',
        start: 'top 80%',
        toggleActions: 'play none none none'
      }
    });
  }

  // Stats Cards
  const statsSection = document.querySelector('.stats-section');
  if (statsSection) {
    const statCards = gsap.utils.toArray('.stat-card');
    statCards.forEach((card, i) => {
      gsap.to(card, {
        opacity: 1,
        y: 0,
        duration: 0.7,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: card,
          start: 'top 85%',
          toggleActions: 'play none none none',
          onEnter: () => {
            // Animate the number
            const numEl = card.querySelector('.stat-number');
            if (numEl && !numEl.classList.contains('animated')) {
              const target = parseInt(numEl.getAttribute('data-target'));
              const prefix = numEl.getAttribute('data-prefix') || '';
              animateValue(numEl, 0, target, 2200, prefix);
              numEl.classList.add('animated');
            }

            // Animate the bar
            const barFill = card.querySelector('.stat-bar-fill');
            if (barFill) {
              const width = getComputedStyle(barFill).getPropertyValue('--fill-width');
              setTimeout(() => { barFill.style.width = width; }, 300);
            }
          }
        },
        delay: i * 0.12,
        onComplete: () => { gsap.set(card, { clearProps: 'all' }); card.classList.add('revealed'); }
      });
    });
  }

  // Call Cards
  gsap.utils.toArray('.call-card').forEach((card, i) => {
    gsap.to(card, {
      opacity: 1,
      y: 0,
      duration: 0.7,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: card,
        start: 'top 85%',
        toggleActions: 'play none none none'
      },
      delay: i * 0.15,
      onComplete: () => { gsap.set(card, { clearProps: 'all' }); card.classList.add('revealed'); }
    });
  });

  // Feature Cards
  gsap.utils.toArray('.feature-card').forEach((card, i) => {
    gsap.to(card, {
      opacity: 1,
      y: 0,
      duration: 0.7,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: card,
        start: 'top 85%',
        toggleActions: 'play none none none'
      },
      delay: i * 0.1,
      onComplete: () => { gsap.set(card, { clearProps: 'all' }); card.classList.add('revealed'); }
    });
  });

  // Section Headers
  gsap.utils.toArray('.section-header').forEach(header => {
    gsap.from(header, {
      opacity: 0,
      y: 40,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: header,
        start: 'top 85%',
        toggleActions: 'play none none none'
      }
    });
  });

  // Comparison Section Animations
  const compBefore = document.querySelector('.comparison-before');
  const compAfter = document.querySelector('.comparison-after');
  const compVS = document.querySelector('.comparison-vs');

  if (compBefore) {
    gsap.from(compBefore, {
      y: 40, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: '.comparison-container', start: 'top 85%', toggleActions: 'play none none none' }
    });
  }

  if (compAfter) {
    gsap.from(compAfter, {
      y: 40, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: '.comparison-container', start: 'top 85%', toggleActions: 'play none none none' },
      delay: 0.3
    });
  }

  if (compVS) {
    gsap.from(compVS, {
      scale: 0, opacity: 0, duration: 0.6, ease: 'back.out(2)',
      scrollTrigger: { trigger: '.comparison-container', start: 'top 85%', toggleActions: 'play none none none' },
      delay: 0.15
    });
  }

  // ============================================
  // Real-time Hero Stats Ticker
  // ============================================
  setTimeout(() => {
    const heroMetrics = document.querySelectorAll('.hero-metrics .metric-value');
    heroMetrics.forEach(el => {
      const isRupee = el.getAttribute('data-suffix') === 'L+';
      setInterval(() => {
        const text = el.textContent;
        if (isRupee) {
          const num = parseFloat(text.replace(/[^0-9.]/g, ''));
          if (!isNaN(num)) el.textContent = '₹' + (num + 0.1).toFixed(1) + 'L+';
        } else {
          const num = parseInt(text.replace(/[^0-9]/g, ''));
          if (!isNaN(num) && num > 0) el.textContent = (num + 1).toLocaleString() + '+';
        }
      }, Math.random() * 5000 + 3000);
    });
  }, 4000);

  // Auto-scroll transcript to show typing indicator
  const transcript = document.getElementById('liveTranscript');
  if (transcript) {
    setTimeout(() => { transcript.scrollTop = transcript.scrollHeight; }, 2000);
  }

  // CTA Section parallax-like reveal
  const ctaSection = document.querySelector('.cta-section');
  if (ctaSection) {
    gsap.from('.cta-content', {
      opacity: 0,
      scale: 0.9,
      y: 60,
      duration: 1,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: ctaSection,
        start: 'top 75%',
        toggleActions: 'play none none none'
      }
    });

    gsap.from('.cta-orb-1', {
      x: 200,
      y: -200,
      opacity: 0,
      duration: 1.5,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: ctaSection,
        start: 'top 80%',
        toggleActions: 'play none none none'
      }
    });

    gsap.from('.cta-orb-2', {
      x: -200,
      y: 200,
      opacity: 0,
      duration: 1.5,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: ctaSection,
        start: 'top 80%',
        toggleActions: 'play none none none'
      }
    });
  }

  // Footer columns stagger
  gsap.utils.toArray('.footer-grid > *').forEach((col, i) => {
    gsap.from(col, {
      opacity: 0,
      y: 30,
      duration: 0.6,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: '.footer',
        start: 'top 85%',
        toggleActions: 'play none none none'
      },
      delay: i * 0.12
    });
  });

  // ============================================
  // Live Timer
  // ============================================
  const liveTimerEl = document.getElementById('liveTimer');
  if (liveTimerEl) {
    let [minutes, seconds] = liveTimerEl.textContent.split(':').map(Number);

    setInterval(() => {
      seconds++;
      if (seconds >= 60) { minutes++; seconds = 0; }
      liveTimerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
  }

  // ============================================
  // Live Call Message Simulator
  // ============================================
  const liveTranscript = document.getElementById('liveTranscript');
  if (liveTranscript) {
    const grannyResponses = [
      "Arre beta, one minute... let me find my reading glasses...",
      "My grandson Rahul also works with computers. You know him?",
      "Can you speak louder? My hearing aid battery is running low...",
      "Beta, first tell me — have you eaten lunch? You sound so stressed...",
      "Wait wait wait... I'm writing this down on a paper... how do you spell 'PAN'?",
      "Oh hello? Hello? Are you still there? I dropped the phone..."
    ];

    const scammerResponses = [
      "Madam, please listen! This is very urgent, your account is at risk!",
      "Can you give me the OTP that was sent to your phone?",
      "I am from the government department. You MUST cooperate!",
      "This is the LAST chance madam, or your money will be gone!"
    ];

    let grannyIdx = 0;
    let scammerIdx = 0;
    let isGranny = true;

    setInterval(() => {
      if (isGranny && grannyIdx < grannyResponses.length) {
        addMessage('granny', grannyResponses[grannyIdx++]);
      } else if (!isGranny && scammerIdx < scammerResponses.length) {
        addMessage('scammer', scammerResponses[scammerIdx++]);
      }
      isGranny = !isGranny;
    }, 12000);

    function addMessage(type, text) {
      const icon = type === 'scammer' ? 'user-x' : 'heart-handshake';
      const speaker = type === 'scammer' ? 'Scammer' : 'Granny';
      
      const msg = document.createElement('div');
      msg.className = `msg msg-${type}`;
      msg.innerHTML = `
        <div class="msg-avatar"><i data-lucide="${icon}" style="width:16px;height:16px"></i></div>
        <div class="msg-bubble">
          <span class="msg-speaker">${speaker}</span>
          <p>${text}</p>
        </div>
      `;
      liveTranscript.appendChild(msg);
      lucide.createIcons({ nodes: [msg] });
      liveTranscript.scrollTop = liveTranscript.scrollHeight;
    }
  }

  // ============================================
  // Button Interactions
  // ============================================

  // Listen Live button
  const listenLiveBtn = document.getElementById('listenLiveBtn');
  if (listenLiveBtn) {
    listenLiveBtn.addEventListener('click', function() {
      const isPlaying = this.classList.toggle('playing');
      this.innerHTML = isPlaying
        ? '<span class="listen-dot"></span> Pause Live'
        : '<span class="listen-dot"></span> Listen Live';
    });
  }

  // Play Recording buttons
  document.querySelectorAll('.btn-play').forEach(btn => {
    btn.addEventListener('click', function() {
      const isPlaying = this.classList.toggle('playing');
      const iconName = isPlaying ? 'pause' : 'play';
      const label = isPlaying ? 'Pause Recording' : 'Play Recording';
      this.innerHTML = `<i data-lucide="${iconName}" style="width:16px;height:16px"></i> ${label}`;
      lucide.createIcons({ nodes: [this] });
    });
  });

  // ============================================
  // Scammer Data & Modal
  // ============================================
  const scammerData = {
    1: {
      type: 'Bank Fraud',
      phone: '+91-XXXX-789-234',
      location: 'Jamtara, Jharkhand, India',
      coordinates: '24.0367° N, 86.8032° E',
      callReason: 'Fake bank account compromise alert',
      duration: '42:18',
      keywords: ['OTP', 'account compromised', 'urgent', 'verify now', 'security team'],
      tactics: [
        'Caller posed as <strong>State Bank security officer</strong>',
        'Created false urgency claiming <strong>account breach</strong>',
        'Requested <strong>OTP and card details</strong> under pressure',
        'Threatened account freezing if not complied immediately'
      ],
      notes: 'Multiple similar calls traced to this location. Gang operates from rented apartment. Local police notified.',
      riskLevel: 'HIGH'
    },
    2: {
      type: 'Prize Scam',
      phone: '+91-XXXX-456-890',
      location: 'Noida, Uttar Pradesh, India',
      coordinates: '28.5355° N, 77.3910° E',
      callReason: 'Fake lottery winning notification',
      duration: '38:45',
      keywords: ['congratulations', 'won prize', 'processing fee', '25 lakhs', 'limited time'],
      tactics: [
        'Claimed victim won <strong>₹25 lakh lottery</strong>',
        'Demanded <strong>₹5000 processing fee</strong> upfront',
        'Provided fake government registration numbers',
        'Pressured for immediate payment via UPI'
      ],
      notes: 'Call center operating from commercial building. Uses VoIP to mask real number. 50+ victims reported.',
      riskLevel: 'CRITICAL'
    },
    3: {
      type: 'Tax Refund Scam',
      phone: '+91-XXXX-123-567',
      location: 'Kolkata, West Bengal, India',
      coordinates: '22.5726° N, 88.3639° E',
      callReason: 'Fraudulent tax refund claim',
      duration: '15:32 (LIVE)',
      keywords: ['tax refund', 'PAN card', 'income tax', 'government', 'urgent update'],
      tactics: [
        'Impersonating <strong>Income Tax Department</strong> officer',
        'Offering fake <strong>₹50,000 refund</strong>',
        'Requesting <strong>PAN and Aadhaar details</strong>',
        'Creating urgency with "last day" claims'
      ],
      notes: 'Currently active call. Scammer showing increasing frustration. Voice stress analysis indicates amateur operator.',
      riskLevel: 'MEDIUM'
    }
  };

  const modal = document.getElementById('scammerModal');
  const modalBody = document.getElementById('modalBody');
  const modalClose = document.getElementById('modalClose');

  document.querySelectorAll('.btn-info').forEach(btn => {
    btn.addEventListener('click', function() {
      const id = this.getAttribute('data-scammer-id');
      const data = scammerData[id];
      if (!data) return;

      const riskClass = data.riskLevel === 'HIGH' ? 'risk-high' : data.riskLevel === 'CRITICAL' ? 'risk-critical' : 'risk-medium';

      modalBody.innerHTML = `
        <div class="info-block">
          <div class="info-block-label">Scam Type</div>
          <div class="info-block-value">${data.type}</div>
          <span class="risk-badge ${riskClass}">⚠ Risk Level: ${data.riskLevel}</span>
        </div>

        <div class="info-block">
          <div class="info-block-label">Phone Number</div>
          <div class="info-block-value">${data.phone}</div>
          <div class="info-block-detail">Number may be spoofed or VoIP-based</div>
        </div>

        <div class="info-block">
          <div class="info-block-label">Call Origin</div>
          <div class="info-block-value">${data.location}</div>
          <div class="info-block-detail">Coordinates: ${data.coordinates}</div>
        </div>

        <div class="info-block">
          <div class="info-block-label">Scam Reason</div>
          <div class="info-block-value">${data.callReason}</div>
          <div class="info-block-detail">Duration: ${data.duration}</div>
        </div>

        <div class="info-block">
          <div class="info-block-label">Keywords Detected</div>
          <div style="margin-top:8px">${data.keywords.map(kw => `<span class="keyword-tag">${kw}</span>`).join(' ')}</div>
        </div>

        <div class="info-block">
          <div class="info-block-label">Scammer Tactics</div>
          <ul class="tactic-list">
            ${data.tactics.map(t => `<li>${t}</li>`).join('')}
          </ul>
        </div>

        <div class="info-block">
          <div class="info-block-label">Intelligence Notes</div>
          <div class="info-block-detail">${data.notes}</div>
        </div>
      `;

      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
      lucide.createIcons({ nodes: [modalBody] });
    });
  });

  function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }

  modalClose?.addEventListener('click', closeModal);
  modal?.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

  // ============================================
  // Magnetic Button Effect (premium touch)
  // ============================================
  document.querySelectorAll('.btn-primary, .nav-cta, .btn-cta-primary').forEach(btn => {
    btn.addEventListener('mousemove', function(e) {
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      this.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
    });

    btn.addEventListener('mouseleave', function() {
      this.style.transform = '';
    });
  });

  // ============================================
  // Tilt Effect on Cards (subtle, premium)
  // ============================================
  if (window.matchMedia('(pointer: fine)').matches) {
    document.querySelectorAll('.feature-card, .stat-card').forEach(card => {
      card.addEventListener('mousemove', function(e) {
        const rect = this.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        this.style.transform = `perspective(800px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateY(-8px)`;
      });

      card.addEventListener('mouseleave', function() {
        this.style.transform = '';
      });
    });
  }

  // ============================================
  // Text Reveal on Scroll (section titles)
  // ============================================
  gsap.utils.toArray('.section-title').forEach(title => {
    gsap.from(title, {
      backgroundPosition: '200% 50%',
      duration: 1.2,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: title,
        start: 'top 85%',
        toggleActions: 'play none none none'
      }
    });
  });

  // ============================================
  // Console Branding
  // ============================================
  console.log(
    '%c⚡ KARMA %c— Scam Defense System',
    'color: #C4F82A; font-size: 24px; font-weight: 900; font-family: "Space Grotesk", sans-serif;',
    'color: #888; font-size: 14px; font-weight: 400;'
  );
}
