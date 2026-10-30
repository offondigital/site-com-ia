/* Popup "Auditoria gratuita do seu site" - InovaSEO
   Desktop: janela ao intencionar sair (mouse sobe para fora da página), após 15 s.
   Celular: faixa NÃO bloqueante na parte de baixo, após 20 s ou 50% de rolagem (sem tela cheia, por causa do Google).
   Envia o lead (site + WhatsApp) ao Apps Script, que cria a linha no CRM e avisa no Telegram. */
(function () {
  'use strict';
  var AVISO = 'https://script.google.com/macros/s/AKfycbxcoFgihWxI51tOExb75D3I3rE8UBhin-Z_xa5PfwPd4Elz5tx2bXYJy83WP3UrG5G1/exec';
  var WHATS = '5545988195137';
  var DIAS_DISPENSA = 7, DIAS_ENVIADO = 30;
  var SEM_SITE = true; /* opção "Ainda não tenho site": ligar (true) só depois de atualizar o Apps Script */

  var ATIVO = true;
  if (!ATIVO) return;

  var path = location.pathname;
  if (/^\/(propostas|crm|auditorias|privacidade)(\/|$)/.test(path)) return;

  function ls(k, v) {
    try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; }
  }
  /* link de teste: /qualquer-pagina/?popup=teste abre o popup em ~3 s, ignorando modo dono, "já fechou" e "já enviou"; não grava nada no aparelho */
  var TESTE = /[?&]popup=teste(&|$)/.test(location.search);
  if (!TESTE && ls('prop_dono')) return; // modo dono (?dono=1): não incomoda e não mede
  function recente(k, dias) { if (TESTE) return false; var t = parseInt(ls(k) || '0', 10); return t && (Date.now() - t) < dias * 864e5; }
  if (recente('pp_enviado', DIAS_ENVIADO) || recente('pp_dispensado', DIAS_DISPENSA)) return;
  var gravar = function (k, v) { if (!TESTE) ls(k, v); };

  function ev(nome, extra) {
    try { if (typeof window.gtag === 'function') window.gtag('event', nome, extra || {}); } catch (e) {}
  }

  var celular = !window.matchMedia('(hover: hover) and (pointer: fine)').matches || window.innerWidth < 900;
  var aberto = false, caixa = null, ultimoFoco = null, inicio = Date.now(), abertoEm = 0;

  /* ---------- estilo ---------- */
  var css = '' +
    '.pp-fundo{position:fixed;inset:0;background:rgba(15,23,42,.55);z-index:99998;opacity:0;transition:opacity .2s}' +
    '.pp-fundo.on{opacity:1}' +
    '.pp{position:fixed;z-index:99999;background:#fff;color:hsl(215,50%,15%);font-family:Inter,system-ui,sans-serif;box-shadow:0 20px 60px rgba(15,23,42,.35);' +
    'opacity:0;transition:opacity .2s,transform .25s}' +
    '.pp.on{opacity:1;transform:none}' +
    '.pp--modal{left:50%;top:50%;width:min(440px,calc(100vw - 32px));border-radius:16px;padding:28px 26px 22px;transform:translate(-50%,-46%)}' +
    '.pp--modal.on{transform:translate(-50%,-50%)}' +
    '.pp--faixa{left:0;right:0;bottom:0;border-radius:16px 16px 0 0;padding:18px 16px calc(16px + env(safe-area-inset-bottom));transform:translateY(24px)}' +
    '.pp h2{margin:0 0 6px;font-size:1.25rem;line-height:1.25;font-weight:700;padding-right:28px}' +
    '.pp--faixa h2{font-size:1.05rem}' +
    '.pp p{margin:0 0 14px;font-size:.92rem;line-height:1.45;color:hsl(215,20%,35%)}' +
    '.pp--faixa p{font-size:.85rem;margin-bottom:10px}' +
    '.pp label{display:block;font-size:.8rem;font-weight:600;margin:0 0 4px}' +
    '.pp input[type=text],.pp input[type=tel],.pp input[type=url]{width:100%;box-sizing:border-box;font:inherit;font-size:16px;padding:11px 12px;border:1px solid hsl(214,32%,80%);border-radius:10px;margin:0 0 10px;background:#fff;color:inherit}' +
    '.pp input:focus{outline:2px solid hsl(217,91%,60%);outline-offset:1px;border-color:transparent}' +
    '.pp .pp-ok{display:block;width:100%;border:0;cursor:pointer;font:inherit;font-weight:700;font-size:1rem;padding:13px 16px;border-radius:10px;background:hsl(217,91%,50%);color:#fff}' +
    '.pp .pp-ok:hover{background:hsl(221,83%,43%)}' +
    '.pp .pp-ok[disabled]{opacity:.6;cursor:wait}' +
    '.pp .pp-x{position:absolute;top:10px;right:10px;width:36px;height:36px;border:0;border-radius:50%;background:transparent;cursor:pointer;font-size:24px;line-height:1;color:hsl(215,20%,40%)}' +
    '.pp .pp-x:hover{background:hsl(210,30%,94%)}' +
    '.pp .pp-mini{margin:12px 0 0;text-align:center;font-size:.82rem}' +
    '.pp .pp-mini a{color:hsl(221,83%,40%);text-decoration:underline}' +
    '.pp .pp-lgpd{margin:10px 0 0;font-size:.72rem;line-height:1.35;color:hsl(215,15%,45%)}' +
    '.pp .pp-lgpd a{color:inherit;text-decoration:underline}' +
    '.pp .pp-semsite-p{margin:-4px 0 10px;font-size:.82rem}' +
    '.pp .pp-semsite{color:hsl(221,83%,40%);text-decoration:underline;cursor:pointer}' +
    '.pp .pp-erro{color:#b91c1c;font-size:.8rem;margin:-4px 0 8px;min-height:0}' +
    '.pp .pp-iscas{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}' +
    '.pp--compacta form,.pp--compacta .pp-mini,.pp--compacta .pp-lgpd{display:none}' +
    '.pp .pp-abre{display:none}' +
    '.pp--compacta .pp-abre{display:block;margin:0}' +
    '.pp--compacta p.pp-sub{display:none}' +
    '.pp--compacta h2{font-size:1rem;margin-bottom:10px}' +
    '@media (prefers-reduced-motion:reduce){.pp,.pp-fundo{transition:none}}';

  function injetarCss() {
    var s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
  }

  /* ---------- abrir / fechar ---------- */
  function abrir(origem) {
    if (aberto) return; aberto = true;
    injetarCss();
    ultimoFoco = document.activeElement; abertoEm = Date.now();
    var modal = !celular;
    if (modal) {
      var f = document.createElement('div'); f.className = 'pp-fundo'; f.id = 'pp-fundo';
      f.addEventListener('click', function () { fechar('fundo'); });
      document.body.appendChild(f);
      requestAnimationFrame(function () { f.classList.add('on'); });
    }
    caixa = document.createElement('div');
    caixa.className = 'pp ' + (modal ? 'pp--modal' : 'pp--faixa');
    if (!modal) caixa.className += ' pp--compacta';
    caixa.setAttribute('role', 'dialog');
    caixa.setAttribute('aria-labelledby', 'pp-t');
    if (modal) caixa.setAttribute('aria-modal', 'true');
    caixa.innerHTML =
      '<button type="button" class="pp-x" aria-label="Fechar">&times;</button>' +
      '<div id="pp-conteudo">' +
      '<h2 id="pp-t">Seu site está aparecendo pra quem busca no Google?</h2>' +
      '<p class="pp-sub">Receba uma <strong>auditoria gratuita</strong> do seu site em até 24 h e veja o que está impedindo sua empresa de aparecer na primeira página.</p>' +
      '<button type="button" class="pp-ok pp-abre">Quero minha auditoria grátis</button>' +
      '<form novalidate>' +
      '<label for="pp-site">Endereço do seu site</label>' +
      '<input id="pp-site" name="site" type="text" inputmode="url" autocomplete="url" placeholder="www.suaempresa.com.br" required>' +
      (SEM_SITE ? '<p class="pp-semsite-p"><a href="#" class="pp-semsite" role="button">Ainda não tenho site</a></p>' : '') +
      '<label for="pp-zap">Seu WhatsApp (com DDD)</label>' +
      '<input id="pp-zap" name="whatsapp" type="tel" inputmode="tel" autocomplete="tel" placeholder="(45) 99999-9999" required>' +
      '<div class="pp-iscas" aria-hidden="true"><label>Não preencha<input type="text" name="confirme_email" tabindex="-1" autocomplete="off"></label></div>' +
      '<div class="pp-erro" role="alert"></div>' +
      '<button type="submit" class="pp-ok">Quero minha auditoria grátis</button>' +
      '</form>' +
      '<p class="pp-mini">Prefere conversar? <a href="https://wa.me/' + WHATS + '?text=' + encodeURIComponent('Olá! Quero marcar uma reunião sobre o site da minha empresa.') + '" target="_blank" rel="noopener" data-pp="reuniao">Marcar uma reunião</a></p>' +
      '<p class="pp-lgpd">Ao enviar, você autoriza o contato por WhatsApp sobre a auditoria. <a href="/privacidade/">Política de privacidade</a>.</p>' +
      '</div>';
    document.body.appendChild(caixa);
    requestAnimationFrame(function () { caixa.classList.add('on'); });

    caixa.querySelector('.pp-x').addEventListener('click', function () { fechar('x'); });
    caixa.querySelector('form').addEventListener('submit', enviar);
    var tg = caixa.querySelector('.pp-semsite');
    if (tg) tg.addEventListener('click', function (ev2) {
      ev2.preventDefault();
      var f = caixa.querySelector('form'), semSite = f.getAttribute('data-sem-site') !== '1';
      f.setAttribute('data-sem-site', semSite ? '1' : '0');
      caixa.querySelector('label[for="pp-site"]').textContent = semSite ? 'Nome da empresa e cidade' : 'Endereço do seu site';
      var inp = caixa.querySelector('#pp-site');
      inp.placeholder = semSite ? 'Ex.: Clínica Sol, Cascavel' : 'www.suaempresa.com.br';
      inp.setAttribute('inputmode', semSite ? 'text' : 'url'); inp.setAttribute('autocomplete', semSite ? 'organization' : 'url');
      inp.value = ''; inp.focus();
      tg.textContent = semSite ? 'Tenho site' : 'Ainda não tenho site';
      caixa.querySelector('.pp-sub').innerHTML = semSite
        ? 'Sem problema. Receba uma <strong>análise gratuita</strong> de como sua empresa aparece hoje no Google e do que um site traria de clientes.'
        : 'Receba uma <strong>auditoria gratuita</strong> do seu site em até 24 h e veja o que está impedindo sua empresa de aparecer na primeira página.';
      caixa.querySelector('.pp-ok:not(.pp-abre)').textContent = semSite ? 'Quero minha análise grátis' : 'Quero minha auditoria grátis';
      caixa.querySelector('.pp-erro').textContent = '';
      ev('popup_sem_site', { ativo: semSite, pagina: path });
    });
    caixa.querySelector('.pp-abre').addEventListener('click', function () {
      caixa.classList.remove('pp--compacta');
      var i = caixa.querySelector('#pp-site'); if (i) i.focus();
    });
    caixa.querySelector('[data-pp="reuniao"]').addEventListener('click', function () {
      ev('popup_reuniao', { pagina: path });
      ev('generate_lead', { lead_source: 'popup_reuniao', pagina: path });
      gravar('pp_enviado', String(Date.now()));
    });
    document.addEventListener('keydown', teclas);
    if (modal) setTimeout(function () { var i = caixa && caixa.querySelector('#pp-site'); if (i) i.focus(); }, 250);
    ev('popup_exibido', { gatilho: origem, formato: modal ? 'janela' : 'faixa', pagina: path });
  }

  function teclas(e) {
    if (e.key === 'Escape') { fechar('esc'); return; }
    if (e.key === 'Tab' && caixa && !celular) { // mantém o foco dentro da janela
      var els = caixa.querySelectorAll('button,a[href],input:not([tabindex="-1"])');
      if (!els.length) return;
      var a = els[0], b = els[els.length - 1];
      if (e.shiftKey && document.activeElement === a) { e.preventDefault(); b.focus(); }
      else if (!e.shiftKey && document.activeElement === b) { e.preventDefault(); a.focus(); }
    }
  }

  function fechar(como) {
    if (!aberto) return; aberto = false;
    document.removeEventListener('keydown', teclas);
    if (!recente('pp_enviado', DIAS_ENVIADO)) { gravar('pp_dispensado', String(Date.now())); ev('popup_fechado', { como: como, pagina: path }); }
    var f = document.getElementById('pp-fundo');
    if (caixa) caixa.classList.remove('on');
    if (f) f.classList.remove('on');
    setTimeout(function () { if (caixa) caixa.remove(); if (f) f.remove(); caixa = null; }, 260);
    try { if (ultimoFoco && ultimoFoco.focus) ultimoFoco.focus(); } catch (e) {}
  }

  /* ---------- envio ---------- */
  function siteValido(v) { return /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}(\/\S*)?$/i.test(v.trim()); }
  function zapValido(v) { var n = v.replace(/\D/g, ''); if (n.indexOf('55') === 0 && n.length > 11) n = n.slice(2); return n.length === 10 || n.length === 11; }

  function enviar(e) {
    e.preventDefault();
    var f = e.target, erro = f.querySelector('.pp-erro');
    var site = f.site.value.trim(), zap = f.whatsapp.value.trim();
    var semSite = f.getAttribute('data-sem-site') === '1';
    if (semSite ? site.length < 4 : !siteValido(site)) { erro.textContent = semSite ? 'Informe o nome da empresa e a cidade, por exemplo Clínica Sol, Cascavel' : 'Informe o endereço do site, por exemplo www.suaempresa.com.br'; f.site.focus(); return; }
    if (!zapValido(zap)) { erro.textContent = 'Informe o WhatsApp com DDD, por exemplo (45) 99999-9999'; f.whatsapp.focus(); return; }
    erro.textContent = '';
    var btn = f.querySelector('.pp-ok'); btn.disabled = true; btn.textContent = 'Enviando…';
    var corpo = JSON.stringify({
      perfil_acesso: 'lead_popup', cliente: 'lead popup', site: site, sem_site: semSite, whatsapp: zap,
      pagina: path, confirme_email: f.confirme_email.value, data_hora: new Date().toISOString()
    });
    var ok = function () {
      gravar('pp_enviado', String(Date.now()));
      ev('popup_enviado', { pagina: path, sem_site: semSite });
      ev('generate_lead', { lead_source: semSite ? 'popup_sem_site' : 'popup', pagina: path });
      var c = caixa && caixa.querySelector('#pp-conteudo');
      if (c) c.innerHTML = '<h2 id="pp-t">Recebemos seu pedido!</h2><p>' + (semSite ? 'Vamos analisar como a empresa <strong></strong> aparece no Google e chamar você no WhatsApp em até 24 h.' : 'Vamos analisar o site <strong></strong> e chamar você no WhatsApp em até 24 h.') + '</p>' +
        '<button type="button" class="pp-ok" id="pp-fim">Fechar</button>';
      if (c) { c.querySelector('strong').textContent = site; c.querySelector('#pp-fim').addEventListener('click', function () { fechar('concluido'); }); }
    };
    var falha = function () {
      btn.disabled = false; btn.textContent = semSite ? 'Quero minha análise grátis' : 'Quero minha auditoria grátis';
      erro.innerHTML = 'Não conseguimos enviar agora. <a href="https://wa.me/' + WHATS + '?text=' + encodeURIComponent((semSite ? 'Olá! Ainda não tenho site e quero a análise gratuita da minha empresa: ' : 'Olá! Quero a auditoria gratuita do site ') + site) + '" target="_blank" rel="noopener">Peça pelo WhatsApp</a>.';
    };
    try {
      fetch(AVISO, { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: corpo, keepalive: true }).then(ok, falha);
    } catch (x) { falha(); }
  }

  /* celular: tocar na página, fora da faixa, recolhe o formulário; tocar de novo fecha (a janela do desktop já fecha ao clicar no fundo) */
  document.addEventListener('click', function (e) {
    if (!aberto || !caixa || !celular) return;
    if (Date.now() - abertoEm < 600) return;      // o mesmo toque que abriu não conta
    if (caixa.contains(e.target)) return;
    if (!caixa.classList.contains('pp--compacta') && caixa.querySelector('form') && caixa.querySelector('#pp-fim') === null) {
      caixa.classList.add('pp--compacta');        // só recolhe; o que foi digitado fica guardado
      ev('popup_recolhido', { pagina: path });
    } else {
      fechar('toque_fora');
    }
  }, true);

  /* quem já clicou no WhatsApp do site não recebe o popup nas próximas visitas */
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href*="wa.me"]');
    if (a && !a.closest('.pp')) { gravar('pp_enviado', String(Date.now())); if (aberto) fechar('whatsapp'); }
  });

  /* ---------- gatilhos ---------- */
  if (TESTE) { setTimeout(function () { abrir('teste'); }, 3000); }
  else if (!celular) {
    document.addEventListener('mouseout', function (e) {
      if (aberto || e.relatedTarget || e.clientY > 0) return;
      if (Date.now() - inicio < 15000) return;
      abrir('saida');
    });
  } else {
    var disparado = false;
    var dispara = function (o) { if (disparado || aberto) return; disparado = true; abrir(o); };
    setTimeout(function () { dispara('tempo'); }, 20000);
    window.addEventListener('scroll', function () {
      var h = document.documentElement, rolou = (window.scrollY + window.innerHeight) / Math.max(h.scrollHeight, 1);
      if (rolou >= 0.5 && Date.now() - inicio > 8000) dispara('rolagem');
    }, { passive: true });
  }
})();
