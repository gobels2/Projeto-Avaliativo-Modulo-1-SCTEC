"""
analise.py - Analise Exploratoria de Dados (AED/EDA) do esquema HR

Projeto: Analise Exploratoria da Estrutura Salarial e Distribuicao
         Geografica - Esquema HR
Aluno:   Leo Gobel
Turma:   Visualizacao de Dados e Business Intelligence - T2

ENTRADA : data/query_01.csv e data/query_02.csv
          (exportados do SQL Worksheet do FreeSQL via Download > CSV)
SAIDA   : 5 graficos em img/ e um resumo em data/resultados.txt

ESTRUTURA DA ANALISE (8 blocos)
  BLOCO 1 - Carga e verificacao de integridade
  BLOCO 2 - Estatistica descritiva
  BLOCO 3 - Distribuicao e assimetria      -> img/hist_salarios.png
  BLOCO 4 - Comparacao por departamento    -> img/boxplot_departamento.png
  BLOCO 5 - Comparacao por regiao          -> img/boxplot_regiao.png
  BLOCO 6 - Outliers e o efeito do filtro  -> img/outliers_efeito_filtro.png
  BLOCO 7 - Conformidade de banda salarial -> img/bandas_salariais.png
  BLOCO 8 - Remuneracao total com comissao

COMO EXECUTAR
    python src/analise.py
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # backend sem janela: so grava arquivos
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# O parametro vert= do boxplot foi depreciado no matplotlib 3.11, mas o
# substituto (orientation=) nao existe nas versoes anteriores. Mantemos
# vert= para compatibilidade e silenciamos o aviso, que nao afeta a saida.
warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
IMG = RAIZ / "img"

# ---------------------------------------------------------------------
# Paleta e estilo visual
# Uma unica matiz (azul) para comparacoes entre categorias: departamentos
# e regioes nao sao 12 "series" diferentes, sao a MESMA metrica medida em
# grupos distintos. Cores diferentes por categoria sugeririam identidades
# independentes e adicionariam ruido sem informacao.
# O vermelho fica reservado para sinalizar outliers e limites.
# ---------------------------------------------------------------------
AZUL = "#2a78d6"
AZUL_CLARO = "#9ec5f4"
AZUL_ESCURO = "#184f95"
VERMELHO = "#d03b3b"
LARANJA = "#eb6834"
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
MUDO = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
    "axes.edgecolor": EIXO,
    "axes.labelcolor": TINTA_2,
    "axes.titlecolor": TINTA,
    "text.color": TINTA,
    "xtick.color": MUDO,
    "ytick.color": MUDO,
    "xtick.labelcolor": TINTA_2,
    "ytick.labelcolor": TINTA_2,
    "grid.color": GRADE,
    "grid.linewidth": 0.8,
    "axes.grid": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
})

linhas_resumo: list[str] = []


def titulo(texto: str) -> None:
    """Imprime um cabecalho de bloco no terminal e guarda no resumo."""
    barra = "=" * 70
    bloco = f"\n{barra}\n{texto}\n{barra}"
    print(bloco)
    linhas_resumo.append(bloco)


def registrar(texto: str = "") -> None:
    """Imprime e guarda uma linha do relatorio."""
    print(texto)
    linhas_resumo.append(texto)


def brl(valor: float) -> str:
    """Formata numero no padrao brasileiro: 1.234,56"""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =====================================================================
# BLOCO 1 - CARGA E VERIFICACAO DE INTEGRIDADE
# =====================================================================
def bloco_1_carga() -> tuple[pd.DataFrame, pd.DataFrame]:
    titulo("BLOCO 1 - CARGA E VERIFICACAO DE INTEGRIDADE")

    caminho1, caminho2 = DATA / "query_01.csv", DATA / "query_02.csv"
    if not caminho1.exists() or not caminho2.exists():
        sys.exit(
            "ERRO: CSVs nao encontrados em data/.\n"
            "Exporte os resultados das consultas no SQL Worksheet do FreeSQL\n"
            "(botao Download > CSV) e salve como data/query_01.csv e\n"
            "data/query_02.csv. Veja a secao 6 do README."
        )

    # O Oracle devolve os nomes de coluna em MAIUSCULAS. Normalizar aqui
    # deixa o resto do script independente do banco de origem.
    df1 = pd.read_csv(caminho1)
    df2 = pd.read_csv(caminho2)
    df1.columns = [c.strip().lower() for c in df1.columns]
    df2.columns = [c.strip().lower() for c in df2.columns]
    df1["data_admissao"] = pd.to_datetime(df1["data_admissao"], errors="coerce")

    registrar(f"query_01.csv : {df1.shape[0]} linhas x {df1.shape[1]} colunas")
    registrar(f"query_02.csv : {df2.shape[0]} linhas x {df2.shape[1]} colunas")

    registrar("\nTipos de dados (query_01):")
    for coluna, tipo in df1.dtypes.items():
        registrar(f"   {coluna:<18} {tipo}")

    registrar("\nValores ausentes por coluna (query_01):")
    nulos = df1.isnull().sum()
    for coluna, qtd in nulos[nulos > 0].items():
        registrar(f"   {coluna:<18} {qtd}")
    if nulos.sum() == 0:
        registrar("   (nenhum)")

    registrar(f"\nLinhas duplicadas: {df1.duplicated().sum()}")

    # A verificacao central: os nulos NAO sao sujeira, sao informacao.
    sem_depto = df1[df1["departamento"].isna()]
    sem_regiao = df2[df2["regiao"].isna()]
    registrar(
        f"\nFuncionarios sem departamento : {len(sem_depto)}"
        f"\nFuncionarios sem regiao       : {len(sem_regiao)}"
    )
    if len(sem_depto):
        registrar("\nRegistro preservado pelo LEFT JOIN:")
        for _, linha in sem_depto.iterrows():
            registrar(
                f"   id {linha['id_funcionario']} - {linha['funcionario']} "
                f"({linha['cargo']}) - salario {brl(linha['salario'])}"
            )
        registrar(
            "\n   Este funcionario nao tem departamento cadastrado. Como a\n"
            "   localizacao no esquema HR vem do departamento, ele tambem\n"
            "   fica sem cidade, pais e regiao. Com INNER JOIN ele teria\n"
            "   sumido das duas consultas sem qualquer aviso."
        )
    return df1, df2


# =====================================================================
# BLOCO 2 - ESTATISTICA DESCRITIVA
# =====================================================================
def bloco_2_descritiva(df1: pd.DataFrame) -> None:
    titulo("BLOCO 2 - ESTATISTICA DESCRITIVA")

    s = df1["salario"]
    q1, q3 = s.quantile(0.25), s.quantile(0.75)

    registrar(f"Funcionarios      : {len(s)}")
    registrar(f"Folha total       : {brl(s.sum())}")
    registrar("")
    registrar(f"Media             : {brl(s.mean())}")
    registrar(f"Mediana           : {brl(s.median())}")
    registrar(f"Minimo            : {brl(s.min())}")
    registrar(f"Maximo            : {brl(s.max())}")
    registrar("")
    registrar(f"Desvio padrao     : {brl(s.std())}")
    registrar(f"Q1 (25%)          : {brl(q1)}")
    registrar(f"Q3 (75%)          : {brl(q3)}")
    registrar(f"IQR (Q3-Q1)       : {brl(q3 - q1)}")
    registrar(f"Coef. de variacao : {s.std() / s.mean():.1%}")
    registrar(f"Assimetria (skew) : {s.skew():.3f}")

    diferenca = (s.mean() - s.median()) / s.median()
    registrar(
        f"\nLEITURA: a media supera a mediana em {diferenca:.1%}. A distribuicao\n"
        f"e assimetrica a direita - poucos salarios altos puxam a media para\n"
        f"cima. Para descrever o funcionario tipico, a MEDIANA e a medida\n"
        f"adequada; a media descreve o custo medio da folha, nao a pessoa."
    )


# =====================================================================
# BLOCO 3 - DISTRIBUICAO E ASSIMETRIA
# =====================================================================
def bloco_3_histograma(df1: pd.DataFrame) -> None:
    titulo("BLOCO 3 - DISTRIBUICAO (HISTOGRAMA)")

    s = df1["salario"]
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.hist(s, bins=20, color=AZUL, edgecolor=SUPERFICIE, linewidth=1.5)
    ax.axvline(s.median(), color=LARANJA, linewidth=2, linestyle="-")
    ax.axvline(s.mean(), color=VERMELHO, linewidth=2, linestyle="--")

    # Rotulos diretos: evitam uma caixa de legenda para duas referencias
    topo = ax.get_ylim()[1]
    ax.text(s.median() - 400, topo * 0.92, f"mediana\n{brl(s.median())}",
            color=LARANJA, fontsize=9, ha="right", fontweight="bold")
    ax.text(s.mean() + 400, topo * 0.92, f"media\n{brl(s.mean())}",
            color=VERMELHO, fontsize=9, ha="left", fontweight="bold")

    ax.set_title(f"Distribuicao dos salarios ({len(s)} funcionarios)")
    ax.set_xlabel("Salario")
    ax.set_ylabel("Numero de funcionarios")
    ax.set_axisbelow(True)
    ax.grid(axis="x", visible=False)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))

    fig.text(0.5, -0.04,
             "A media fica a direita da mediana: sinal de assimetria positiva.",
             ha="center", fontsize=9, color=TINTA_2)

    IMG.mkdir(exist_ok=True)
    fig.savefig(IMG / "hist_salarios.png")
    plt.close(fig)
    registrar("Grafico salvo: img/hist_salarios.png")

    faixas = pd.cut(s, bins=[0, 4000, 6000, 8000, 10000, 15000, 25000],
                    labels=["ate 4k", "4k-6k", "6k-8k", "8k-10k",
                            "10k-15k", "acima de 15k"])
    registrar("\nFuncionarios por faixa salarial:")
    for faixa, qtd in faixas.value_counts().sort_index().items():
        barra = "#" * int(qtd)
        registrar(f"   {str(faixa):<14} {qtd:>3}  {barra}")


def desenhar_boxplot(ax, grupos: list[np.ndarray]) -> None:
    """Desenha um boxplot horizontal com os pontos individuais sobrepostos.

    A sobreposicao nao e enfeite: grupos com um unico funcionario produzem
    uma caixa de largura zero, que ficaria invisivel no grafico. Plotar os
    pontos garante que todo grupo apareca, mostra o tamanho real de cada
    amostra e evita que uma mediana de n=1 seja lida como uma distribuicao.

    Os outliers sao calculados por grupo (regra do IQR) e destacados em
    vermelho - por isso showfliers=False, para nao desenhar o mesmo ponto
    duas vezes.
    """
    bp = ax.boxplot(grupos, vert=False, patch_artist=True, widths=0.6,
                    showfliers=False,
                    medianprops=dict(color=SUPERFICIE, linewidth=2),
                    whiskerprops=dict(color=EIXO, linewidth=1.2),
                    capprops=dict(color=EIXO, linewidth=1.2))
    for caixa in bp["boxes"]:
        caixa.set(facecolor=AZUL_CLARO, edgecolor=SUPERFICIE, linewidth=1.5)

    rng = np.random.default_rng(11)
    for i, valores in enumerate(grupos, start=1):
        v = np.asarray(valores, dtype=float)
        if v.size == 0:
            continue
        _, _, _, inf, sup = limites_iqr(pd.Series(v))
        fora = (v < inf) | (v > sup)
        y = (i + rng.normal(0, 0.07, v.size) if v.size > 1
             else np.full(v.size, float(i)))
        ax.scatter(v[~fora], y[~fora], s=24, color=AZUL, alpha=0.9,
                   edgecolor=SUPERFICIE, linewidth=0.7, zorder=4)
        if fora.any():
            ax.scatter(v[fora], y[fora], s=44, color=VERMELHO,
                       edgecolor=SUPERFICIE, linewidth=0.9, zorder=5)


# =====================================================================
# BLOCO 4 - COMPARACAO POR DEPARTAMENTO
# =====================================================================
def bloco_4_departamento(df1: pd.DataFrame) -> None:
    titulo("BLOCO 4 - SALARIO POR DEPARTAMENTO")

    dados = df1.copy()
    dados["departamento"] = dados["departamento"].fillna("(sem departamento)")

    resumo = (dados.groupby("departamento")["salario"]
              .agg(n="size", media="mean", mediana="median",
                   minimo="min", maximo="max")
              .sort_values("mediana"))

    registrar(f"{'Departamento':<22}{'n':>4}{'mediana':>12}{'media':>12}")
    registrar("-" * 50)
    for nome, linha in resumo.sort_values("mediana", ascending=False).iterrows():
        registrar(f"{nome:<22}{int(linha['n']):>4}"
                  f"{brl(linha['mediana']):>12}{brl(linha['media']):>12}")

    ordem = resumo.index.tolist()
    grupos = [dados.loc[dados["departamento"] == d, "salario"].values
              for d in ordem]

    fig, ax = plt.subplots(figsize=(9, 6.5))
    desenhar_boxplot(ax, grupos)

    ax.set_yticklabels([f"{d}  (n={int(resumo.loc[d, 'n'])})" for d in ordem])
    ax.set_title("Salario por departamento")
    ax.set_xlabel("Salario")
    ax.set_axisbelow(True)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))

    fig.text(0.5, -0.03,
             "Cada ponto e um funcionario. Em vermelho, os valores fora dos "
             "limites do IQR do proprio grupo.",
             ha="center", fontsize=9, color=TINTA_2)

    fig.savefig(IMG / "boxplot_departamento.png")
    plt.close(fig)
    registrar("\nGrafico salvo: img/boxplot_departamento.png")

    maior, menor = resumo.index[-1], resumo.index[0]
    registrar(
        f"\nLEITURA: {maior} tem a maior mediana "
        f"({brl(resumo.loc[maior, 'mediana'])}) e {menor} a menor "
        f"({brl(resumo.loc[menor, 'mediana'])}) - uma razao de "
        f"{resumo.loc[maior, 'mediana'] / resumo.loc[menor, 'mediana']:.1f}x."
    )


# =====================================================================
# BLOCO 5 - COMPARACAO POR REGIAO
# =====================================================================
def bloco_5_regiao(df2: pd.DataFrame) -> None:
    titulo("BLOCO 5 - SALARIO E DISTRIBUICAO POR REGIAO")

    dados = df2.copy()
    dados["regiao"] = dados["regiao"].fillna("(sem regiao)")

    resumo = (dados.groupby("regiao")["salario"]
              .agg(n="size", media="mean", mediana="median")
              .sort_values("mediana"))

    registrar(f"{'Regiao':<22}{'n':>4}{'mediana':>12}{'media':>12}")
    registrar("-" * 50)
    for nome, linha in resumo.sort_values("n", ascending=False).iterrows():
        registrar(f"{nome:<22}{int(linha['n']):>4}"
                  f"{brl(linha['mediana']):>12}{brl(linha['media']):>12}")

    registrar("\nDistribuicao por pais:")
    for pais, qtd in dados["pais"].value_counts(dropna=False).items():
        registrar(f"   {str(pais):<28}{qtd:>4}")

    registrar("\nDistribuicao por cidade:")
    for cidade, qtd in dados["cidade"].value_counts(dropna=False).items():
        registrar(f"   {str(cidade):<28}{qtd:>4}")

    ordem = resumo.index.tolist()
    grupos = [dados.loc[dados["regiao"] == r, "salario"].values for r in ordem]

    fig, ax = plt.subplots(figsize=(9, 4.6))
    desenhar_boxplot(ax, grupos)

    ax.set_yticklabels([f"{r}  (n={int(resumo.loc[r, 'n'])})" for r in ordem])
    ax.set_title("Salario por regiao geografica")
    ax.set_xlabel("Salario")
    ax.set_axisbelow(True)
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))

    fig.savefig(IMG / "boxplot_regiao.png")
    plt.close(fig)
    registrar("\nGrafico salvo: img/boxplot_regiao.png")

    registrar(
        "\nLEITURA: a empresa opera em apenas 2 regioes com pessoas alocadas,\n"
        "apesar de manter 23 escritorios cadastrados em 4 regioes. A maioria\n"
        "das localidades esta cadastrada mas vazia - um achado estrutural que\n"
        "so aparece porque a consulta parte de EMPLOYEES, e nao de LOCATIONS."
    )


# =====================================================================
# BLOCO 6 - OUTLIERS E O EFEITO DO FILTRO  (bloco central da analise)
# =====================================================================
def limites_iqr(s: pd.Series) -> tuple[float, float, float, float, float]:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return q1, q3, iqr, q1 - 1.5 * iqr, q3 + 1.5 * iqr


def bloco_6_outliers(df1: pd.DataFrame) -> None:
    titulo("BLOCO 6 - OUTLIERS E O EFEITO DO FILTRO WHERE")

    s = df1["salario"]
    q1, q3, iqr, inf, sup = limites_iqr(s)
    fora = s[(s < inf) | (s > sup)]

    registrar("Metodo do intervalo interquartil (IQR), base completa:")
    registrar(f"   Q1 = {brl(q1)}   Q3 = {brl(q3)}   IQR = {brl(iqr)}")
    registrar(f"   Limite inferior = {brl(inf)}")
    registrar(f"   Limite superior = {brl(sup)}")
    registrar(f"   OUTLIERS ENCONTRADOS: {len(fora)}")

    for _, linha in df1[df1["salario"].isin(fora)].iterrows():
        registrar(f"      {linha['funcionario']} - {linha['cargo']} - "
                  f"{brl(linha['salario'])}")

    registrar(
        "\nOs valores extremos correspondem a cargos de direcao. Nao sao erros\n"
        "de digitacao nem fraude: sao a camada executiva da empresa. Remove-los\n"
        "eliminaria justamente a hierarquia que a analise quer descrever."
    )

    # -----------------------------------------------------------------
    # A demonstracao central: a contagem de outliers depende do filtro
    # -----------------------------------------------------------------
    registrar("\n" + "-" * 70)
    registrar("O EFEITO DO FILTRO SOBRE A CONTAGEM DE OUTLIERS")
    registrar("-" * 70)

    cenarios = [
        ("Sem filtro", s),
        ("WHERE salario > 3000", s[s > 3000]),
        ("WHERE salario > 5000", s[s > 5000]),
    ]

    registrar(f"{'Cenario':<24}{'n':>5}{'IQR':>11}{'lim. sup.':>12}{'outliers':>10}")
    registrar("-" * 62)
    resultados = []
    for nome, serie in cenarios:
        _q1, _q3, _iqr, _inf, _sup = limites_iqr(serie)
        n_fora = int(((serie < _inf) | (serie > _sup)).sum())
        resultados.append((nome, serie, _iqr, _sup, n_fora))
        registrar(f"{nome:<24}{len(serie):>5}{brl(_iqr):>11}"
                  f"{brl(_sup):>12}{n_fora:>10}")

    registrar(
        "\nLEITURA: a mesma empresa, com as mesmas pessoas, produz 1 ou 3\n"
        "outliers dependendo apenas do filtro aplicado na consulta SQL.\n"
        "Cortar em 5000 remove a cauda inferior, comprime o IQR em 46% e\n"
        "derruba o limite superior de 17.600 para 15.100 - fazendo os dois\n"
        "Vice-Presidentes (17.000) 'virarem' outliers. Eles nao mudaram de\n"
        "salario; mudou a regua.\n"
        "Por isso a Query 1 filtra por 'SALARY IS NOT NULL' e nao por\n"
        "'SALARY > X': a contagem de outliers so e interpretavel sobre a\n"
        "distribuicao completa."
    )

    # Grafico de 3 paineis (small multiples, mesma escala nos tres)
    fig, eixos = plt.subplots(1, 3, figsize=(13, 4.6), sharey=True)
    for ax, (nome, serie, _iqr, _sup, n_fora) in zip(eixos, resultados):
        dentro = serie[serie <= _sup]
        fora_c = serie[serie > _sup]

        ax.scatter(np.random.default_rng(7).normal(0, 0.06, len(dentro)),
                   dentro, s=26, color=AZUL, alpha=0.75,
                   edgecolor=SUPERFICIE, linewidth=0.6, zorder=3)
        if len(fora_c):
            ax.scatter(np.random.default_rng(7).normal(0, 0.06, len(fora_c)),
                       fora_c, s=60, color=VERMELHO,
                       edgecolor=SUPERFICIE, linewidth=1.2, zorder=4)

        ax.axhline(_sup, color=VERMELHO, linewidth=1.6, linestyle="--", zorder=2)
        ax.text(0.30, _sup + 600, f"limite {brl(_sup)}", color=VERMELHO,
                fontsize=8.5, ha="right", fontweight="bold")

        ax.set_title(f"{nome}\nn={len(serie)}  |  {n_fora} outlier(s)",
                     fontsize=11)
        ax.set_xlim(-0.35, 0.35)
        ax.set_xticks([])
        ax.grid(axis="x", visible=False)
        ax.set_axisbelow(True)

    eixos[0].set_ylabel("Salario")
    eixos[0].yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))

    fig.suptitle("A contagem de outliers depende do filtro, nao dos dados",
                 fontsize=14, fontweight="bold", y=1.04)
    fig.text(0.5, -0.06,
             "Mesmas pessoas nos tres paineis. Cortar em 5.000 comprime o IQR e "
             "transforma os dois Vice-Presidentes em outliers.",
             ha="center", fontsize=9.5, color=TINTA_2)

    fig.savefig(IMG / "outliers_efeito_filtro.png")
    plt.close(fig)
    registrar("\nGrafico salvo: img/outliers_efeito_filtro.png")


# =====================================================================
# BLOCO 7 - CONFORMIDADE DE BANDA SALARIAL
# =====================================================================
def bloco_7_bandas(df1: pd.DataFrame) -> None:
    titulo("BLOCO 7 - CONFORMIDADE DE BANDA SALARIAL POR CARGO")

    d = df1.dropna(subset=["piso_cargo", "teto_cargo"]).copy()
    # Posicao relativa dentro da banda: 0 = piso do cargo, 1 = teto
    d["pos_banda"] = ((d["salario"] - d["piso_cargo"])
                      / (d["teto_cargo"] - d["piso_cargo"]))
    # Compa-ratio: indicador classico de RH (salario / ponto medio da banda)
    d["compa_ratio"] = d["salario"] / ((d["piso_cargo"] + d["teto_cargo"]) / 2)

    fora = d[(d["pos_banda"] < 0) | (d["pos_banda"] > 1)]
    abaixo_meio = (d["compa_ratio"] < 1).sum()

    registrar(f"Funcionarios FORA da banda do proprio cargo : {len(fora)}")
    registrar(f"Compa-ratio medio da empresa                : "
              f"{d['compa_ratio'].mean():.3f}")
    registrar(f"Abaixo do ponto medio da banda              : "
              f"{abaixo_meio} de {len(d)} ({abaixo_meio/len(d):.1%})")

    registrar(
        "\nLEITURA: nenhum salario viola a faixa definida para o cargo - as\n"
        "bandas sao formalmente respeitadas. Mas 3 em cada 4 funcionarios\n"
        "estao ABAIXO do ponto medio da propria banda, e o compa-ratio medio\n"
        "de 0,88 mostra que a empresa opera sistematicamente no terco\n"
        "inferior das faixas que ela mesma definiu."
    )

    resumo = (d.groupby("cargo")
              .agg(n=("salario", "size"), pos=("pos_banda", "mean"),
                   compa=("compa_ratio", "mean"))
              .sort_values("pos"))

    registrar(f"\n{'Cargo':<34}{'n':>4}{'posicao':>10}{'compa':>8}")
    registrar("-" * 56)
    for cargo, linha in resumo.iterrows():
        registrar(f"{cargo:<34}{int(linha['n']):>4}"
                  f"{linha['pos']:>10.2f}{linha['compa']:>8.2f}")

    # Grafico: faixa cinza = banda do cargo (0 a 1); pontos = funcionarios
    fig, ax = plt.subplots(figsize=(9.5, 7.5))
    for i, cargo in enumerate(resumo.index):
        ax.barh(i, 1.0, height=0.62, color=GRADE, zorder=1)
        valores = d.loc[d["cargo"] == cargo, "pos_banda"]
        ax.scatter(valores, np.full(len(valores), i), s=42, color=AZUL,
                   alpha=0.8, edgecolor=SUPERFICIE, linewidth=0.8, zorder=3)
        ax.scatter([resumo.loc[cargo, "pos"]], [i], s=110, marker="|",
                   color=AZUL_ESCURO, linewidth=2.5, zorder=4)

    ax.axvline(0.5, color=LARANJA, linewidth=1.8, linestyle="--", zorder=2)
    ax.text(0.505, len(resumo) - 0.3, "ponto medio da banda", color=LARANJA,
            fontsize=9, fontweight="bold")

    ax.set_yticks(range(len(resumo)))
    ax.set_yticklabels([f"{c}  (n={int(resumo.loc[c, 'n'])})"
                        for c in resumo.index])
    ax.set_xlim(-0.03, 1.03)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["piso\ndo cargo", "25%", "50%", "75%", "teto\ndo cargo"])
    ax.set_title("Posicao do salario dentro da banda definida para o cargo")
    ax.set_xlabel("")
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)

    fig.text(0.5, -0.03,
             "Nenhum ponto fora da faixa cinza: as bandas sao respeitadas. "
             "Mas a maioria se concentra a esquerda do ponto medio.",
             ha="center", fontsize=9.5, color=TINTA_2)

    fig.savefig(IMG / "bandas_salariais.png")
    plt.close(fig)
    registrar("\nGrafico salvo: img/bandas_salariais.png")

    # O achado que inverte a leitura do Bloco 6
    presidente = d[d["cargo"] == "President"]
    if len(presidente):
        p = presidente.iloc[0]
        topo = d.loc[d["pos_banda"].idxmax()]
        onde = ("exatamente no teto do cargo" if topo["pos_banda"] >= 0.999
                else "quase no teto do cargo")
        registrar(
            f"\nACHADO QUE INVERTE A LEITURA DOS OUTLIERS:\n"
            f"   {p['funcionario']} ({p['cargo']}) ganha {brl(p['salario'])} - o\n"
            f"   maior salario da empresa e o unico outlier estatistico. Mas a\n"
            f"   banda do cargo vai de {brl(p['piso_cargo'])} a {brl(p['teto_cargo'])}:\n"
            f"   ele esta na posicao {p['pos_banda']:.2f} da propria faixa, ABAIXO\n"
            f"   do ponto medio (compa-ratio {p['compa_ratio']:.2f}).\n"
            f"\n   Em contraste, {topo['funcionario']} ({topo['cargo']}) ganha\n"
            f"   {brl(topo['salario'])} - nem aparece como outlier - mas esta\n"
            f"   {onde} (posicao {topo['pos_banda']:.2f}).\n"
            f"\n   Ou seja: o 'outlier' e um artefato de comparar cargos com\n"
            f"   faixas diferentes. Normalizando pela banda, quem parecia\n"
            f"   extremo passa a ser modestamente remunerado para a funcao."
        )


# =====================================================================
# BLOCO 8 - REMUNERACAO TOTAL COM COMISSAO
# =====================================================================
def bloco_8_comissao(df1: pd.DataFrame) -> None:
    titulo("BLOCO 8 - REMUNERACAO TOTAL (SALARIO + COMISSAO)")

    d = df1.copy()
    d["pct_comissao"] = d["pct_comissao"].fillna(0)
    d["remuneracao_total"] = d["salario"] * (1 + d["pct_comissao"])

    com = d[d["pct_comissao"] > 0]
    registrar(f"Funcionarios com comissao : {len(com)} de {len(d)}")
    registrar(f"Departamentos envolvidos  : "
              f"{', '.join(sorted(com['departamento'].dropna().unique()))}")
    registrar(f"Comissao media            : {com['pct_comissao'].mean():.1%}")

    registrar("\nComparacao por departamento (mediana):")
    registrar(f"{'Departamento':<22}{'so salario':>14}{'com comissao':>16}{'dif':>8}")
    registrar("-" * 60)
    dd = d.copy()
    dd["departamento"] = dd["departamento"].fillna("(sem departamento)")
    tabela = dd.groupby("departamento").agg(
        base=("salario", "median"), total=("remuneracao_total", "median"))
    for nome, linha in tabela.sort_values("total", ascending=False).iterrows():
        dif = (linha["total"] / linha["base"] - 1)
        registrar(f"{nome:<22}{brl(linha['base']):>14}"
                  f"{brl(linha['total']):>16}{dif:>7.0%}")

    registrar(
        "\nLEITURA: a comissao existe apenas em Sales. Analisar somente o\n"
        "salario-base subestima a remuneracao dessa area e distorce qualquer\n"
        "comparacao entre departamentos. Este bloco usa a coluna\n"
        "COMMISSION_PCT, que as duas consultas trouxeram justamente para\n"
        "tornar a comparacao honesta."
    )


# =====================================================================
def main() -> None:
    print("\n" + "#" * 70)
    print("#  ANALISE EXPLORATORIA DE DADOS - ESQUEMA HR")
    print("#  Leo Gobel - Visualizacao de Dados e Business Intelligence T2")
    print("#" * 70)

    df1, df2 = bloco_1_carga()
    bloco_2_descritiva(df1)
    bloco_3_histograma(df1)
    bloco_4_departamento(df1)
    bloco_5_regiao(df2)
    bloco_6_outliers(df1)
    bloco_7_bandas(df1)
    bloco_8_comissao(df1)

    titulo("FIM DA ANALISE")
    registrar("5 graficos gravados em img/")
    registrar("Resumo completo em data/resultados.txt")

    (DATA / "resultados.txt").write_text(
        "\n".join(linhas_resumo), encoding="utf-8")


if __name__ == "__main__":
    main()
