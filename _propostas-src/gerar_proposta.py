#!/usr/bin/env python3
"""Gera uma proposta protegida por senha em /propostas/.

O conteúdo da proposta é criptografado (AES-256-GCM, chave derivada da senha
com PBKDF2-SHA256, 600.000 iterações). O HTML publicado não contém o texto da
proposta em claro: sem a senha, nem o código-fonte da página revela nada.

Regra da senha (nesta ordem):
  1. o número do botão flutuante de WhatsApp do site do prospecto;
  2. se o site não tiver WhatsApp, o e-mail do site;
  3. se não tiver e-mail, o telefone do site.
  Opcional: --senha auto gera uma senha aleatória de 12 caracteres (mais segura,
  para propostas com preço ou dados sensíveis; o prospecto não a "descobre" sozinho,
  então envie a senha a ele por WhatsApp).
Telefone: a página aceita com ou sem parênteses, espaços, traço ou +55.
E-mail: a página ignora maiúsculas/minúsculas e espaços nas pontas.

IMPORTANTE: este repositório é público. Nunca faça commit do arquivo de
conteúdo em claro; mantenha-o fora do repositório.

Uso:
  python3 _propostas-src/gerar_proposta.py \
      --cliente "Jet Point" --slug jet-point --data 29/10/2026 \
      --senha "(81) 9 9795-0880"   (ou --senha contato@empresa.com.br) --conteudo /caminho/fora/do/repo/conteudo.html

Saída: propostas/<slug>-<dd-mm-aaaa>-<código aleatório>.html
(preencha a coluna Q do CRM com o nome impresso, sem .html, para a tag "Proposta aberta")
"""
import argparse
import secrets
import base64
import html
import os
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERACOES = 600_000
GA4_ID = "G-CDGVGTPP75"          # ID de medição (fluxo da web) do GA4
PIXEL_ID = "1098807029734790"    # Pixel do Facebook/Meta
WHATSAPP = "5545988195137"
# Apps Script que avisa no Telegram (o mesmo das auditorias parciais). Vazio = sem aviso.
AVISO_URL = os.environ.get("AVISO_URL", "https://script.google.com/macros/s/AKfycbxcoFgihWxI51tOExb75D3I3rE8UBhin-Z_xa5PfwPd4Elz5tx2bXYJy83WP3UrG5G1/exec")
RAIZ = Path(__file__).resolve().parent.parent
MODELO = Path(__file__).resolve().parent / "modelo.html"


def senha_aleatoria() -> str:
    alfabeto = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O/1/l/I
    return "".join(secrets.choice(alfabeto) for _ in range(12))


def normalizar_senha(t: str) -> str:
    t = t.strip()
    if t == "auto":
        return senha_aleatoria()
    if "@" in t:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", t):
            sys.exit(f"E-mail inválido: '{t}'")
        return t.lower()
    d = re.sub(r"\D", "", t)
    if len(d) in (12, 13) and d.startswith("55"):
        d = d[2:]
    if len(d) not in (10, 11):
        sys.exit(f"Telefone inválido: '{t}' (esperado DDD + número)")
    return d


def criptografar(texto: str, senha: str) -> dict:
    sal = os.urandom(16)
    iv = os.urandom(12)
    chave = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sal,
                       iterations=ITERACOES).derive(senha.encode())
    cifra = AESGCM(chave).encrypt(iv, texto.encode("utf-8"), None)
    b64 = lambda b: base64.b64encode(b).decode()
    return {"sal": b64(sal), "iv": b64(iv), "dados": b64(cifra)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cliente", required=True)
    p.add_argument("--slug", required=True)
    p.add_argument("--data", required=True, help="dd/mm/aaaa (data de envio)")
    p.add_argument("--senha", "--telefone", dest="senha", required=True,
                   help="WhatsApp do botão flutuante; sem WhatsApp, e-mail; sem e-mail, telefone")
    p.add_argument("--conteudo", required=True)
    a = p.parse_args()

    if not re.fullmatch(r"[a-z0-9-]+", a.slug):
        sys.exit("slug deve ter só letras minúsculas, números e hífen")
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", a.data):
        sys.exit("data deve estar em dd/mm/aaaa")
    conteudo = Path(a.conteudo).resolve()
    if RAIZ in conteudo.parents:
        sys.exit("O conteúdo em claro não pode ficar dentro do repositório (ele é público).")

    livre = a.senha.strip() == "auto"
    senha = normalizar_senha(a.senha)
    c = criptografar(conteudo.read_text(encoding="utf-8"), senha)
    codigo = secrets.token_hex(3)  # 6 caracteres aleatórios: o endereço deixa de ser adivinhável
    nome = f"{a.slug}-{a.data.replace('/', '-')}-{codigo}"

    pagina = MODELO.read_text(encoding="utf-8")
    trocas = {
        "{{CLIENTE}}": html.escape(a.cliente),
        "{{SLUG}}": nome,
        "{{DATA}}": a.data,
        "{{GA4_ID}}": GA4_ID,
        "{{PIXEL_ID}}": PIXEL_ID,
        "{{WHATSAPP}}": WHATSAPP,
        "{{AVISO_URL}}": AVISO_URL,
        "{{ITERACOES}}": str(ITERACOES),
        "{{INPUTMODE}}": "text" if livre else ("email" if "@" in senha else "numeric"),
        "{{SENHA_LIVRE}}": "true" if livre else "false",
        "{{SAL}}": c["sal"],
        "{{IV}}": c["iv"],
        "{{DADOS}}": c["dados"],
    }
    for k, v in trocas.items():
        pagina = pagina.replace(k, v)

    destino = RAIZ / "propostas" / f"{nome}.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(pagina, encoding="utf-8")
    print(f"OK: {destino.relative_to(RAIZ)}")
    print(f"Link: https://inovaseo.com.br/propostas/{nome}.html")
    print(f"Senha: {senha}")


if __name__ == "__main__":
    main()
