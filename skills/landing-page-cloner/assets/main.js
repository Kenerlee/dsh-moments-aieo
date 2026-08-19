/* ============================================
   LANDING PAGE CLONE - JAVASCRIPT TEMPLATE
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
  
  /* ============================================
     MOBILE NAVIGATION
     ============================================ */
  const navToggle = document.getElementById('nav-toggle');
  const navClose = document.getElementById('nav-close');
  const navMenu = document.getElementById('nav-menu');
  
  // Show menu
  if (navToggle) {
    navToggle.addEventListener('click', () => {
      navMenu.classList.add('active');
    });
  }
  
  // Hide menu
  if (navClose) {
    navClose.addEventListener('click', () => {
      navMenu.classList.remove('active');
    });
  }
  
  // Close menu when clicking on nav links
  const navLinks = document.querySelectorAll('.nav__link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navMenu.classList.remove('active');
    });
  });
  
  /* ============================================
     STICKY HEADER
     ============================================ */
  const header = document.getElementById('header');
  const scrollThreshold = 100;
  
  function handleScroll() {
    if (window.scrollY > scrollThreshold) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }
  
  window.addEventListener('scroll', handleScroll);
  
  /* ============================================
     ACTIVE LINK ON SCROLL
     ============================================ */
  const sections = document.querySelectorAll('section[id]');
  
  function scrollActive() {
    const scrollY = window.pageYOffset;
    
    sections.forEach(section => {
      const sectionHeight = section.offsetHeight;
      const sectionTop = section.offsetTop - 150;
      const sectionId = section.getAttribute('id');
      const navLink = document.querySelector(`.nav__link[href="#${sectionId}"]`);
      
      if (navLink) {
        if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
          navLink.classList.add('active');
        } else {
          navLink.classList.remove('active');
        }
      }
    });
  }
  
  window.addEventListener('scroll', scrollActive);
  
  /* ============================================
     SMOOTH SCROLL
     ============================================ */
  const smoothLinks = document.querySelectorAll('a[href^="#"]');
  
  smoothLinks.forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        const headerHeight = header.offsetHeight;
        const targetPosition = targetElement.offsetTop - headerHeight;
        
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
  
  /* ============================================
     SCROLL REVEAL ANIMATION
     ============================================ */
  const revealElements = document.querySelectorAll('.reveal');
  
  function scrollReveal() {
    const windowHeight = window.innerHeight;
    
    revealElements.forEach(element => {
      const elementTop = element.getBoundingClientRect().top;
      const revealPoint = 150;
      
      if (elementTop < windowHeight - revealPoint) {
        element.classList.add('active');
      }
    });
  }
  
  window.addEventListener('scroll', scrollReveal);
  scrollReveal(); // Initial check
  
  /* ============================================
     FORM HANDLING
     ============================================ */
  const contactForm = document.getElementById('contact-form');
  
  if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      // Get form data
      const formData = new FormData(this);
      const data = Object.fromEntries(formData);
      
      // Validate
      if (!validateForm(data)) {
        return;
      }
      
      // Show loading state
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = '提交中...';
      submitBtn.disabled = true;
      
      // Simulate form submission (replace with actual API call)
      setTimeout(() => {
        alert('感谢您的留言！我们会尽快与您联系。');
        this.reset();
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
      }, 1500);
    });
  }
  
  function validateForm(data) {
    // Name validation
    if (!data.name || data.name.trim().length < 2) {
      alert('请输入有效的姓名');
      return false;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!data.email || !emailRegex.test(data.email)) {
      alert('请输入有效的邮箱地址');
      return false;
    }
    
    // Message validation
    if (!data.message || data.message.trim().length < 10) {
      alert('请输入至少10个字符的留言');
      return false;
    }
    
    return true;
  }
  
  /* ============================================
     COUNTER ANIMATION (if needed)
     ============================================ */
  function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    
    function updateCounter() {
      start += increment;
      if (start < target) {
        element.textContent = Math.floor(start);
        requestAnimationFrame(updateCounter);
      } else {
        element.textContent = target;
      }
    }
    
    updateCounter();
  }
  
  // Usage: 
  // const counters = document.querySelectorAll('.counter');
  // counters.forEach(counter => {
  //   const target = parseInt(counter.getAttribute('data-target'));
  //   animateCounter(counter, target);
  // });
  
  /* ============================================
     TESTIMONIAL SLIDER (if needed)
     ============================================ */
  // Basic slider functionality
  // Can be replaced with Swiper.js or other libraries
  
  const sliderContainer = document.querySelector('.testimonials__slider');
  if (sliderContainer && sliderContainer.children.length > 3) {
    // Implement slider if needed
    // Or integrate Swiper.js
  }
  
  /* ============================================
     LAZY LOADING IMAGES
     ============================================ */
  const lazyImages = document.querySelectorAll('img[data-src]');
  
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          observer.unobserve(img);
        }
      });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
  } else {
    // Fallback for older browsers
    lazyImages.forEach(img => {
      img.src = img.dataset.src;
    });
  }
  
  /* ============================================
     PARALLAX EFFECT (if needed)
     ============================================ */
  const parallaxElements = document.querySelectorAll('.parallax');
  
  if (parallaxElements.length > 0) {
    window.addEventListener('scroll', () => {
      const scrolled = window.pageYOffset;
      
      parallaxElements.forEach(element => {
        const speed = element.dataset.speed || 0.5;
        element.style.transform = `translateY(${scrolled * speed}px)`;
      });
    });
  }
  
  /* ============================================
     MODAL FUNCTIONALITY (if needed)
     ============================================ */
  const modalTriggers = document.querySelectorAll('[data-modal]');
  const modals = document.querySelectorAll('.modal');
  
  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const modalId = trigger.dataset.modal;
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });
  
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal || e.target.classList.contains('modal__close')) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });
  
  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      modals.forEach(modal => {
        modal.classList.remove('active');
      });
      document.body.style.overflow = '';
    }
  });
  
  /* ============================================
     BACK TO TOP BUTTON (if needed)
     ============================================ */
  const backToTop = document.getElementById('back-to-top');
  
  if (backToTop) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 500) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
    });
    
    backToTop.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }
  
  /* ============================================
     ACCESSIBILITY
     ============================================ */
  // Focus trap for modals
  function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    element.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstFocusable) {
            lastFocusable.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            firstFocusable.focus();
            e.preventDefault();
          }
        }
      }
    });
  }
  
  /* ============================================
     INITIALIZATION COMPLETE
     ============================================ */
  console.log('Landing page scripts initialized');
  
});
