# Especificação Completa das Variáveis

Quadro de variáveis do estudo, incluindo definição operacional, fonte e tratamento aplicado.

## Variáveis Dependentes

| Variável | Definição | Fonte (CVM) | Tratamento |
|---|---|---|---|
| **RENTAB_MES** | Variação percentual mensal do valor da cota por classe | Tab. X_3 | Winsorização: obs. com \|val\| > 50% excluídas como outliers de reporte |
| **VOLATILIDADE** | Desvio-padrão das rentabilidades em janela móvel de 3 meses (mín. 2 obs.) | Construída a partir da Tab. X_3 | Winsorização no percentil 99 por ano |
| **DRAWDOWN** | Perda percentual acumulada em relação ao pico histórico: DD = (V_max − V_t) / V_max | Construída a partir da Tab. X_2 | Winsorização ao intervalo [0, 1]; calculado por ID fundo-classe |
| **SHARPE** | Razão RENTAB_MES / VOLATILIDADE | Construída | Winsorização no intervalo [−10, +10]; obs. com VOLATILIDADE = 0 excluídas |
| **TAXA_INAD** | Razão entre créditos vencidos inadimplentes e total de direitos creditórios com risco | Tab. I | Winsorização ao intervalo [0, 1]; obs. com denominador = 0 excluídas |

## Variáveis Explicativas de Governança

| Variável | Definição | Fonte (CVM) | Tratamento |
|---|---|---|---|
| **DESVIO_GC** | Módulo da diferença entre desempenho realizado e esperado da cota: \|DESEMP_REAL − DESEMP_ESPERADO\| | Tab. X_6 | Winsorização no percentil 99 por ano |
| **GC_ALINHADO** | Variável binária: assume 1 quando DESVIO_GC = 0 | Construída a partir da Tab. X_6 | Nenhum; derivada diretamente de DESVIO_GC |

## Variáveis de Controle

| Variável | Definição | Fonte (CVM) | Tratamento |
|---|---|---|---|
| **LOG_PL** | Logaritmo natural do patrimônio líquido do fundo: ln(max(PL, 1)) | Tab. IV | Imputação de PL ≤ 0 como 0 (equivalente a R$ 1) |
| **D_SENIOR** | Variável binária: assume 1 para cotas sênior | Construída a partir da Tab. X_3 | Normalização textual: variações como "Sênior 1", "Senior", "Classe Sênior" mapeadas para categoria única |

## Variáveis de Tratamento (DiD)

| Variável | Definição | Fonte (CVM) | Tratamento |
|---|---|---|---|
| **D_POS_CVM175** | Variável binária: assume 1 para meses a partir de janeiro de 2023 (vigência efetiva da Resolução CVM nº 175/2022) | Construída | Nenhum; determinística |

## Variáveis Auxiliares

| Variável | Definição | Fonte (CVM) | Tratamento |
|---|---|---|---|
| **VL_COTA** | Valor unitário da cota em R$ ao final do mês | Tab. X_2 | Valores negativos excluídos como erros de reporte |
| **ANO** | Ano de competência da observação; utilizado como variável de efeito temporal | Construída | Extraído da coluna DT_COMPTC |
| **ID** | Identificador único do par fundo-classe: CNPJ_FUNDO concatenado com CLASSE_NORM | Construída | Chave de identificação para within-demeaning nos modelos FE |

## Tabelas da CVM Utilizadas

As tabelas dos informes mensais utilizadas são:

- **Tabela X_3** — Rentabilidade mensal por classe de série
- **Tabela X_6** — Desempenho esperado versus realizado por classe de série
- **Tabela X_2** — Quantidade de cotas e valor unitário por classe de série
- **Tabela IV** — Patrimônio líquido do fundo
- **Tabela I** — Composição do ativo, concentração de cedentes e créditos inadimplentes

A partir de outubro de 2023, os dados passaram a incluir também a Tabela X (rating SCR por devedor e por operação), não utilizada neste trabalho, mas disponível para pesquisas futuras.

## Mudança de Layout (Outubro de 2023)

Em decorrência da Resolução CVM nº 175/2022, a CVM reformulou o layout dos informes mensais a partir de outubro de 2023. As principais alterações foram:

- A coluna `CNPJ_FUNDO` foi substituída por `CNPJ_FUNDO_CLASSE` (CNPJ da classe, não do fundo consolidado)
- A coluna `TP_FUNDO_CLASSE` foi adicionada

O pipeline (função `ler_csv`) detecta automaticamente o layout vigente em cada período e aplica o mapeamento correto da chave de identificação, preservando a integridade longitudinal das séries.
