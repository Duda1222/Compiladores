# -*- coding: utf-8 -*-
"""Gera docs/img/fluxo-sistema.png (fluxograma do sistema) a partir de um SVG."""
import cairosvg

W, H = 1120, 1062
XL, XM, XR = 215, 560, 905
VERDE_F, VERDE_B = "#d9f2e0", "#2e7d32"
CINZA_F, CINZA_B = "#efefef", "#8a8a8a"
TXT = "#111111"
partes = []

def caixa(cx, cy, w, h, linhas, tipo="proc", pend=False, fs=15):
    f, b = (CINZA_F, CINZA_B) if pend else (VERDE_F, VERDE_B)
    tracejado = ' stroke-dasharray="7 5"' if pend else ''
    x, y = cx - w / 2, cy - h / 2
    if tipo == "term":
        partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{f}" stroke="{b}" stroke-width="2"{tracejado}/>')
    elif tipo == "dec":
        partes.append(f'<polygon points="{cx},{y} {cx+w/2},{cy} {cx},{y+h} {cx-w/2},{cy}" fill="{f}" stroke="{b}" stroke-width="2"/>')
    else:
        partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{f}" stroke="{b}" stroke-width="2"{tracejado}/>')
    n = len(linhas)
    y0 = cy - (n - 1) * (fs + 5) / 2 + fs / 3
    for i, t in enumerate(linhas):
        partes.append(f'<text x="{cx}" y="{y0 + i*(fs+5):.0f}" font-size="{fs}" text-anchor="middle" fill="{TXT}" font-family="Helvetica, Arial, sans-serif">{t}</text>')

def seta(pontos, rotulo=None, rx=0, ry=0, tracejada=False):
    d = "M " + " L ".join(f"{x} {y}" for x, y in pontos)
    tr = ' stroke-dasharray="6 5"' if tracejada else ''
    partes.append(f'<path d="{d}" fill="none" stroke="#555" stroke-width="1.8" marker-end="url(#sa)"{tr}/>')
    if rotulo:
        partes.append(f'<text x="{rx}" y="{ry}" font-size="14" fill="#333" font-family="Helvetica, Arial, sans-serif">{rotulo}</text>')

# ---- nós (cy, altura) ----
caixa(XM,  42, 250, 46, ["Código Python"], "term")
caixa(XM, 140, 520, 56, ["Validação da entrada no frontend e no backend:", "campo vazio, limite de 100.000 caracteres, JSON"])
caixa(XM, 243, 440, 56, ["Análise léxica (scanner): tokens,", "INDENT e DEDENT"])
caixa(XM, 360, 330, 86, ["Há erros léxicos?"], "dec")
caixa(XL, 487, 350, 64, ["Parser NÃO é executado:", "sintatico.executado = false"])
caixa(XR, 487, 350, 64, ["Análise sintática: parser", "descendente recursivo"])
caixa(XR, 600, 300, 80, ["Há erros sintáticos?"], "dec")
caixa(XM, 718, 330, 80, ["Erros com encontrado,", "esperado, regra e dica;", "recuperação em modo pânico"])
caixa(XR, 718, 300, 80, ["AST e árvore de", "derivação completas"])
caixa(XM, 838, 700, 56, ["Resposta JSON: campos planos da Etapa 3 +", "bloco lexico + bloco sintatico"])
caixa(XM, 930, 700, 56, ["Interface: tokens passo a passo, erros léxicos e sintáticos", "separados, AST e árvore de derivação"])
caixa(XM, 1000, 420, 34, ["Análise semântica — Etapa 5: não implementada"], pend=True, fs=14)

# ---- setas ----
seta([(XM, 65), (XM, 112)])
seta([(XM, 168), (XM, 215)])
seta([(XM, 271), (XM, 317)])
seta([(XM - 165, 360), (XL, 360), (XL, 455)], "sim", XL + 8, 420)
seta([(XM + 165, 360), (XR, 360), (XR, 455)], "não", XR + 8, 420)
seta([(XR, 519), (XR, 560)])
seta([(XR - 150, 600), (XM, 600), (XM, 678)], "sim", XM + 8, 650)
seta([(XR, 640), (XR, 678)], "não", XR + 10, 663)
seta([(XL, 519), (XL, 838 - 28)])
seta([(XM, 758), (XM, 810)])
seta([(XR, 758), (XR, 838 - 28)])
seta([(XM, 866), (XM, 902)])
seta([(XM, 958), (XM, 983)], tracejada=True)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M0 0L10 5L0 10z" fill="#555"/></marker></defs>
<rect width="{W}" height="{H}" fill="white"/>
{''.join(partes)}
<text x="18" y="{H-14}" font-size="13" fill="#555" font-family="Helvetica, Arial, sans-serif">Verde: implementado nas Etapas 3 e 4.  Cinza tracejado: pendente (Etapa 5).</text>
</svg>'''
open("/tmp/fluxo.svg", "w", encoding="utf-8").write(svg)
cairosvg.svg2png(url="/tmp/fluxo.svg", write_to="/tmp/fluxo.png", scale=2)
print("ok")
