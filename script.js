const menuToggle = document.getElementById('menuToggle');
const navLinks   = document.getElementById('navLinks');
const body       = document.body;

const navOverlay = document.createElement('div');
navOverlay.className = 'nav-overlay';
document.body.appendChild(navOverlay);

function openDropdown(dropdown) {
    dropdown.setAttribute('data-open', '');
    const btn = dropdown.querySelector('.nav-dropdown-toggle');
    if (btn) btn.setAttribute('aria-expanded', 'true');
    navOverlay.classList.add('active');
}

function closeDropdown(dropdown) {
    dropdown.removeAttribute('data-open');
    const btn = dropdown.querySelector('.nav-dropdown-toggle');
    if (btn) btn.setAttribute('aria-expanded', 'false');
}

function closeAllDropdowns() {
    document.querySelectorAll('.nav-dropdown[data-open]').forEach(closeDropdown);
    navOverlay.classList.remove('active');
}

function toggleMenu() {
    const isOpen = navLinks.classList.contains('active');
    menuToggle.classList.toggle('active');
    navLinks.classList.toggle('active');
    menuToggle.setAttribute('aria-expanded', String(!isOpen));
    body.style.overflow = !isOpen ? 'hidden' : 'auto';
    if (isOpen) closeAllDropdowns();
}

if (menuToggle) {
    menuToggle.addEventListener('click', toggleMenu);
}

document.querySelectorAll('.nav-dropdown').forEach(function(dropdown) {
    const toggle = dropdown.querySelector('.nav-dropdown-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        const isMobile = window.innerWidth <= 600;

        if (isMobile) {
            const wasOpen = dropdown.hasAttribute('data-open');
            wasOpen ? closeDropdown(dropdown) : openDropdown(dropdown);
        } else {
            const wasOpen = dropdown.hasAttribute('data-open');
            closeAllDropdowns();
            if (!wasOpen) openDropdown(dropdown);
        }
    });
});

navOverlay.addEventListener('click', closeAllDropdowns);

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeAllDropdowns();
        if (navLinks && navLinks.classList.contains('active')) toggleMenu();
    }
});

window.addEventListener('resize', function() {
    if (window.innerWidth > 600 && navLinks && navLinks.classList.contains('active')) {
        menuToggle.classList.remove('active');
        navLinks.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
        body.style.overflow = 'auto';
    }
    if (window.innerWidth <= 600) {
        navOverlay.classList.remove('active');
    }
});

document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            if (navLinks && navLinks.classList.contains('active')) toggleMenu();
            closeAllDropdowns();
            const headerOffset    = 80;
            const elementPosition = targetElement.getBoundingClientRect().top;
            const offsetPosition  = elementPosition + window.pageYOffset - headerOffset;
            window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
        }
    });
});

if ('loading' in HTMLImageElement.prototype) {
    document.querySelectorAll('img[loading="lazy"]').forEach(function(img) {
        img.loading = 'lazy';
    });
} else {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

document.querySelectorAll('script[data-src]').forEach(function(script) {
    script.src = script.dataset.src;
});

document.addEventListener('DOMContentLoaded', function() {
    initCarrossel();
});

function initCarrossel() {
    const slidesContainer = document.getElementById('carrosselSlides');
    const slides = document.querySelectorAll('.slide');
    const indicadoresContainer = document.getElementById('carrosselIndicadores');

    if (!slides.length) return;

    let currentIndex = 0;
    let slideInterval;
    let isTransitioning = false;

    function goToSlide(index) {
        if (isTransitioning) return;
        isTransitioning = true;
        if (index >= slides.length) { currentIndex = 0; }
        else if (index < 0) { currentIndex = slides.length - 1; }
        else { currentIndex = index; }
        if (slidesContainer) { slidesContainer.style.transform = `translateX(-${currentIndex * 100}%)`; }
        slides.forEach(function(slide) { slide.classList.remove('ativo'); });
        slides[currentIndex].classList.add('ativo');
        document.querySelectorAll('.indicador').forEach(function(ind, i) {
            ind.classList.toggle('ativo', i === currentIndex);
        });
        setTimeout(function() { isTransitioning = false; }, 500);
    }

    function nextSlide() { if (!isTransitioning) goToSlide(currentIndex + 1); }
    function prevSlide() { if (!isTransitioning) goToSlide(currentIndex - 1); }
    function startAutoSlide() { stopAutoSlide(); slideInterval = setInterval(nextSlide, 1500); }
    function stopAutoSlide() { if (slideInterval) clearInterval(slideInterval); }

    if (indicadoresContainer) {
        indicadoresContainer.innerHTML = '';
        slides.forEach(function(_, index) {
            const indicador = document.createElement('span');
            indicador.className = `indicador ${index === 0 ? 'ativo' : ''}`;
            indicador.setAttribute('data-slide', index);
            indicador.addEventListener('click', function() { stopAutoSlide(); goToSlide(index); startAutoSlide(); });
            indicadoresContainer.appendChild(indicador);
        });
    }

    const carrosselContainer = document.querySelector('.carrossel-container');
    if (carrosselContainer && !document.querySelector('.carrossel-seta')) {
        const setaEsquerda = document.createElement('button');
        setaEsquerda.className = 'carrossel-seta esquerda';
        setaEsquerda.innerHTML = '‹';
        setaEsquerda.setAttribute('aria-label', 'Slide anterior');
        const setaDireita = document.createElement('button');
        setaDireita.className = 'carrossel-seta direita';
        setaDireita.innerHTML = '›';
        setaDireita.setAttribute('aria-label', 'Próximo slide');
        setaEsquerda.addEventListener('click', function() { stopAutoSlide(); prevSlide(); startAutoSlide(); });
        setaDireita.addEventListener('click',  function() { stopAutoSlide(); nextSlide(); startAutoSlide(); });
        carrosselContainer.appendChild(setaEsquerda);
        carrosselContainer.appendChild(setaDireita);
    }

    goToSlide(0);
    startAutoSlide();

    if (carrosselContainer) {
        carrosselContainer.addEventListener('mouseenter', stopAutoSlide);
        carrosselContainer.addEventListener('mouseleave', startAutoSlide);
        carrosselContainer.addEventListener('touchstart', stopAutoSlide);
        carrosselContainer.addEventListener('touchend',   startAutoSlide);
    }

    return { next: nextSlide, prev: prevSlide, goTo: goToSlide, start: startAutoSlide, stop: stopAutoSlide };
}
