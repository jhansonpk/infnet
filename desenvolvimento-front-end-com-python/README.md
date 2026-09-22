# TP2 - Desenvolvimento Front-End com Python (com Streamlit) [26E3_1]

**Aluno:** Andre Luis Martins do Nascimento Junior
**Matricula:** GRLBDD01C1-N2-L1
**Disciplina:** Desenvolvimento Front-End com Python (com Streamlit)

Dashboard em Streamlit com os 12 exercicios do TP, usando os dados reais de COVID-19 do portal Coronavirus Brasil (https://covid.saude.gov.br/), do Ministerio da Saude.

Todo o codigo-fonte esta no arquivo `app.py`, com cada exercicio identificado por um comentario.

## Dados

Os arquivos de dados nao estao no repositorio porque passam de 100 MB. Para rodar o projeto:

1. Acesse https://covid.saude.gov.br/ e clique no botao **Arquivo CSV**.
2. Descompacte o pacote. Voce vai ter varios arquivos `HIST_PAINEL_COVIDBR_*.csv`.
3. Coloque esses arquivos em uma pasta `dados` ao lado do `app.py` (o app tambem encontra os arquivos em qualquer subpasta).

Estrutura esperada:

```
TP2/
  app.py
  dados/
    HIST_PAINEL_COVIDBR_2020_Parte1_*.csv
    HIST_PAINEL_COVIDBR_2020_Parte2_*.csv
    ...
```

As coordenadas dos municipios usadas nos mapas nao existem no arquivo do portal, entao sao baixadas em tempo de execucao da base publica de municipios do IBGE (kelvins/municipios-brasileiros). Por isso o app precisa de internet na primeira carga.

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas matplotlib seaborn altair plotly pydeck
streamlit run app.py
```

O app abre em http://localhost:8501. A primeira carga demora um pouco porque o arquivo do portal tem alguns milhoes de linhas. Depois disso os dados ficam em cache.

## Exercicios

1. Importancia da visualizacao de dados (resposta em texto)
2. Grafico de barras com Streamlit - casos novos por semana no RJ
3. Grafico de linha com Streamlit - obitos acumulados no Brasil
4. Grafico de area com Streamlit - casos acumulados em SP, RJ e AM
5. Mapa com st.map - casos acumulados por municipio do RJ
6. Matplotlib - casos novos x obitos novos por estado na semana mais recente
7. Boxplot com Seaborn - casos novos por semana nas regioes Norte, Nordeste e Sudeste
8. Grafico de area com Altair - casos novos por semana no Nordeste
9. Heatmap com Altair - correlacao entre casos e obitos no RJ
10. Grafico de pizza com Plotly - casos acumulados por regiao
11. Subplots com Plotly - casos e obitos novos no Sudeste e no Norte
12. Mapa interativo com PyDeck - casos por 100 mil habitantes nos municipios do Sudeste

## Observacoes

- O arquivo do portal nao traz leitos hospitalares ocupados, entao o heatmap do exercicio 9 usa casos e obitos (novos e acumulados).
- O portal tambem nao traz a area dos municipios, entao no exercicio 12 os casos acumulados sao ajustados pela populacao (casos por 100 mil habitantes).
- A coluna `semanaEpi` reinicia a cada ano, por isso as semanas sao identificadas no formato `2021-SE07`, juntando o ano epidemiologico com o numero da semana.
