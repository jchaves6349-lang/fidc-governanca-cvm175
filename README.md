# Governança Corporativa em FIDC no Brasil: Pipeline de Dados e Modelos Econométricos

Repositório de replicação do artigo:

> **Albuquerque, J. C., & Abreu, E. S.** (2026). Governança Corporativa em Fundos de Investimento em Direitos Creditórios no Brasil: Volatilidade e a Resolução CVM nº 175/2022. *XX Congresso ANPCONT.*

---

## Sobre

Este repositório contém o pipeline completo de coleta, tratamento e estimação econométrica utilizado no artigo. O código processa 74 arquivos mensais públicos da Comissão de Valores Mobiliários (CVM) referentes ao período de janeiro de 2020 a fevereiro de 2026, construindo um painel desbalanceado de **462.937 observações fundo–classe–mês** para **3.949 FIDC** e **7.603 IDs fundo-classe**.

O pipeline estima cinco modelos de efeitos fixos com erros-padrão robustos HC1 e um modelo de diferenças em diferenças para a transição regulatória de janeiro de 2023 (vigência efetiva da Resolução CVM nº 175/2022).

## Estrutura do repositório

```
.
├── README.md                    # Este arquivo
├── LICENSE                      # MIT License
├── requirements.txt             # Bibliotecas Python necessárias
├── pipeline.py                  # Script principal (4 módulos)
└── docs/
    └── variaveis.md             # Especificação completa das variáveis
```

## Como usar

### 1. Pré-requisitos

- Python 3.12 ou superior
- Bibliotecas: pandas, numpy, scipy

### 2. Instalação

```bash
# Clone o repositório
git clone https://github.com/jchaves6349-lang/fidc-governanca-cvm175.git
cd fidc-governanca-cvm175

# Instale as dependências
pip install -r requirements.txt
```

### 3. Baixar os dados da CVM

Os dados são públicos e disponibilizados pela CVM no Portal de Dados Abertos:

- **Informes mensais dos FIDC:** https://dados.cvm.gov.br/dataset/fidc-doc-inf_mensal

Baixe os arquivos `.zip` mensais do período de interesse (jan/2020 a fev/2026 no artigo original) e coloque-os em `./dados_cvm/zips/`.

### 4. Executar o pipeline

```bash
python pipeline.py
```

O script é organizado em quatro módulos sequenciais:

1. **C.1 — Extração** dos arquivos `.zip` da CVM
2. **C.2 — Construção** do painel fundo-classe-mês, com detecção automática do layout pré e pós CVM 175 (out/2023)
3. **C.3 — Limpeza** e construção das variáveis (DESVIO_GC, GC_ALINHADO, VOLATILIDADE, DRAWDOWN, SHARPE, TAXA_INAD, LOG_PL, D_POS_CVM175)
4. **C.4 — Estimação** dos modelos de efeitos fixos com erros-padrão robustos HC1
5. **C.5 — Estimação** do modelo de diferenças em diferenças

## Reprodução dos resultados

Os principais resultados reportados no artigo são:

| Modelo | Variável dependente | β (GC_ALINHADO) | p-valor |
|---|---|---|---|
| M1 | Rentabilidade | −0,1784 | < 0,001 |
| M2 | Inadimplência | +0,0149 | < 0,001 |
| M3 | Volatilidade | −0,4029 | < 0,001 |
| M4 | Drawdown | +0,1889 | < 0,001 |
| M5 | Sharpe | −0,2117 | < 0,001 |

Diferenças em Diferenças (Resolução CVM nº 175/2022):

| Variável | Δ (γ̂) | p-valor |
|---|---|---|
| GC Alinhado | +0,0320 | < 0,001 |
| Volatilidade | −0,2475 | 0,023 |

## Limitações conhecidas

- A proxy GC_ALINHADO baseia-se em dados autodeclarados pelos gestores (Tabela X_6 dos informes mensais) e captura apenas uma dimensão da governança (alinhamento entre projeção e execução).
- Variáveis estruturais de governança (quóruns de assembleia, qualidade dos prestadores críticos, histórico de auditoria) não são capturadas, pois exigem análise documental de atas em PDF não estruturado.
- O modelo DiD não possui grupo de controle exógeno, pois a Resolução CVM nº 175/2022 incidiu simultaneamente sobre todos os FIDC.

## Citação

Se você utilizar este código ou pipeline em sua pesquisa, por favor cite:

```bibtex
@inproceedings{albuquerque2026fidc,
  author    = {Albuquerque, Jonas Chaves and Abreu, Emmanuel Sousa de},
  title     = {Governança Corporativa em Fundos de Investimento em Direitos
               Creditórios no Brasil: Volatilidade e a Resolução CVM
               nº 175/2022},
  booktitle = {Anais do XX Congresso ANPCONT},
  year      = {2026}
}
```

## Licença

Este código é distribuído sob a [Licença MIT](LICENSE). Os dados utilizados são públicos e disponibilizados pela Comissão de Valores Mobiliários (CVM) sob seus próprios termos.

## Contato

- **Jonas Chaves Albuquerque** — Universidade de Brasília (UnB)
- **Emmanuel Sousa de Abreu** — Universidade de Brasília (UnB)

Para dúvidas, abrir uma *issue* neste repositório.
