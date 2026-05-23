"""
Pipeline de coleta, tratamento e estimação econométrica
=======================================================

Replicação dos resultados do artigo:
    Albuquerque, J. C., & Abreu, E. S. (2026).
    Governança Corporativa em Fundos de Investimento em Direitos
    Creditórios no Brasil: Volatilidade e a Resolução CVM nº 175/2022.
    XX Congresso ANPCONT.

Módulos:
    C.1 — Extração dos arquivos mensais da CVM
    C.2 — Construção do painel fundo-classe-mês
    C.3 — Limpeza, normalização e construção das variáveis
    C.4 — Estimação dos modelos de efeitos fixos (OLS within + HC1)
    C.5 — Estimação do modelo de diferenças em diferenças

Requisitos: Python 3.12+, pandas, numpy, scipy
"""

import os
import zipfile
import glob
import pandas as pd
import numpy as np
from scipy import stats

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

PASTA_ZIPS = "./dados_cvm/zips/"
PASTA_DADOS = "./dados_cvm/csv/"

os.makedirs(PASTA_ZIPS, exist_ok=True)
os.makedirs(PASTA_DADOS, exist_ok=True)


# ============================================================================
# C.1 — Extração dos arquivos mensais da CVM
# ============================================================================

def extrair_arquivos():
    """Extrai todos os arquivos .zip da pasta de origem."""
    for arq_zip in sorted(glob.glob(PASTA_ZIPS + "*.zip")):
        with zipfile.ZipFile(arq_zip, "r") as z:
            z.extractall(PASTA_DADOS)
    print(f"Arquivos extraídos: {len(os.listdir(PASTA_DADOS))}")


# ============================================================================
# C.2 — Construção do painel fundo-classe-mês
# ============================================================================

def norm_classe(c):
    """Normaliza variações textuais de classe de cota."""
    c = str(c).strip().lower()
    if any(t in c for t in ["senior", "sénior", "sênior"]):
        return "Senior"
    if any(t in c for t in ["subordinada", "mezanino", "mezzanino"]):
        return "Subordinada"
    return "Outra"


def ler_csv(path):
    """
    Lê CSV e normaliza a coluna de CNPJ conforme layout.
    Detecta automaticamente layout pré e pós CVM 175 (out/2023):
        - Pré:  CNPJ_FUNDO
        - Pós:  CNPJ_FUNDO_CLASSE
    """
    df = pd.read_csv(path, sep=";", encoding="latin1")
    if "CNPJ_FUNDO_CLASSE" in df.columns:
        df = df.rename(columns={
            "CNPJ_FUNDO_CLASSE": "CNPJ",
            "DT_COMPTC": "DT",
            "DENOM_SOCIAL": "NOME",
        })
    elif "CNPJ_FUNDO" in df.columns:
        df = df.rename(columns={
            "CNPJ_FUNDO": "CNPJ",
            "DT_COMPTC": "DT",
            "DENOM_SOCIAL": "NOME",
        })
    return df


def coletar_frames():
    """Coleta todos os arquivos CSV organizados por tabela e mês."""
    meses = sorted(set(
        f.split("_X_3_")[1].replace(".csv", "") if "_X_3_" in f else ""
        for f in os.listdir(PASTA_DADOS)
    ) - {""})

    frames = {k: [] for k in ["x3", "x2", "x6", "iv", "inad"]}
    COLS_INAD = {
        "CNPJ_FUNDO", "DT_COMPTC",
        "TAB_I2A2_VL_CRED_VENC_INAD", "TAB_I2A_VL_DIRCRED_RISCO",
        "CNPJ_FUNDO_CLASSE",
    }

    for mes in meses:
        for tag, lst in [("X_3", "x3"), ("X_2", "x2"),
                         ("X_6", "x6"), ("IV", "iv")]:
            f = f"{PASTA_DADOS}inf_mensal_fidc_tab_{tag}_{mes}.csv"
            if os.path.exists(f):
                frames[lst].append(ler_csv(f))
        f = f"{PASTA_DADOS}inf_mensal_fidc_tab_I_{mes}.csv"
        if os.path.exists(f):
            df = pd.read_csv(
                f, sep=";", encoding="latin1",
                usecols=lambda c: c in COLS_INAD,
            )
            if len(df.columns) >= 2:
                frames["inad"].append(df)

    print(f"Meses processados: {len(meses)} ({meses[0]} → {meses[-1]})")
    return frames


# ============================================================================
# C.3 — Limpeza, normalização e construção das variáveis
# ============================================================================

def construir_painel(frames):
    """Constrói o painel fundo-classe-mês com todas as variáveis."""

    # --- Rentabilidade (X_3) ---
    rent = pd.concat(frames["x3"], ignore_index=True)
    rent = rent.rename(columns={
        "TAB_X_CLASSE_SERIE": "CLASSE",
        "TAB_X_VL_RENTAB_MES": "RENTAB_MES",
    })
    rent["DT"] = pd.to_datetime(rent["DT"])
    rent["CLASSE_NORM"] = rent["CLASSE"].apply(norm_classe)
    rent["RENTAB_MES"] = pd.to_numeric(rent["RENTAB_MES"], errors="coerce")
    rent = rent[rent["CLASSE_NORM"].isin(["Senior", "Subordinada"])]

    # --- Valor de cota (X_2) — para cálculo de drawdown ---
    cotas = pd.concat(frames["x2"], ignore_index=True)
    cotas = cotas.rename(columns={
        "TAB_X_CLASSE_SERIE": "CLASSE",
        "TAB_X_QT_COTA": "QT_COTA",
        "TAB_X_VL_COTA": "VL_COTA",
    })
    cotas["DT"] = pd.to_datetime(cotas["DT"])
    cotas["CLASSE_NORM"] = cotas["CLASSE"].apply(norm_classe)
    cotas["VL_COTA"] = pd.to_numeric(cotas["VL_COTA"], errors="coerce")

    # --- Desvio de governança (X_6) ---
    desemp = pd.concat(frames["x6"], ignore_index=True)
    desemp = desemp.rename(columns={
        "TAB_X_CLASSE_SERIE": "CLASSE",
        "TAB_X_PR_DESEMP_ESPERADO": "DESEMP_ESPERADO",
        "TAB_X_PR_DESEMP_REAL": "DESEMP_REAL",
    })
    desemp["DT"] = pd.to_datetime(desemp["DT"])
    desemp["CLASSE_NORM"] = desemp["CLASSE"].apply(norm_classe)
    desemp["DESEMP_ESPERADO"] = pd.to_numeric(
        desemp["DESEMP_ESPERADO"], errors="coerce"
    )
    desemp["DESEMP_REAL"] = pd.to_numeric(
        desemp["DESEMP_REAL"], errors="coerce"
    )
    # Proxy central de governança: desvio absoluto entre esperado e realizado
    desemp["DESVIO_GC"] = (
        desemp["DESEMP_REAL"] - desemp["DESEMP_ESPERADO"]
    ).abs()

    # --- Patrimônio líquido (Tab IV) ---
    pl = pd.concat(frames["iv"], ignore_index=True)
    pl = pl.rename(columns={
        "TAB_IV_A_VL_PL": "VL_PL",
        "TAB_IV_B_VL_PL_MEDIO": "VL_PL_MEDIO",
    })
    pl["DT"] = pd.to_datetime(pl["DT"])
    pl["VL_PL"] = pd.to_numeric(pl["VL_PL"], errors="coerce")

    # --- Inadimplência (Tab I) ---
    inad = pd.concat(frames["inad"], ignore_index=True)
    if "CNPJ_FUNDO_CLASSE" in inad.columns:
        inad = inad.rename(columns={
            "CNPJ_FUNDO_CLASSE": "CNPJ",
            "DT_COMPTC": "DT",
        })
    else:
        inad = inad.rename(columns={
            "CNPJ_FUNDO": "CNPJ",
            "DT_COMPTC": "DT",
        })
    inad["DT"] = pd.to_datetime(inad["DT"], errors="coerce")
    for col in ["TAB_I2A2_VL_CRED_VENC_INAD", "TAB_I2A_VL_DIRCRED_RISCO"]:
        if col in inad.columns:
            inad[col] = pd.to_numeric(inad[col], errors="coerce")
    # Taxa de inadimplência = créditos vencidos inadimplentes / total com risco
    inad["TAXA_INAD"] = (
        inad["TAB_I2A2_VL_CRED_VENC_INAD"]
        / inad["TAB_I2A_VL_DIRCRED_RISCO"].replace(0, np.nan)
    )

    # --- Montar painel base ---
    painel = rent[["CNPJ", "NOME", "DT", "CLASSE_NORM", "RENTAB_MES"]].copy()

    gc_m = (
        desemp[["CNPJ", "DT", "CLASSE_NORM",
                "DESVIO_GC", "DESEMP_ESPERADO", "DESEMP_REAL"]]
        .drop_duplicates(["CNPJ", "DT", "CLASSE_NORM"])
    )
    painel = painel.merge(
        gc_m, on=["CNPJ", "DT", "CLASSE_NORM"], how="left"
    )

    pl_m = pl[["CNPJ", "DT", "VL_PL"]].drop_duplicates(["CNPJ", "DT"])
    painel = painel.merge(pl_m, on=["CNPJ", "DT"], how="left")

    inad_m = inad[["CNPJ", "DT", "TAXA_INAD"]].drop_duplicates(["CNPJ", "DT"])
    painel = painel.merge(inad_m, on=["CNPJ", "DT"], how="left")

    # --- Drawdown por ID fundo-classe ---
    painel["ID"] = painel["CNPJ"] + "_" + painel["CLASSE_NORM"]
    c = cotas[cotas["CLASSE_NORM"].isin(["Senior", "Subordinada"])].copy()
    c["ID"] = c["CNPJ"] + "_" + c["CLASSE_NORM"]
    c = c.sort_values(["ID", "DT"])
    c["VL_COTA_MAX"] = c.groupby("ID")["VL_COTA"].cummax()
    c["DRAWDOWN"] = (
        (c["VL_COTA_MAX"] - c["VL_COTA"])
        / c["VL_COTA_MAX"].replace(0, np.nan)
    )
    c = c[["CNPJ", "DT", "CLASSE_NORM", "DRAWDOWN"]].drop_duplicates(
        ["CNPJ", "DT", "CLASSE_NORM"]
    )
    painel = painel.merge(c, on=["CNPJ", "DT", "CLASSE_NORM"], how="left")

    # --- Volatilidade móvel (3 meses) ---
    painel = painel.sort_values(["ID", "DT"])
    painel["VOLATILIDADE"] = (
        painel.groupby("ID")["RENTAB_MES"]
        .transform(lambda x: x.rolling(3, min_periods=2).std())
    )

    # --- Limpeza e winsorização ---
    painel.loc[painel["RENTAB_MES"].abs() > 50, "RENTAB_MES"] = np.nan
    painel["TAXA_INAD"] = painel["TAXA_INAD"].clip(0, 1)
    painel["DRAWDOWN"] = painel["DRAWDOWN"].clip(0, 1)

    for col in ["DESVIO_GC", "VOLATILIDADE"]:
        p99 = painel[col].quantile(0.99)
        painel[col] = painel[col].clip(0, p99)

    # --- Variáveis derivadas ---
    painel["LOG_PL"] = np.log(painel["VL_PL"].clip(lower=1))
    painel["D_SENIOR"] = (painel["CLASSE_NORM"] == "Senior").astype(int)
    painel["GC_ALINHADO"] = (painel["DESVIO_GC"] == 0).astype(int)
    painel["SHARPE"] = (
        painel["RENTAB_MES"] / painel["VOLATILIDADE"].replace(0, np.nan)
    ).clip(-10, 10)
    painel["D_POS_CVM175"] = (painel["DT"] >= "2023-01-01").astype(int)
    painel["ANO"] = painel["DT"].dt.year

    # --- Filtro de qualidade: mínimo de 12 meses por ID ---
    contagem = painel.groupby("ID")["DT"].count()
    painel = painel[painel["ID"].isin(contagem[contagem >= 12].index)]

    print(f"Painel final: {len(painel):,} obs"
          f" | {painel['CNPJ'].nunique():,} fundos"
          f" | {painel['ID'].nunique():,} IDs fundo-classe")
    return painel


# ============================================================================
# C.4 — Estimação dos modelos de efeitos fixos (OLS within + HC1)
# ============================================================================

def ols_fe_hc1(dep_var, indep_vars, data):
    """
    OLS com within-transformation (efeitos fixos por ID)
    e erros-padrão robustos à heteroscedasticidade HC1.

    Retorna coeficientes, SE, t e p-valores.
    """
    cols = ["ID"] + [dep_var] + indep_vars
    sub = data[cols].copy().dropna()

    # Within-demeaning: subtrair média do grupo de cada variável
    grp = sub.groupby("ID")
    for col in [dep_var] + indep_vars:
        sub[col + "_dm"] = sub[col] - grp[col].transform("mean")

    y = sub[dep_var + "_dm"].values
    X = np.column_stack([sub[v + "_dm"].values for v in indep_vars])

    # OLS por mínimos quadrados
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape

    # Erros-padrão robustos HC1 (corrigidos por n / (n - k))
    e2 = resid ** 2
    XtXinv = np.linalg.pinv(X.T @ X)
    meat = X.T @ (X * e2[:, None])
    V_HC1 = (n / (n - k)) * XtXinv @ meat @ XtXinv
    se = np.sqrt(np.diag(V_HC1))

    t_stat = beta / (se + 1e-12)
    df_res = max(n - k - 1, 1)
    p_val = 2 * (1 - stats.t.cdf(np.abs(t_stat), df_res))

    # R² within
    ss_res = resid @ resid
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return {
        "coefs": beta, "se": se, "t": t_stat, "p": p_val,
        "r2": r2, "n": n, "vars": indep_vars,
    }


def estimar_modelos_fe(painel):
    """Estima os cinco modelos de efeitos fixos."""
    INDEP = ["GC_ALINHADO", "DESVIO_GC", "LOG_PL", "D_SENIOR"]

    modelos = {
        "Rentabilidade":  ols_fe_hc1("RENTAB_MES",  INDEP, painel),
        "Inadimplencia":  ols_fe_hc1(
            "TAXA_INAD", INDEP, painel.dropna(subset=["TAXA_INAD"])),
        "Volatilidade":   ols_fe_hc1("VOLATILIDADE", INDEP, painel),
        "Drawdown":       ols_fe_hc1(
            "DRAWDOWN", INDEP, painel.dropna(subset=["DRAWDOWN"])),
        "Sharpe":         ols_fe_hc1(
            "SHARPE", INDEP, painel.dropna(subset=["SHARPE"])),
    }

    for nome, res in modelos.items():
        print(f"\n=== {nome} | N={res['n']:,} | R²={res['r2']:.4f} ===")
        for i, var in enumerate(res["vars"]):
            p = res["p"][i]
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            print(f"  {var:<20} β={res['coefs'][i]:+.4f}"
                  f"  SE={res['se'][i]:.4f}"
                  f"  p={res['p'][i]:.4f} {sig}")

    return modelos


# ============================================================================
# C.5 — Estimação do modelo de diferenças em diferenças
# ============================================================================

def estimar_did(painel):
    """
    Diferenças em Diferenças: impacto da Resolução CVM 175/2022.
    Corte temporal: jan/2023 (D_POS_CVM175 = 1).
    Comparação pareada por fundo entre médias pré e pós.
    """
    # Fundos com dados nos dois períodos (balanceamento)
    ids_pre = set(painel[painel["D_POS_CVM175"] == 0]["ID"])
    ids_pos = set(painel[painel["D_POS_CVM175"] == 1]["ID"])
    ids_bal = ids_pre & ids_pos
    df_did = painel[painel["ID"].isin(ids_bal)].copy()

    print(f"\nFundos balanceados: {len(ids_bal):,}")

    resultados = {}
    for dep, label in [
        ("GC_ALINHADO",  "GC Alinhado"),
        ("TAXA_INAD",    "Inadimplência"),
        ("RENTAB_MES",   "Rentabilidade"),
        ("VOLATILIDADE", "Volatilidade"),
        ("DRAWDOWN",     "Drawdown"),
    ]:
        pre = df_did[df_did["D_POS_CVM175"] == 0].groupby("ID")[dep].mean().dropna()
        pos = df_did[df_did["D_POS_CVM175"] == 1].groupby("ID")[dep].mean().dropna()
        ci = pre.index.intersection(pos.index)
        t, p = stats.ttest_rel(pos[ci], pre[ci])
        delta = pos[ci].mean() - pre[ci].mean()
        sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "n.s."
        print(f"{label:<18} pré={pre[ci].mean():.4f}"
              f" pós={pos[ci].mean():.4f}"
              f" Δ={delta:+.4f} t={t:.3f} p={p:.4f} {sig}")
        resultados[label] = {
            "pre": pre[ci].mean(), "pos": pos[ci].mean(),
            "delta": delta, "t": t, "p": p,
        }

    return resultados


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Pipeline FIDC — Governança e Resolução CVM 175/2022")
    print("=" * 70)

    # C.1 — Extração
    print("\n[C.1] Extraindo arquivos da CVM...")
    extrair_arquivos()

    # C.2 — Coleta dos frames por tabela
    print("\n[C.2] Coletando frames por tabela...")
    frames = coletar_frames()

    # C.3 — Construção do painel
    print("\n[C.3] Construindo painel fundo-classe-mês...")
    painel = construir_painel(frames)

    # Salvar painel intermediário (opcional)
    painel.to_csv("painel_final.csv", index=False)
    print("Painel salvo em painel_final.csv")

    # C.4 — Modelos de efeitos fixos
    print("\n[C.4] Estimando modelos de efeitos fixos...")
    modelos = estimar_modelos_fe(painel)

    # C.5 — Diferenças em diferenças
    print("\n[C.5] Estimando modelo de diferenças em diferenças...")
    resultados_did = estimar_did(painel)

    print("\n" + "=" * 70)
    print("Pipeline concluído.")
    print("=" * 70)
