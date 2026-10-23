#!/usr/bin/env python3
"""Gera o blog da InovaSEO a partir de _blog-src/ (pasta com _ para o GitHub Pages nao publicar os rascunhos).

Uso:
  python3 _blog-src/build.py          publica so os posts com data <= hoje (Brasilia) em blog/
  python3 _blog-src/build.py --all    gera todos os posts em blog-preview/ (para revisar)

Cada post vive em _blog-src/posts/<slug>.html (corpo) + entrada em posts.json.
Atalhos usados no corpo:
  [[cta-wa posicao | Titulo | Texto | Botao]]     botao de WhatsApp com UTMs
  [[cta-link posicao | Titulo | Texto | Botao]]   botao para a pagina de servico do post (+ WhatsApp)
  [[post slug | ancora]]                          link para outro post (vira texto puro ate o post ser publicado)
  [[pagina caminho | ancora]]                     link para uma pagina do site (ex.: agencia-de-seo)
"""
import html, json, re, shutil, subprocess, sys
from datetime import datetime, date
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_blog-src"
BASE = ""
SITE = "https://inovaseo.com.br"
TEL = "5545988195137"
PREVIEW = "--all" in sys.argv
OUT_NAME = "blog-preview" if PREVIEW else "blog"
OUT = ROOT / OUT_NAME
CAPAS = ROOT / "assets" / "blog"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
PILAR = "como-aparecer-no-google"
AUTOR_NOME = "Cezar Dias"
AUTOR = {"@type": "Person", "@id": SITE + "/#cezar-dias", "name": AUTOR_NOME,
         "jobTitle": "Especialista em SEO local", "worksFor": {"@id": SITE + "/#organization"}}
GRUPOS = {"c1": "Google e Maps", "c2": "SEO", "c3": "SEO para IA", "c4": "Sites", "c5": "Tráfego pago",
          "c6": "Marketing por segmento", "c7": "Contratar agência", "pilar": "Guia"}

# pagina de servico -> posts que ela deve linkar (bloco "Para entender antes de decidir")
REVERSO = {
    "index": [PILAR, "seo-local-o-que-e", "quanto-custa-um-site", "seo-vale-a-pena"],
    "seo": ["o-que-e-seo", "seo-vale-a-pena", "quanto-custa-seo", "como-escolher-agencia-de-seo"],
    "sites": ["quanto-custa-um-site", "criar-site-com-ia", "landing-page-o-que-e", "empresa-precisa-de-site"],
    "trafego": ["quanto-custa-google-ads", "quanto-cobra-agencia-de-trafego-pago", "trafego-pago-como-funciona", "seo-ou-google-ads"],
    "marketing": ["quanto-custa-agencia-de-marketing", "como-contratar-agencia-de-marketing", PILAR, "como-ganhar-clientes-pela-internet"],
    "consultoria": ["como-escolher-agencia-de-seo", "seo-vale-a-pena", "seo-ou-google-ads"],
    "pequenas": ["marketing-digital-vale-a-pena", "como-ganhar-clientes-pela-internet", "como-colocar-minha-empresa-no-google"],
    "seo-cidade": ["seo-local-o-que-e", "como-aparecer-no-google-maps", "como-conseguir-avaliacoes-no-google"],
    "sites-cidade": ["quanto-custa-um-site", "empresa-precisa-de-site", "site-lento-como-resolver"],
    "trafego-cidade": ["quanto-custa-google-ads", "seo-ou-google-ads", "trafego-pago-como-funciona"],
    "marketing-cidade": [PILAR, "como-colocar-minha-empresa-no-google", "como-ganhar-clientes-pela-internet"],
}


def tipo_pagina(pasta):
    """Tipo da pagina de servico pelo nome da pasta (ou 'index' para a home)."""
    fixos = {"": "index", "agencia-de-seo": "seo", "agencia-de-criacao-de-sites": "sites",
             "agencia-de-trafego-pago": "trafego", "agencia-de-marketing-digital": "marketing",
             "consultoria-de-marketing": "consultoria", "marketing-digital-para-pequenas-empresas": "pequenas"}
    if pasta in fixos:
        return fixos[pasta]
    for pref, t in (("agencia-de-seo-em-", "seo-cidade"), ("agencia-de-criacao-de-sites-em-", "sites-cidade"),
                    ("agencia-de-trafego-pago-em-", "trafego-cidade"), ("agencia-de-marketing-digital-em-", "marketing-cidade")):
        if pasta.startswith(pref):
            return t
    return None


def data_pt(d):
    return f"{d.day} de {MESES[d.month-1]} de {d.year}"


def utm(slug, content):
    return f"utm_source=blog&utm_medium=whatsapp&utm_campaign={slug}&utm_content={content}"


def wa_href(slug, content, titulo):
    texto = (f"Olá! Li o texto \"{titulo}\" no blog da InovaSEO e quero conversar sobre a minha empresa. "
             f"(Origem: {utm(slug, content)})")
    return f"https://wa.me/{TEL}?text={quote(texto, safe='')}"


def wa_btn(p, content, label, classe="btn-cta-primary"):
    return (f'<a class="{classe}" href="{wa_href(p["slug"], content, p["title"])}" target="_blank" rel="noopener noreferrer" '
            f'data-cta="whatsapp" data-pos="{content}" data-post="{p["slug"]}">{html.escape(label)}</a>')


def link_post(slug):
    return f"{BASE}/{OUT_NAME}/{slug}/"


def expandir(corpo, p, pub_slugs, por_slug):
    slug = p["slug"]

    def f_post(m):
        alvo, ancora = [x.strip() for x in m.group(1).split("|", 1)]
        if alvo not in por_slug:
            raise SystemExit(f"[[post]] para slug inexistente em {slug}: {alvo}")
        if alvo in pub_slugs and alvo != slug:
            return f'<a href="{link_post(alvo)}">{html.escape(ancora)}</a>'
        return html.escape(ancora)

    def f_pagina(m):
        alvo, ancora = [x.strip() for x in m.group(1).split("|", 1)]
        if alvo and not (ROOT / alvo / "index.html").exists():
            raise SystemExit(f"[[pagina]] inexistente em {slug}: {alvo}")
        return f'<a href="{BASE}/{alvo + "/" if alvo else ""}">{html.escape(ancora)}</a>'

    def f_cta_wa(m):
        pos, tit, txt, btn = [x.strip() for x in m.group(1).split("|", 3)]
        return (f'<aside class="post-cta"><p class="post-cta-tit">{html.escape(tit)}</p><p>{html.escape(txt)}</p>'
                f'{wa_btn(p, "cta-" + pos, btn)}</aside>')

    def f_cta_link(m):
        pos, tit, txt, btn = [x.strip() for x in m.group(1).split("|", 3)]
        pagina = p["page"]
        return (f'<aside class="post-cta post-cta-fim" id="cta"><p class="post-cta-tit">{html.escape(tit)}</p><p>{html.escape(txt)}</p>'
                f'<div class="post-cta-btns"><a class="btn-cta-primary" href="{BASE}/{pagina}/" data-cta="pagina" data-pos="cta-{pos}" data-post="{slug}">{html.escape(btn)}</a>'
                f'{wa_btn(p, "cta-" + pos + "-whatsapp", "Falar no WhatsApp", "btn-cta-secondary")}</div></aside>')

    corpo = re.sub(r"\[\[post ([^\]]+)\]\]", f_post, corpo)
    corpo = re.sub(r"\[\[pagina ([^\]]*)\]\]", f_pagina, corpo)
    corpo = re.sub(r"\[\[cta-wa ([^\]]+)\]\]", f_cta_wa, corpo)

    itens = []
    if slug != PILAR and PILAR in pub_slugs:
        itens.append(f'<li>Visão geral: <a href="{link_post(PILAR)}">{html.escape(por_slug[PILAR]["title"])}</a></li>')
    for alvo in p.get("to", []):
        if alvo not in por_slug:
            raise SystemExit(f"'to' com slug inexistente em {slug}: {alvo}")
        if alvo in pub_slugs and alvo != slug:
            itens.append(f'<li><a href="{link_post(alvo)}">{html.escape(por_slug[alvo]["title"])}</a></li>')
    continuar = ('<nav class="post-next" aria-label="Para continuar"><h2>Para continuar</h2><ul>' + "".join(itens) + '</ul></nav>') if itens else ""
    if "[[cta-link" not in corpo:
        raise SystemExit(f"post sem [[cta-link]]: {slug}")
    return re.sub(r"\[\[cta-link ([^\]]+)\]\]", lambda m: continuar + f_cta_link(m), corpo)


def capa(p):
    """Gera a capa do post (1200x630) com o titulo, em webp e jpg. So refaz se o titulo mudar."""
    CAPAS.mkdir(parents=True, exist_ok=True)
    webp, jpg, marca = CAPAS / f"{p['slug']}.webp", CAPAS / f"{p['slug']}.jpg", CAPAS / f"{p['slug']}.txt"
    titulo = p.get("cover", p["title"])
    if webp.exists() and jpg.exists() and marca.exists() and marca.read_text(encoding="utf-8") == titulo:
        return
    # capas sao geradas na maquina local (ImageMagick 7 + Arial Bold do macOS) e vao para o git;
    # o GitHub Actions so reaproveita as que ja existem
    fonte = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    grupo = GRUPOS.get(p.get("cluster", ""), "Blog").upper()
    base = ["magick", "-size", "1200x630", "gradient:#1e3a8a-#3b82f6", "-rotate", "0",
            "(", "-size", "1200x630", "xc:none", "-fill", "#ffffff14", "-draw", "circle 1080,90 1080,420", "-draw", "circle 120,640 120,860", ")",
            "-composite",
            "-font", str(fonte), "-fill", "#93c5fd", "-pointsize", "30", "-annotate", "+80+120", grupo,
            "(", "-size", "1040x330", "-background", "none", "-fill", "white", "-font", str(fonte), "-pointsize", "66",
            "-interline-spacing", "6", f"caption:{titulo}", ")", "-gravity", "northwest", "-geometry", "+80+160", "-composite",
            "-gravity", "southwest", "-fill", "white", "-pointsize", "38", "-annotate", "+80+60", "InovaSEO",
            "-fill", "#bfdbfe", "-pointsize", "26", "-gravity", "southeast", "-annotate", "+80+66", "Blog · SEO local e sites com IA"]
    subprocess.run(base + ["-quality", "82", str(jpg)], check=True)
    subprocess.run(["magick", str(jpg), "-quality", "80", str(webp)], check=True)
    marca.write_text(titulo, encoding="utf-8")


def ld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=2) + "\n</script>"


MODELO = (ROOT / "agencia-de-seo" / "index.html").read_text(encoding="utf-8")
HEADER = MODELO[MODELO.find("<header"):MODELO.find("</header>") + 9]
FOOTER = MODELO[MODELO.find("<footer"):MODELO.find("</footer>") + 9]
RASTREIO_HEAD = MODELO[MODELO.find("<!-- Rastreadores"):MODELO.find("</head>")].rstrip()
NOSCRIPT = re.search(r"<!-- Google Tag Manager \(noscript\) -->.*?</noscript>", MODELO, re.S)
NOSCRIPT = NOSCRIPT.group(0) if NOSCRIPT else ""
if "<header" not in HEADER or "<footer" not in FOOTER or "Rastreadores" not in RASTREIO_HEAD:
    raise SystemExit("nao achei header/footer/rastreio no modelo agencia-de-seo/index.html")

RASTREIO_CTA = """<script>
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[data-cta]');
  if (!a) return;
  var dados = { cta_tipo: a.dataset.cta, cta_posicao: a.dataset.pos || '', cta_texto: (a.textContent || '').trim().slice(0, 80),
                cta_destino: a.getAttribute('href').slice(0, 100), post: a.dataset.post || '', pagina: location.pathname };
  if (typeof window.gtag === 'function') window.gtag('event', 'cta_click', dados);
  if (a.dataset.cta === 'whatsapp' && typeof window.gtag === 'function')
    window.gtag('event', 'generate_lead', { lead_source: 'blog', botao: dados.cta_posicao, post: dados.post });
});
</script>"""


def menu_com_links(txt):
    """Garante os links Blog e Segmentos no menu (antes de Contato) e no rodape (depois de Consultoria/Inicio/Precos)."""
    for rot, alvo in (("Blog", f"{BASE}/blog/"), ("Segmentos", f"{BASE}/segmentos/")):
        i, j = txt.find("<header"), txt.find("</header>")
        if i >= 0 and j > i and f'href="{alvo}"' not in txt[i:j]:
            cab = re.sub(r'(\n[ \t]*)(<a href="[^"]*"( class="nav-item")?>Contato</a>)',
                         lambda m: f'{m.group(1)}<a href="{alvo}"{m.group(3) or ""}>{rot}</a>{m.group(1)}{m.group(2)}', txt[i:j], count=1)
            txt = txt[:i] + cab + txt[j:]
        i = txt.find("<footer")
        if i >= 0 and f'<li><a href="{alvo}">{rot}</a></li>' not in txt[i:]:
            ancora = (rf'<li><a href="{BASE}/blog/">Blog</a></li>' if rot == "Segmentos" else
                      rf'<li><a href="{BASE}/consultoria-de-marketing/">Consultoria</a></li>|<li><a href="{BASE}/">Início</a></li>|<li><a href="#planos">Preços</a></li>')
            rod = re.sub(rf'(\n[ \t]*)({ancora})', lambda m: f'{m.group(1)}{m.group(2)}{m.group(1)}<li><a href="{alvo}">{rot}</a></li>', txt[i:], count=1)
            txt = txt[:i] + rod
    return txt


def pagina(titulo, desc, canon, og_img, tipo_og, ld_blocos, miolo, preload="", atual="blog"):
    t, d = html.escape(titulo), html.escape(desc)
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t}</title>
    <meta name="description" content="{d}">
    <link rel="canonical" href="{canon}">
    <meta name="robots" content="index,follow,max-image-preview:large">
    <meta property="og:type" content="{tipo_og}">
    <meta property="og:title" content="{t}">
    <meta property="og:description" content="{d}">
    <meta property="og:url" content="{canon}">
    <meta property="og:image" content="{og_img}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:site_name" content="InovaSEO">
    <meta property="og:locale" content="pt_BR">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="icon" href="{BASE}/assets/favicon.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="{BASE}/assets/apple-touch-icon.png">
    <link rel="preload" href="{BASE}/assets/inter-latin.woff2" as="font" type="font/woff2" crossorigin>
    {preload}
    <style>@font-face{{font-family:"Inter";font-style:normal;font-weight:100 900;font-display:swap;src:url({BASE}/assets/inter-latin.woff2) format("woff2")}}</style>
    <link rel="stylesheet" href="{BASE}/style.css?v=2">
    <link rel="stylesheet" href="{BASE}/{OUT_NAME}/blog.css?v=1">
{chr(10).join(ld_blocos)}
    {RASTREIO_HEAD}
</head>
<body id="top">
    {NOSCRIPT}
    {menu_com_links(HEADER).replace(f'href="{BASE}/{atual}/" class="nav-item">', f'href="{BASE}/{atual}/" class="nav-item" aria-current="page">')}
<main>
{miolo}
</main>
    {menu_com_links(FOOTER)}
    <script src="{BASE}/script.js?v=2"></script>
{RASTREIO_CTA}
</body>
</html>
'''


def card(o, com_desc=False):
    desc = f'<p>{html.escape(o["desc"])}</p>' if com_desc else ""
    return (f'<a class="blog-card" href="{link_post(o["slug"])}"><img src="{BASE}/assets/blog/{o["slug"]}.webp" width="1200" height="630" '
            f'alt="" loading="lazy" decoding="async"><div class="blog-card-body"><time datetime="{o["date"]}">{data_pt(date.fromisoformat(o["date"]))}</time>'
            f'<h3>{html.escape(o["title"])}</h3>{desc}</div></a>')


def leia_tambem(p, pub):
    outros = [o for o in pub if o["slug"] != p["slug"]]
    mesmo = sorted([o for o in outros if o.get("cluster") == p.get("cluster")], key=lambda o: o["date"], reverse=True)
    escolha = mesmo[:3]
    for o in [x for x in outros if x["slug"] == PILAR] + outros:
        if len(escolha) >= 3:
            break
        if o not in escolha:
            escolha.append(o)
    return escolha


def atualizar_paginas_do_site(pub, por_slug):
    """Bloco com links para posts publicados nas paginas de servico + link Blog no menu e no rodape."""
    pub_slugs = {o["slug"] for o in pub}
    alteradas = 0
    arquivos = [ROOT / "index.html"] + sorted(ROOT.glob("*/index.html"))
    for f in arquivos:
        pasta = "" if f.parent == ROOT else f.parent.name
        if pasta in ("blog", "blog-preview", "auditorias", "segmentos") or pasta.startswith("_") or pasta in NICHO_SLUGS:
            continue
        txt = f.read_text(encoding="utf-8")
        novo = txt
        if pub:
            novo = menu_com_links(novo)
        tipo = tipo_pagina(pasta)
        novo = re.sub(r"\n?<!-- blog-links:start -->.*?<!-- blog-links:end -->\n?", "\n", novo, flags=re.S)
        lista = [s for s in REVERSO.get(tipo, []) if s in pub_slugs][:3] if tipo else []
        if lista and "<footer" in novo:
            li = "".join(f'<li><a href="{link_post(s)}">{html.escape(por_slug[s]["title"])}</a></li>' for s in lista)
            bloco = ('<!-- blog-links:start -->\n<section class="blog-links" style="padding:2.5rem 0;background:var(--muted)"><div class="container">'
                     '<p style="font-size:.8rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--primary);margin-bottom:.8rem">Para entender antes de decidir</p>'
                     f'<ul style="list-style:none;display:grid;gap:.6rem;margin-bottom:1rem">{li}</ul>'
                     f'<a href="{BASE}/blog/" style="color:var(--primary);font-weight:600">Ver todos os textos do blog →</a></div></section>\n'
                     '<!-- blog-links:end -->\n')
            i = novo.find("<footer")
            linha = novo.rfind("\n", 0, i) + 1
            novo = novo[:linha] + bloco + novo[linha:]
        if novo != txt:
            f.write_text(novo, encoding="utf-8")
            alteradas += 1
    return alteradas


# ---------------------------------------------------------------- paginas por segmento (nichos)
NICHOS = json.loads((SRC / "nichos.json").read_text(encoding="utf-8")) if (SRC / "nichos.json").exists() else []
NICHO_SLUGS = {n["slug"] for n in NICHOS}


def wa_nicho(n, pos, label, classe="btn-cta-primary"):
    texto = (f"Olá! Vi a página de marketing para {n['nome']} da InovaSEO e quero conversar sobre o meu negócio. "
             f"(Origem: utm_source=site&utm_medium=whatsapp&utm_campaign=nicho-{n['slug']}&utm_content={pos})")
    return (f'<a class="{classe}" href="https://wa.me/{TEL}?text={quote(texto, safe="")}" target="_blank" rel="noopener noreferrer" '
            f'data-cta="whatsapp" data-pos="{pos}" data-post="{n["slug"]}">{html.escape(label)}</a>')


def gerar_nichos(pub_slugs, por_slug):
    if not NICHOS:
        return 0
    for n in NICHOS:
        capa({"slug": n["slug"], "title": n["h1"], "cover": n["h1"], "cluster": "c6"})
        corpo = (SRC / "nichos" / f"{n['slug']}.html").read_text(encoding="utf-8")
        if "\u2014" in corpo or "\u2013" in corpo:
            raise SystemExit(f"travessao no nicho {n['slug']}")

        def f_post(m):
            alvo, ancora = [x.strip() for x in m.group(1).split("|", 1)]
            if alvo not in por_slug:
                raise SystemExit(f"[[post]] inexistente no nicho {n['slug']}: {alvo}")
            return f'<a href="{link_post(alvo)}">{html.escape(ancora)}</a>' if alvo in pub_slugs else html.escape(ancora)

        def f_wa(m):
            pos, tit, txt, btn = [x.strip() for x in m.group(1).split("|", 3)]
            return (f'<aside class="post-cta"><p class="post-cta-tit">{html.escape(tit)}</p><p>{html.escape(txt)}</p>'
                    f'{wa_nicho(n, "cta-" + pos, btn)}</aside>')
        corpo = re.sub(r"\[\[post ([^\]]+)\]\]", f_post, corpo)
        corpo = re.sub(r"\[\[cta-wa ([^\]]+)\]\]", f_wa, corpo)
        lidos = [s for s in n.get("posts", []) if s in pub_slugs][:4]
        ler = ""
        if lidos:
            ler = ('<nav class="post-next" aria-label="Para entender antes de decidir"><h2>Para entender antes de decidir</h2><ul>'
                   + "".join(f'<li><a href="{link_post(s)}">{html.escape(por_slug[s]["title"])}</a></li>' for s in lidos) + "</ul></nav>")
        outros = [o for o in NICHOS if o["slug"] != n["slug"]]
        irmaos = ('<nav class="post-next" aria-label="Outros segmentos"><h2>Outros segmentos que atendemos</h2><ul>'
                  + "".join(f'<li><a href="{BASE}/{o["slug"]}/">{html.escape(o["h1"])}</a></li>' for o in outros[:6])
                  + f'<li><a href="{BASE}/segmentos/">Ver todos os segmentos</a></li></ul></nav>')
        canon = f"{SITE}/{n['slug']}/"
        miolo = f'''<section class="page-hero">
    <div class="container post-narrow">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{BASE}/">Início</a><span aria-hidden="true">›</span><a href="{BASE}/segmentos/">Segmentos</a><span aria-hidden="true">›</span><span>{html.escape(n["nome"].capitalize())}</span></nav>
        <h1>{html.escape(n["h1"])}</h1>
        <p>{html.escape(n["sub"])}</p>
        <div class="post-cta-btns" style="margin-top:1.4rem">{wa_nicho(n, "hero", "Falar com especialista")}<a class="btn-cta-secondary" href="{BASE}/#planos" data-cta="pagina" data-pos="hero-planos" data-post="{n["slug"]}">Ver planos</a></div>
    </div>
</section>
<article class="post"><div class="container post-narrow content-text">
{corpo}
<aside class="post-cta post-cta-fim" id="cta"><p class="post-cta-tit">{html.escape(n["cta"])}</p><p>Atendemos {html.escape(n["nome"])} de todo o Brasil, com reuniões on-line e relatórios mensais de cliques, ligações e contatos.</p>
<div class="post-cta-btns">{wa_nicho(n, "cta-fim", "Falar no WhatsApp")}<a class="btn-cta-secondary" href="{BASE}/agencia-de-marketing-digital/" data-cta="pagina" data-pos="cta-fim-servico" data-post="{n["slug"]}">Conhecer a agência</a></div></aside>
{ler}
{irmaos}
</div></article>'''
        servico = {"@context": "https://schema.org", "@type": "Service", "name": n["h1"], "serviceType": "Marketing digital",
                   "description": n["desc"], "provider": {"@id": SITE + "/#organization"}, "areaServed": {"@type": "Country", "name": "Brasil"},
                   "audience": {"@type": "BusinessAudience", "name": n["nome"].capitalize()}, "url": canon}
        trilha = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Segmentos", "item": SITE + "/segmentos/"},
            {"@type": "ListItem", "position": 3, "name": n["h1"], "item": canon}]}
        (ROOT / n["slug"]).mkdir(exist_ok=True)
        (ROOT / n["slug"] / "index.html").write_text(
            pagina(n["title"], n["desc"], canon, f"{SITE}/assets/blog/{n['slug']}.jpg", "website", [ld(servico), ld(trilha)], miolo, "", "segmentos"),
            encoding="utf-8")
    cards = "".join(f'<a class="blog-card" href="{BASE}/{n["slug"]}/"><img src="{BASE}/assets/blog/{n["slug"]}.webp" width="1200" height="630" alt="" loading="lazy" decoding="async">'
                    f'<div class="blog-card-body"><h3>{html.escape(n["h1"])}</h3><p>{html.escape(n["sub"])}</p></div></a>' for n in NICHOS)
    miolo = f'''<section class="page-hero"><div class="container">
    <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{BASE}/">Início</a><span aria-hidden="true">›</span><span>Segmentos</span></nav>
    <h1>Marketing digital por segmento</h1>
    <p>Cada tipo de negócio é encontrado de um jeito no Google. Escolha o seu e veja como trabalhamos SEO, Google Maps, site e anúncios para ele, em qualquer cidade do Brasil.</p>
</div></section>
<section class="page-section"><div class="container"><div class="blog-grid">{cards}</div></div></section>'''
    (ROOT / "segmentos").mkdir(exist_ok=True)
    (ROOT / "segmentos" / "index.html").write_text(
        pagina("Marketing digital por segmento | InovaSEO", "Agência de marketing para dentistas, advogados, imobiliárias, restaurantes, academias e outros segmentos, em todo o Brasil.",
               SITE + "/segmentos/", SITE + "/assets/og-inovaseo.jpg", "website",
               [ld({"@context": "https://schema.org", "@type": "CollectionPage", "name": "Marketing digital por segmento", "url": SITE + "/segmentos/"})], miolo, "", "segmentos"),
        encoding="utf-8")
    return len(NICHOS)


def main():
    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    posts = json.loads((SRC / "posts.json").read_text(encoding="utf-8"))
    por_slug = {p["slug"]: p for p in posts}
    pub = [p for p in posts if PREVIEW or date.fromisoformat(p["date"]) <= hoje]
    pub.sort(key=lambda p: p["date"], reverse=True)
    pub_slugs = {p["slug"] for p in pub}

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(SRC / "blog.css", OUT / "blog.css")

    for p in pub:
        slug = p["slug"]
        capa(p)
        d = date.fromisoformat(p["date"])
        corpo = expandir((SRC / "posts" / f"{slug}.html").read_text(encoding="utf-8"), p, pub_slugs, por_slug)
        if "—" in corpo or "–" in corpo:
            raise SystemExit(f"travessao no post {slug}")
        palavras = len(re.sub(r"<[^>]+>", " ", corpo).split())
        minutos = max(3, round(palavras / 200))
        canon = f"{SITE}/blog/{slug}/"
        og = f"{SITE}/assets/blog/{slug}.jpg"
        outros = leia_tambem(p, pub)
        mais = ""
        if outros:
            mais = ('<section class="page-section page-section--alt"><div class="container"><h2 class="section-title">Leia também</h2>'
                    '<div class="blog-grid">' + "".join(card(o) for o in outros) + '</div></div></section>')
        miolo = f'''<section class="page-hero post-hero">
    <div class="container post-narrow">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{BASE}/">Início</a><span aria-hidden="true">›</span><a href="{BASE}/blog/">Blog</a><span aria-hidden="true">›</span><span>{html.escape(GRUPOS.get(p.get("cluster",""), "Blog"))}</span></nav>
        <h1>{html.escape(p["title"])}</h1>
        <p class="post-meta">Por {AUTOR_NOME}, InovaSEO · <time datetime="{p["date"]}">{data_pt(d)}</time> · {minutos} min de leitura</p>
    </div>
</section>
<div class="post-capa"><img src="{BASE}/assets/blog/{slug}.webp" width="1200" height="630" alt="{html.escape(p["title"])}" fetchpriority="high" decoding="async"></div>
<article class="post"><div class="container post-narrow content-text">
{corpo}
</div></article>
{mais}'''
        artigo = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": p["desc"],
                  "image": og, "datePublished": p["date"], "dateModified": p.get("updated", p["date"]), "inLanguage": "pt-BR",
                  "keywords": p.get("kw", ""), "author": AUTOR, "publisher": {"@id": SITE + "/#organization"},
                  "mainEntityOfPage": canon}
        if slug != PILAR and PILAR in pub_slugs:
            artigo["isPartOf"] = {"@type": "CreativeWork", "@id": f"{SITE}/blog/{PILAR}/", "name": por_slug[PILAR]["title"]}
        trilha = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": canon}]}
        preload = f'<link rel="preload" as="image" href="{BASE}/assets/blog/{slug}.webp" type="image/webp" fetchpriority="high">'
        (OUT / slug).mkdir()
        (OUT / slug / "index.html").write_text(
            pagina(p.get("seo_title", p["title"] + " | InovaSEO"), p["desc"], canon, og, "article", [ld(artigo), ld(trilha)], miolo, preload),
            encoding="utf-8")

    if pub:
        cards = "".join(card(o, True) for o in pub)
        miolo = f'''<section class="page-hero">
    <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{BASE}/">Início</a><span aria-hidden="true">›</span><span>Blog</span></nav>
        <h1>Blog da InovaSEO</h1>
        <p>O que eu explico todo dia para donos de negócio sobre Google, Maps, sites e IA, escrito para quem tem empresa em Foz do Iguaçu e no Oeste do Paraná. Dois textos novos por semana.</p>
    </div>
</section>
<section class="page-section"><div class="container"><div class="blog-grid">{cards}</div></div></section>'''
        (OUT / "index.html").write_text(
            pagina("Blog de SEO local, Google Maps e sites com IA | InovaSEO",
                   "Guias práticos sobre SEO local, perfil da empresa no Google, sites, Google Ads e IA para empresas do Oeste do Paraná.",
                   SITE + "/blog/", SITE + "/assets/og-inovaseo.jpg", "website",
                   [ld({"@context": "https://schema.org", "@type": "Blog", "name": "Blog da InovaSEO", "url": SITE + "/blog/",
                        "inLanguage": "pt-BR", "publisher": {"@id": SITE + "/#organization"}})], miolo),
            encoding="utf-8")

    if not PREVIEW:
        print(f"paginas de segmento: {gerar_nichos(pub_slugs, por_slug)}")
        sm = ROOT / "sitemap.xml"
        txt = sm.read_text(encoding="utf-8")
        txt = re.sub(r"\s*<!-- blog:start -->.*?<!-- blog:end -->", "", txt, flags=re.S)
        if pub:
            urls = [f"  <url>\n    <loc>{SITE}/blog/</loc>\n    <lastmod>{pub[0]['date']}</lastmod>\n  </url>"]
            urls += [f"  <url>\n    <loc>{SITE}/blog/{o['slug']}/</loc>\n    <lastmod>{o.get('updated', o['date'])}</lastmod>\n  </url>" for o in pub]
            txt = txt.replace("</urlset>", "  <!-- blog:start -->\n" + "\n".join(urls) + "\n  <!-- blog:end -->\n</urlset>")
        txt = re.sub(r"\s*<!-- nichos:start -->.*?<!-- nichos:end -->", "", txt, flags=re.S)
        if NICHOS:
            urls = [f"  <url>\n    <loc>{SITE}/segmentos/</loc>\n  </url>"] + [f"  <url>\n    <loc>{SITE}/{n['slug']}/</loc>\n  </url>" for n in NICHOS]
            txt = txt.replace("</urlset>", "  <!-- nichos:start -->\n" + "\n".join(urls) + "\n  <!-- nichos:end -->\n</urlset>")
        sm.write_text(txt, encoding="utf-8")
        n = atualizar_paginas_do_site(pub, por_slug)
        print(f"paginas do site atualizadas: {n}")
    print(f"{OUT_NAME}: {len(pub)} post(s) | hoje (Brasilia): {hoje}")
    for o in pub:
        print(" ", o["date"], o["slug"])


if __name__ == "__main__":
    main()
