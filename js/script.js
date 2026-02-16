/* ========================================
   Pagi IA SEO - JavaScript Puro
   Versão HTML/CSS/JS do site
======================================== */

document.addEventListener('DOMContentLoaded', function() {
  // ========================================
  // Mobile Menu Toggle
  // ========================================
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  const menuIconOpen = document.getElementById('menu-icon-open');
  const menuIconClose = document.getElementById('menu-icon-close');

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', function() {
      const isOpen = mobileMenu.classList.contains('active');
      
      if (isOpen) {
        mobileMenu.classList.remove('active');
        menuIconOpen.style.display = 'block';
        menuIconClose.style.display = 'none';
      } else {
        mobileMenu.classList.add('active');
        menuIconOpen.style.display = 'none';
        menuIconClose.style.display = 'block';
      }
    });

    // Close menu when clicking on a link
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(function(link) {
      link.addEventListener('click', function() {
        mobileMenu.classList.remove('active');
        menuIconOpen.style.display = 'block';
        menuIconClose.style.display = 'none';
      });
    });
  }

  // ========================================
  // Smooth Scroll for Anchor Links
  // ========================================
  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  
  anchorLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        
        if (target) {
          const headerHeight = document.querySelector('.header').offsetHeight;
          const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;
          
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      }
    });
  });

  // ========================================
  // Intersection Observer for Animations
  // ========================================
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const animateOnScroll = function(entries, observer) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-visible');
        observer.unobserve(entry.target);
      }
    });
  };

  const observer = new IntersectionObserver(animateOnScroll, observerOptions);

  // Observe elements with animation classes
  const animatedElements = document.querySelectorAll('.animate-on-scroll');
  animatedElements.forEach(function(el) {
    observer.observe(el);
  });

  // ========================================
  // Pricing Cards Hover Effect
  // ========================================
  const pricingCards = document.querySelectorAll('.pricing-card');
  
  pricingCards.forEach(function(card) {
    card.addEventListener('mouseenter', function() {
      this.style.transform = this.classList.contains('popular') 
        ? 'scale(1.05) translateY(-8px)' 
        : 'translateY(-8px)';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = this.classList.contains('popular') 
        ? 'scale(1.05)' 
        : '';
    });
  });

  // ========================================
  // Header Background on Scroll
  // ========================================
  const header = document.querySelector('.header');
  
  window.addEventListener('scroll', function() {
    if (window.scrollY > 50) {
      header.style.boxShadow = 'var(--shadow-md)';
    } else {
      header.style.boxShadow = 'none';
    }
  });

  // ========================================
  // Stats Counter Animation
  // ========================================
  const statsObserverOptions = {
    threshold: 0.5
  };

  const animateCounter = function(el, target, suffix) {
    let current = 0;
    const increment = target / 50;
    const duration = 1500;
    const stepTime = duration / 50;

    const timer = setInterval(function() {
      current += increment;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      
      if (Number.isInteger(target)) {
        el.textContent = Math.floor(current) + suffix;
      } else {
        el.textContent = current.toFixed(0) + suffix;
      }
    }, stepTime);
  };

  const statsObserver = new IntersectionObserver(function(entries, observer) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        const statValues = entry.target.querySelectorAll('.hero-stat-value');
        
        statValues.forEach(function(stat) {
          const text = stat.textContent;
          const numMatch = text.match(/[\d.]+/);
          
          if (numMatch) {
            const num = parseFloat(numMatch[0]);
            const suffix = text.replace(numMatch[0], '');
            stat.textContent = '0' + suffix;
            animateCounter(stat, num, suffix);
          }
        });
        
        observer.unobserve(entry.target);
      }
    });
  }, statsObserverOptions);

  const heroStats = document.querySelector('.hero-stats');
  if (heroStats) {
    statsObserver.observe(heroStats);
  }

  // ========================================
  // Button Click Effects
  // ========================================
  const buttons = document.querySelectorAll('.btn');
  
  buttons.forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      // Create ripple effect
      const ripple = document.createElement('span');
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255,255,255,0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
      `;
      
      this.style.position = 'relative';
      this.style.overflow = 'hidden';
      this.appendChild(ripple);
      
      setTimeout(function() {
        ripple.remove();
      }, 600);
    });
  });

  // Add ripple animation to stylesheet
  const style = document.createElement('style');
  style.textContent = `
    @keyframes ripple {
      to {
        transform: scale(4);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);

  // ========================================
  // Console Welcome Message
  // ========================================
  console.log('%c Pagi IA SEO ', 'background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; font-size: 20px; font-weight: bold; padding: 10px 20px; border-radius: 5px;');
  console.log('%c Versão HTML/CSS/JS Puro', 'color: #64748b; font-size: 12px;');
});

