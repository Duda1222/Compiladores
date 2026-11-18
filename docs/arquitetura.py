# -*- coding: utf-8 -*-
"""Gera docs/img/arquitetura.png (arquitetura do sistema) a partir de um SVG."""
import cairosvg

W, H = 1120, 700
AZUL_F, AZUL_B = "#e7f1fb", "#2f6fae"
VERDE_F, VERDE_B = "#d9f2e0", "#2e7d32"
CINZA_B = "#8a8a8a"
TXT = "#111111"
p = []
FONT = "Helvetica, Arial, sans-serif"


def texto(x, y, t, fs=15, anc="middle", cor=TXT, peso="normal"):
    p.append(f'<text x="{x}" y="{y}" font-size="{fs}" text-anchor="{anc}" fill="{cor}" '
             f'font-family="{FONT}" font-weight="{peso}">{t}</text>')


def caixa(cx, cy, w, h, linhas, f=AZUL_F, b=AZUL_B, fs=15, rx=9):
    p.append(f'<rect x="{cx-w/2}" y="{cy-h/2}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{b}" stroke-width="2"/>')
    y0 = cy - (len(linhas) - 1) * (fs + 5) / 2 + fs / 3
    for i, t in enumerate(linhas):
        texto(cx, y0 + i * (fs + 5), t, fs)


def seta(pontos, rotulo=None, rx=0, ry=0, anc="middle"):
    d = "M " + " L ".join(f"{x} {y}" for x, y in pontos)
    p.append(f'<path d="{d}" fill="none" stroke="#555" stroke-width="1.8" marker-end="url(#sa)"/>')
    if rotulo:
        texto(rx, ry, rotulo, 13, anc, "#333")


# contêiner do Docker Compose
p.append(f'<rect x="60" y="150" width="1000" height="520" rx="14" fill="none" stroke="{CINZA_B}" '
         f'stroke-width="2" stroke-dasharray="8 6"/>')
texto(80, 176, "Docker Compose", 14, "start", "#555", "bold")

caixa(560, 55, 300, 54, ["Navegador do usuário"], "#ffffff", "#444", rx=27)

# serviço frontend
p.append('<rect x="100" y="200" width="420" height="150" rx="12" fill="none" stroke="#2f6fae" stroke-width="1.5"/>')
texto(120, 224, "serviço frontend — porta 8080", 13, "start", "#2f6fae", "bold")
caixa(310, 290, 360, 90, ["Nginx: serve index.html, css/ e js/", "e encaminha /api/ para o backend", "(frontend/nginx.conf)"], fs=14)

# serviço backend
p.append('<rect x="580" y="200" width="440" height="430" rx="12" fill="none" stroke="#2e7d32" stroke-width="1.5"/>')
texto(600, 224, "serviço backend — porta 5000", 13, "start", "#2e7d32", "bold")
caixa(800, 275, 380, 60, ["Gunicorn + Flask (app.py):", "rota POST /api/analisar"], VERDE_F, VERDE_B, fs=14)
caixa(800, 375, 330, 48, ["validacao.py: valida a entrada"], VERDE_F, VERDE_B, fs=14)
caixa(800, 455, 330, 48, ["scanner.py: análise léxica"], VERDE_F, VERDE_B, fs=14)
caixa(800, 535, 330, 48, ["sintatico.py: análise sintática"], VERDE_F, VERDE_B, fs=14)
caixa(800, 600, 330, 40, ["arvore.py: nós da AST"], VERDE_F, VERDE_B, fs=14)

seta([(408, 70), (250, 70), (250, 245)], "requisições HTTP (porta 8080)", 400, 56, "end")
seta([(370, 245), (370, 110), (650, 110)], "páginas, arquivos estáticos e respostas JSON", 660, 114, "start")
seta([(490, 272), (610, 272)], "proxy /api/", 532, 258)
seta([(610, 312), (490, 312)], "JSON: lexico + sintatico", 500, 336, "start")
seta([(800, 305), (800, 351)])
seta([(800, 399), (800, 431)])
seta([(800, 479), (800, 511)])
seta([(800, 559), (800, 580)])
texto(310, 420, "O navegador nunca fala direto com a porta 5000:", 13, "middle", "#555")
texto(310, 440, "ela só existe dentro da rede do Docker Compose.", 13, "middle", "#555")

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M0 0L10 5L0 10z" fill="#555"/></marker></defs>
<rect width="{W}" height="{H}" fill="white"/>
{''.join(p)}
</svg>'''
open("/tmp/arq.svg", "w", encoding="utf-8").write(svg)
cairosvg.svg2png(url="/tmp/arq.svg", write_to="img/arquitetura.png", scale=2)
print("ok")
