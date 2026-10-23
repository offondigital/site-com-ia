#!/usr/bin/env python3
"""Avisa Bing, Yahoo, DuckDuckGo e Yandex (IndexNow) sobre posts novos do blog.

Roda depois do build.py. Guarda em _blog-src/indexnow-enviados.json o que ja foi avisado,
entao cada endereco e enviado uma vez so. Falha de rede nao derruba a rotina do blog.
O Google nao usa IndexNow: ele le o sitemap.xml.
"""
import json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "offondigital.github.io"
SITE = f"https://{HOST}/site-com-ia"
ESTADO = ROOT / "_blog-src" / "indexnow-enviados.json"


def main():
    chaves = [p.stem for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem) and p.read_text().strip() == p.stem]
    if not chaves:
        print("indexnow: arquivo de chave nao encontrado, nada enviado")
        return 0
    chave = chaves[0]
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>(%s/blog/[^<]*)</loc>" % re.escape(SITE), sitemap)
    enviados = set(json.loads(ESTADO.read_text())) if ESTADO.exists() else set()
    novas = [u for u in urls if u not in enviados]
    if not novas:
        print("indexnow: nenhum endereco novo")
        return 0
    corpo = json.dumps({"host": HOST, "key": chave, "keyLocation": f"{SITE}/{chave}.txt", "urlList": novas}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=corpo, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            codigo = r.status
    except urllib.error.HTTPError as e:
        codigo = e.code
    except Exception as e:
        print(f"indexnow: falhou ({e}); tentara de novo na proxima execucao")
        return 0
    print(f"indexnow: HTTP {codigo} para {len(novas)} endereco(s)")
    if codigo in (200, 202):
        ESTADO.write_text(json.dumps(sorted(enviados | set(novas)), indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
