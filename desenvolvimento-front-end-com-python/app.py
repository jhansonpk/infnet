# TP2 - Desenvolvimento Front-End com Python (com Streamlit) [26E3_1]
# Aluno: Andre Luis Martins do Nascimento Junior
# Matricula: GRLBDD01C1-N2-L1
#
# Dados: portal Coronavirus Brasil (https://covid.saude.gov.br/), botao "Arquivo CSV".
# Descompactar os arquivos HIST_PAINEL_COVIDBR_*.csv dentro de uma pasta "dados" ao lado deste app.py
# (o app tambem acha os arquivos em qualquer subpasta).
#
# Para rodar:
#   pip install streamlit pandas matplotlib seaborn altair plotly pydeck
#   streamlit run app.py

import glob
import os

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import seaborn as sns
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(page_title="TP2 - COVID-19 no Brasil", layout="wide")


def fmt(n):
    return f"{n:,.0f}".replace(",", ".")


def pct(n):
    return f"{n:.1f}".replace(".", ",")


def semana_epi(df):
    # a semanaEpi reinicia todo ano, entao junto com o ano epidemiologico (ano da quarta-feira da semana)
    domingo = df["data"] - pd.to_timedelta((df["data"].dt.weekday + 1) % 7, unit="D")
    ano = (domingo + pd.Timedelta(days=3)).dt.year
    semana = pd.to_numeric(df["semanaEpi"], errors="coerce").fillna(0).astype(int)
    return ano.astype(str) + "-SE" + semana.astype(str).str.zfill(2)


def achar_arquivos():
    # procura os CSVs do portal na pasta do app e em qualquer subpasta (o zip costuma criar uma pasta propria)
    arquivos = glob.glob("**/HIST_PAINEL_COVIDBR*.csv", recursive=True)
    arquivos += glob.glob("**/HIST_PAINEL_COVIDBR*.CSV", recursive=True)
    return sorted(set(arquivos))


def ler_csv(caminho, colunas):
    # os arquivos do portal as vezes vem em utf-8 e as vezes em latin-1
    try:
        return pd.read_csv(caminho, sep=";", usecols=colunas)
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=";", usecols=colunas, encoding="latin-1")


def por_semana(df, grupo):
    # soma os casos/obitos novos da semana e pega o ultimo acumulado da semana
    df = df.sort_values("data")
    novos = df.groupby(grupo + ["semana"])[["casosNovos", "obitosNovos"]].sum()
    acum = df.groupby(grupo + ["semana"])[["data", "casosAcumulado", "obitosAcumulado"]].last()
    return novos.join(acum).reset_index()


@st.cache_data
def carregar_dados():
    colunas = ["regiao", "estado", "municipio", "codmun", "data", "semanaEpi", "populacaoTCU2019",
               "casosAcumulado", "casosNovos", "obitosAcumulado", "obitosNovos"]
    df = pd.concat([ler_csv(a, colunas) for a in achar_arquivos()], ignore_index=True)

    df["data"] = pd.to_datetime(df["data"])
    for c in ["codmun", "populacaoTCU2019", "casosAcumulado", "casosNovos", "obitosAcumulado", "obitosNovos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    brasil = df[df["regiao"] == "Brasil"].copy()
    estados = df[(df["regiao"] != "Brasil") & df["estado"].notna() & df["codmun"].isna()].copy()
    municipios = df[df["codmun"].notna() & df["municipio"].notna()]

    brasil["semana"] = semana_epi(brasil)
    estados["semana"] = semana_epi(estados)

    sem_brasil = por_semana(brasil, [])
    sem_estados = por_semana(estados, ["regiao", "estado"])

    # ultima posicao de cada municipio (casos acumulados)
    mun = municipios.sort_values("data").drop_duplicates("codmun", keep="last")
    mun = mun[["regiao", "estado", "municipio", "codmun", "populacaoTCU2019", "casosAcumulado", "obitosAcumulado"]]
    mun["codmun"] = mun["codmun"].astype(int)

    return sem_brasil, sem_estados, mun


@st.cache_data
def carregar_coordenadas():
    # o arquivo do portal nao tem latitude/longitude, entao uso a base de municipios do IBGE (kelvins/municipios-brasileiros)
    url = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
    coord = pd.read_csv(url)
    coord["codmun"] = coord["codigo_ibge"] // 10  # no portal o codigo do municipio tem 6 digitos
    return coord[["codmun", "latitude", "longitude"]]


st.title("TP2 - Desenvolvimento Front-End com Python (com Streamlit)")
st.markdown("**Aluno:** Andre Luis Martins do Nascimento Junior  \n**Matricula:** GRLBDD01C1-N2-L1")
st.caption("Fonte dos dados: portal Coronavírus Brasil (https://covid.saude.gov.br/), Ministério da Saúde.")

arquivos = achar_arquivos()
if not arquivos:
    st.error("Nao encontrei nenhum arquivo HIST_PAINEL_COVIDBR_*.csv. "
             "Baixe o arquivo CSV no portal e descompacte na pasta dados, ao lado do app.py.")
    st.write("Pasta atual:", os.getcwd())
    st.write("O que tem nela:", sorted(os.listdir(".")))
    st.stop()

sem_brasil, sem_estados, mun = carregar_dados()
coord = carregar_coordenadas()

# total por regiao em cada semana (soma dos estados)
sem_regioes = sem_estados.groupby(["regiao", "semana"], as_index=False).agg(
    {"data": "max", "casosNovos": "sum", "obitosNovos": "sum", "casosAcumulado": "sum", "obitosAcumulado": "sum"})

st.write(f"Dados até {sem_brasil['data'].max():%d/%m/%Y}.")


# ============================================================
# Exercicio 1 - Importancia da Visualizacao de Dados
# ============================================================
st.header("1. Importância da Visualização de Dados")
st.markdown("Explique a importância da visualização de dados no contexto de uma pandemia como a COVID-19. "
            "Como essas visualizações podem ajudar gestores de saúde pública e a população em geral a tomar decisões informadas?")
st.write("Numa pandemia os dados chegam todo dia e em volume muito grande, e o gráfico mostra rápido o que uma tabela "
         "esconde: se a curva está subindo, onde estão os focos e quando começa uma nova onda. Para os gestores isso ajuda "
         "a decidir onde abrir leitos, mandar vacinas e aplicar restrições. Para a população, visualizações simples deixam "
         "o risco mais claro e ajudam a entender por que seguir as medidas de proteção.")


# ============================================================
# Exercicio 2 - Grafico de Barras com Streamlit
# ============================================================
st.header("2. Gráfico de Barras com Streamlit")
st.markdown("Usando os dados de casos novos de COVID-19 por semana epidemiológica de notificação, crie um gráfico de barras "
            "em Streamlit que mostre a evolução semanal dos casos em um determinado estado. Indique o estado escolhido e explique sua escolha.")

rj = sem_estados[sem_estados["estado"] == "RJ"]
st.bar_chart(rj.set_index("semana")["casosNovos"], x_label="Semana epidemiológica", y_label="Casos novos")
st.write("Estado escolhido: Rio de Janeiro. Escolhi o RJ porque é o estado onde moro e porque foi um dos mais atingidos "
         "do país, com várias ondas bem marcadas ao longo das semanas.")


# ============================================================
# Exercicio 3 - Grafico de Linha com Streamlit
# ============================================================
st.header("3. Gráfico de Linha com Streamlit")
st.markdown("Crie um gráfico de linha utilizando Streamlit para representar o número de óbitos acumulados por COVID-19 ao longo "
            "das semanas epidemiológicas de notificação para todo o Brasil. Explique como a curva de óbitos acumulados pode ser interpretada.")

st.line_chart(sem_brasil.set_index("semana")["obitosAcumulado"], x_label="Semana epidemiológica", y_label="Óbitos acumulados")
st.write(f"A curva nunca desce, só cresce ou fica estável, e termina em {fmt(sem_brasil['obitosAcumulado'].iloc[-1])} óbitos. "
         "O que importa é a inclinação: trechos mais íngremes são as fases com mais mortes por semana (as ondas mais graves), "
         "e quando a curva vai ficando mais plana significa que as mortes diminuíram, o que coincide com o avanço da vacinação.")


# ============================================================
# Exercicio 4 - Grafico de Area com Streamlit
# ============================================================
st.header("4. Gráfico de Área com Streamlit")
st.markdown("Utilizando os dados de casos acumulados por COVID-19, crie um gráfico de área em Streamlit para comparar a "
            "evolução dos casos em três estados diferentes. Explique as diferenças observadas entre os estados escolhidos.")

tres = sem_estados[sem_estados["estado"].isin(["SP", "RJ", "AM"])]
tabela = tres.pivot_table(index="semana", columns="estado", values="casosAcumulado")
st.area_chart(tabela, stack=False, x_label="Semana epidemiológica", y_label="Casos acumulados")

final = tres.sort_values("data").groupby("estado")["casosAcumulado"].last()
st.write(f"Escolhi SP, RJ e AM. SP fica muito acima dos outros ({fmt(final['SP'])} casos) por ter a maior população do país, "
         f"o RJ fica no meio ({fmt(final['RJ'])}) e o AM tem o menor número absoluto ({fmt(final['AM'])}). "
         "Mesmo menor, o AM teve subidas fortes já no primeiro semestre de 2020 e na virada de 2020 para 2021, quando o sistema de saúde de Manaus entrou em colapso.")


# ============================================================
# Exercicio 5 - Mapa com Streamlit
# ============================================================
st.header("5. Mapa com Streamlit")
st.markdown("Crie um mapa interativo utilizando a função st.map do Streamlit que mostre a distribuição dos casos acumulados "
            "de COVID-19 por município em um estado específico. Explique como esse tipo de visualização pode ajudar na análise geográfica da pandemia.")

mapa_rj = mun[mun["estado"] == "RJ"].merge(coord, on="codmun")
mapa_rj["tamanho"] = mapa_rj["casosAcumulado"] / mapa_rj["casosAcumulado"].max() * 15000 + 500
st.map(mapa_rj, latitude="latitude", longitude="longitude", size="tamanho", zoom=6)
st.write("O mapa mostra os casos acumulados por município do RJ (quanto maior o círculo, mais casos). Dá pra ver que os casos "
         "se concentram na capital e na região metropolitana. Esse tipo de mapa ajuda a achar os focos, ver como a doença se "
         "espalha para cidades vizinhas e decidir onde reforçar a estrutura de saúde.")


# ============================================================
# Exercicio 6 - Visualizacao com Matplotlib
# ============================================================
st.header("6. Visualização com Matplotlib")
st.markdown("Utilize a biblioteca Matplotlib para criar um gráfico de barras que mostre a comparação entre os casos novos e os "
            "óbitos novos de COVID-19 por estado na semana epidemiológica mais recente disponível. Explique o que os dados sugerem sobre a relação entre casos e óbitos.")

# as ultimas semanas do arquivo podem vir sem notificacao nenhuma, entao pego a semana mais recente com casos
ultima = sem_estados[sem_estados["casosNovos"] > 0]["semana"].max()
semana_atual = sem_estados[sem_estados["semana"] == ultima].sort_values("casosNovos", ascending=False)

fig, ax = plt.subplots(figsize=(12, 5))
x = np.arange(len(semana_atual))
ax.bar(x - 0.2, semana_atual["casosNovos"], width=0.4, label="Casos novos")
ax.bar(x + 0.2, semana_atual["obitosNovos"], width=0.4, label="Óbitos novos")
ax.set_xticks(x)
ax.set_xticklabels(semana_atual["estado"])
ax.set_yscale("log")
ax.set_ylabel("Quantidade (escala log)")
ax.set_title(f"Casos novos x óbitos novos por estado - semana {ultima}")
ax.legend()
st.pyplot(fig)

taxa = semana_atual["obitosNovos"].sum() / semana_atual["casosNovos"].sum() * 100
st.write(f"Usei escala logarítmica porque os óbitos são bem menores que os casos. A semana {ultima} é a mais recente com "
         f"notificações no arquivo, e nela foram "
         f"{fmt(semana_atual['casosNovos'].sum())} casos e {fmt(semana_atual['obitosNovos'].sum())} óbitos (cerca de {pct(taxa)}%). "
         "Os estados com mais casos em geral também têm mais óbitos, mas a proporção é bem menor que no início da pandemia, "
         "o que sugere o efeito da vacinação. Também tem que lembrar que os óbitos vêm com atraso em relação aos casos.")


# ============================================================
# Exercicio 7 - Boxplot com Seaborn
# ============================================================
st.header("7. Boxplot com Seaborn")
st.markdown("Usando a biblioteca Seaborn, crie um boxplot que compare a distribuição dos casos novos de COVID-19 por semana "
            "epidemiológica entre três regiões do Brasil (Norte, Nordeste, Sudeste). Explique as principais diferenças observadas.")

tres_reg = sem_regioes[sem_regioes["regiao"].isin(["Norte", "Nordeste", "Sudeste"])]
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=tres_reg, x="regiao", y="casosNovos", order=["Norte", "Nordeste", "Sudeste"], ax=ax)
ax.set_xlabel("Região")
ax.set_ylabel("Casos novos por semana")
st.pyplot(fig)

med = tres_reg.groupby("regiao")["casosNovos"].median()
st.write(f"O Sudeste tem a maior mediana ({fmt(med['Sudeste'])} casos por semana) e a maior dispersão, seguido do Nordeste "
         f"({fmt(med['Nordeste'])}) e do Norte ({fmt(med['Norte'])}), o que acompanha o tamanho da população de cada região. "
         "Nas três aparecem muitos outliers acima da caixa, que são as semanas de pico das ondas, principalmente a da Ômicron no começo de 2022.")


# ============================================================
# Exercicio 8 - Grafico de Area com Altair
# ============================================================
st.header("8. Gráfico de Área com Altair")
st.markdown("Crie um gráfico de área em Altair para mostrar a evolução dos casos novos de COVID-19 por semana epidemiológica "
            "de notificação em uma determinada região do Brasil. Explique a escolha da região e as tendências observadas nos dados.")

nordeste = sem_regioes[sem_regioes["regiao"] == "Nordeste"]
grafico = alt.Chart(nordeste).mark_area(opacity=0.7).encode(
    x=alt.X("data:T", title="Semana epidemiológica"),
    y=alt.Y("casosNovos:Q", title="Casos novos"),
    tooltip=["semana", "casosNovos"],
).properties(height=400)
st.altair_chart(grafico, width="stretch")

pico = nordeste.loc[nordeste["casosNovos"].idxmax()]
st.write("Escolhi o Nordeste por ser a segunda região mais populosa e ter nove estados, então mostra bem o comportamento fora "
         f"do Sudeste. A curva tem várias ondas, com o maior pico na semana {pico['semana']} ({fmt(pico['casosNovos'])} casos). "
         "Depois dos grandes picos os casos caem bastante e as ondas seguintes ficam menores.")


# ============================================================
# Exercicio 9 - Heatmap com Altair
# ============================================================
st.header("9. Heatmap com Altair")
st.markdown("Desenvolva um heatmap em Altair que mostre a correlação entre casos novos, óbitos novos e leitos hospitalares "
            "ocupados (caso os dados estejam disponíveis) em um determinado estado. Explique as possíveis correlações observadas.")

corr = rj[["casosNovos", "obitosNovos", "casosAcumulado", "obitosAcumulado"]].corr()
corr_long = corr.reset_index().melt(id_vars="index")
corr_long.columns = ["var1", "var2", "correlacao"]

base = alt.Chart(corr_long).encode(x=alt.X("var1:N", title=""), y=alt.Y("var2:N", title=""))
heatmap = base.mark_rect().encode(color=alt.Color("correlacao:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 1])))
texto = base.mark_text().encode(text=alt.Text("correlacao:Q", format=".2f"))
st.altair_chart((heatmap + texto).properties(height=350, title="Correlação semanal - RJ"), width="stretch")

st.write("O arquivo do portal não tem dados de leitos ocupados, então usei casos e óbitos (novos e acumulados) do RJ por semana. "
         f"Casos novos e óbitos novos têm correlação de {str(round(corr.loc['casosNovos', 'obitosNovos'], 2)).replace('.', ',')}: quando os casos sobem os óbitos "
         "costumam subir junto, só que com atraso e com a relação mudando depois da vacinação. Os acumulados são quase perfeitamente "
         "correlacionados entre si porque os dois só crescem com o tempo.")


# ============================================================
# Exercicio 10 - Grafico de Pizza com Plotly
# ============================================================
st.header("10. Gráfico de Pizza com Plotly")
st.markdown("Usando Plotly, crie um gráfico de pizza (pie chart) que mostre a distribuição percentual dos casos acumulados de "
            "COVID-19 entre as cinco regiões do Brasil. Explique o que os dados revelam sobre a distribuição geográfica dos casos.")

ultimo_estado = sem_estados.sort_values("data").groupby(["regiao", "estado"], as_index=False).last()
pizza = ultimo_estado.groupby("regiao", as_index=False)["casosAcumulado"].sum()
fig = px.pie(pizza, names="regiao", values="casosAcumulado", title="Casos acumulados por região")
st.plotly_chart(fig, width="stretch")

pizza["perc"] = pizza["casosAcumulado"] / pizza["casosAcumulado"].sum() * 100
maior = pizza.loc[pizza["perc"].idxmax()]
menor = pizza.loc[pizza["perc"].idxmin()]
st.write(f"O {maior['regiao']} concentra a maior parte dos casos ({pct(maior['perc'])}%) e o {menor['regiao']} a menor ({pct(menor['perc'])}%). "
         "A distribuição acompanha basicamente o tamanho da população de cada região, então para comparar o risco de verdade "
         "o ideal seria olhar os casos por habitante.")


# ============================================================
# Exercicio 11 - Subplots com Plotly
# ============================================================
st.header("11. Subplots com Plotly")
st.markdown("Crie subplots em Plotly que mostrem, lado a lado, gráficos de barras comparando os casos novos e os óbitos novos "
            "de COVID-19 por semana epidemiológica em duas diferentes regiões do Brasil. Explique as diferenças observadas entre as regiões.")

sudeste = sem_regioes[sem_regioes["regiao"] == "Sudeste"]
norte = sem_regioes[sem_regioes["regiao"] == "Norte"]

fig = make_subplots(rows=2, cols=2, shared_xaxes=True,
                    subplot_titles=["Sudeste - casos novos", "Norte - casos novos", "Sudeste - óbitos novos", "Norte - óbitos novos"])
fig.add_trace(go.Bar(x=sudeste["data"], y=sudeste["casosNovos"], name="Casos Sudeste"), row=1, col=1)
fig.add_trace(go.Bar(x=norte["data"], y=norte["casosNovos"], name="Casos Norte"), row=1, col=2)
fig.add_trace(go.Bar(x=sudeste["data"], y=sudeste["obitosNovos"], name="Óbitos Sudeste"), row=2, col=1)
fig.add_trace(go.Bar(x=norte["data"], y=norte["obitosNovos"], name="Óbitos Norte"), row=2, col=2)
fig.update_layout(height=600, showlegend=False)
st.plotly_chart(fig, width="stretch")

let_se = sudeste["obitosNovos"].sum() / sudeste["casosNovos"].sum() * 100
let_no = norte["obitosNovos"].sum() / norte["casosNovos"].sum() * 100
st.write("Coloquei casos em cima e óbitos embaixo para os óbitos não sumirem perto dos casos. O Sudeste tem números "
         "absolutos muito maiores por causa da população, mas as ondas aparecem nas duas regiões mais ou menos nas mesmas épocas. "
         "O Norte teve picos fortes mais cedo, por volta de maio de 2020 e na virada para 2021 (Manaus). "
         f"A letalidade no período ficou em {pct(let_se)}% no Sudeste e {pct(let_no)}% no Norte.")


# ============================================================
# Exercicio 12 - Mapa Interativo com PyDeck
# ============================================================
st.header("12. Mapa Interativo com PyDeck")
st.markdown("Utilize PyDeck para criar um mapa interativo que mostre a densidade populacional ajustada para os casos acumulados "
            "de COVID-19 por município em uma determinada região do Brasil. Explique como a densidade populacional pode influenciar a disseminação da COVID-19.")

se = mun[(mun["regiao"] == "Sudeste") & (mun["populacaoTCU2019"] > 0)].merge(coord, on="codmun")
se["casos_100mil"] = (se["casosAcumulado"] / se["populacaoTCU2019"] * 100000).round()
se["cor"] = (se["casos_100mil"] / se["casos_100mil"].max() * 255).astype(int)

camada = pdk.Layer(
    "ColumnLayer",
    data=se,
    get_position=["longitude", "latitude"],
    get_elevation="casos_100mil",
    elevation_scale=2,
    radius=4000,
    get_fill_color="[cor, 60, 255 - cor, 180]",
    pickable=True,
)
vista = pdk.ViewState(latitude=-20.5, longitude=-45, zoom=5, pitch=45)
st.pydeck_chart(pdk.Deck(layers=[camada], initial_view_state=vista,
                         tooltip={"text": "{municipio} ({estado})\nCasos por 100 mil hab: {casos_100mil}"}))

st.write("Região escolhida: Sudeste. Como o portal não tem a área dos municípios, ajustei os casos acumulados pela população "
         "(casos por 100 mil habitantes), assim cidade grande e cidade pequena podem ser comparadas. Em lugares com mais gente por "
         "área, como capitais e regiões metropolitanas, há mais contato entre pessoas, transporte público cheio e circulação intensa, "
         "o que facilita a transmissão. Mesmo assim, o mapa mostra que várias cidades do interior também tiveram taxas altas.")
