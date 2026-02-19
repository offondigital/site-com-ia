// Menu sanduíche
const menuToggle = document.getElementById('menuToggle');
const navLinks = document.getElementById('navLinks');
const body = document.body;

function toggleMenu() {
    menuToggle.classList.toggle('active');
    navLinks.classList.toggle('active');
    body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : 'auto';
}

if (menuToggle) {
    menuToggle.addEventListener('click', toggleMenu);
}

// Garantir rolagem suave para todas as âncoras
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        if (targetId === '#') return;

        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            // Fechar menu mobile se estiver aberto
            if (navLinks && navLinks.classList.contains('active')) {
                toggleMenu();
            }

            // Rolagem suave com offset para o header fixo
            const headerOffset = 80;
            const elementPosition = targetElement.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Fechar menu ao redimensionar para desktop
window.addEventListener('resize', () => {
    if (window.innerWidth > 600 && navLinks && navLinks.classList.contains('active')) {
        menuToggle.classList.remove('active');
        navLinks.classList.remove('active');
        body.style.overflow = 'auto';
    }
});

// Lazy loading para imagens (caso sejam adicionadas no futuro)
if ('loading' in HTMLImageElement.prototype) {
    const images = document.querySelectorAll('img[loading="lazy"]');
    images.forEach(img => {
        img.loading = 'lazy';
    });
} else {
    // Fallback para navegadores antigos (carregar script de lazy loading)
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';
    document.body.appendChild(script);
}

// Carregar scripts de forma assíncrona (se houver scripts com data-src)
const scripts = document.querySelectorAll('script[data-src]');
scripts.forEach(script => {
    script.src = script.dataset.src;
});

// ===== CARROSSEL AUTOMÁTICO 1.5s =====
document.addEventListener('DOMContentLoaded', function() {
    initCarrossel();
});

function initCarrossel() {
    const slidesContainer = document.getElementById('carrosselSlides');
    const slides = document.querySelectorAll('.slide');
    const indicadoresContainer = document.getElementById('carrosselIndicadores');
    
    // Se não existirem slides na página, não executa
    if (!slides.length) return;
    
    let currentIndex = 0;
    let slideInterval;
    let isTransitioning = false;

    // Função para ir para um slide específico
    function goToSlide(index) {
        if (isTransitioning) return;
        isTransitioning = true;
        
        // Loop circular
        if (index >= slides.length) {
            currentIndex = 0;
        } else if (index < 0) {
            currentIndex = slides.length - 1;
        } else {
            currentIndex = index;
        }

        // Move o container de slides
        if (slidesContainer) {
            slidesContainer.style.transform = `translateX(-${currentIndex * 100}%)`;
        }

        // Remove classe ativo de todos os slides
        slides.forEach(slide => {
            slide.classList.remove('ativo');
        });
        
        // Adiciona classe ativo ao slide atual
        slides[currentIndex].classList.add('ativo');

        // Atualiza indicadores
        document.querySelectorAll('.indicador').forEach((ind, i) => {
            if (i === currentIndex) {
                ind.classList.add('ativo');
            } else {
                ind.classList.remove('ativo');
            }
        });

        // Libera transição após o tempo da animação
        setTimeout(() => {
            isTransitioning = false;
        }, 500);
    }

    // Função para avançar para o próximo slide
    function nextSlide() {
        if (!isTransitioning) {
            goToSlide(currentIndex + 1);
        }
    }

    // Função para voltar ao slide anterior
    function prevSlide() {
        if (!isTransitioning) {
            goToSlide(currentIndex - 1);
        }
    }

    // Função para iniciar o intervalo automático
    function startAutoSlide() {
        stopAutoSlide();
        slideInterval = setInterval(nextSlide, 1500); // 3.0 segundos
    }

    // Função para parar o intervalo automático
    function stopAutoSlide() {
        if (slideInterval) {
            clearInterval(slideInterval);
        }
    }

    // Cria indicadores se o container existir
    if (indicadoresContainer) {
        indicadoresContainer.innerHTML = ''; // Limpa indicadores existentes
        slides.forEach((_, index) => {
            const indicador = document.createElement('span');
            indicador.className = `indicador ${index === 0 ? 'ativo' : ''}`;
            indicador.setAttribute('data-slide', index);
            indicador.addEventListener('click', () => {
                stopAutoSlide();
                goToSlide(index);
                startAutoSlide();
            });
            indicadoresContainer.appendChild(indicador);
        });
    }

    // Adiciona setas de navegação (opcional)
    const carrosselContainer = document.querySelector('.carrossel-container');
    if (carrosselContainer && !document.querySelector('.carrossel-seta')) {
        // Seta esquerda
        const setaEsquerda = document.createElement('button');
        setaEsquerda.className = 'carrossel-seta esquerda';
        setaEsquerda.innerHTML = '‹';
        setaEsquerda.setAttribute('aria-label', 'Slide anterior');
        
        // Seta direita
        const setaDireita = document.createElement('button');
        setaDireita.className = 'carrossel-seta direita';
        setaDireita.innerHTML = '›';
        setaDireita.setAttribute('aria-label', 'Próximo slide');
        
        // Eventos das setas
        setaEsquerda.addEventListener('click', () => {
            stopAutoSlide();
            prevSlide();
            startAutoSlide();
        });
        
        setaDireita.addEventListener('click', () => {
            stopAutoSlide();
            nextSlide();
            startAutoSlide();
        });
        
        carrosselContainer.appendChild(setaEsquerda);
        carrosselContainer.appendChild(setaDireita);
    }

    // Inicia o carrossel
    goToSlide(0);
    startAutoSlide();

    // Pausar quando o mouse está sobre o carrossel
    if (carrosselContainer) {
        carrosselContainer.addEventListener('mouseenter', stopAutoSlide);
        carrosselContainer.addEventListener('mouseleave', startAutoSlide);
        
        // Pausar em dispositivos touch
        carrosselContainer.addEventListener('touchstart', stopAutoSlide);
        carrosselContainer.addEventListener('touchend', startAutoSlide);
    }

    // Retorna funções úteis (para debug, se necessário)
    return {
        next: nextSlide,
        prev: prevSlide,
        goTo: goToSlide,
        start: startAutoSlide,
        stop: stopAutoSlide
    };
}
