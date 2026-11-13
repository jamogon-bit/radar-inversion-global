import json
import os
import pandas as pd
import streamlit as st
from scanner import ejecutar_rastreo_global

st.set_page_config(page_title="Radar Global de Inversión", page_icon="🌍", layout="wide")

# Sufijos de bolsa para construir enlaces exactos en Yahoo! Finance
SUFIJOS_YAHOO = {
    "BME": ".MC",       # España (Madrid)
    "LSE": ".L",        # Reino Unido (Londres)
    "EURONEXT": ".PA",  # Francia / Europa
    "XETR": ".DE",      # Alemania
    "FWB": ".F",        # Fráncfort
    "SIX": ".SW",       # Suiza
    "TSE": ".T",        # Japón (Tokio)
    "KRX": ".KS",       # Corea del Sur
    "HKEX": ".HK",      # Hong Kong / China
}

def generar_url_yahoo(ticker: str, bolsa: str, pais: str) -> str:
    ticker_limpio = str(ticker).strip()
    bolsa_upper = str(bolsa).upper()

    # Ajuste específico para Ámsterdam vs París en Euronext
    if bolsa_upper == "EURONEXT" and pais == "Países Bajos":
        sufijo = ".AS"
    else:
        sufijo = SUFIJOS_YAHOO.get(bolsa_upper, "")

    # En Hong Kong Yahoo Finance usa 4 dígitos (ej. 0700.HK)
    if sufijo == ".HK" and ticker_limpio.isdigit():
        ticker_limpio = ticker_limpio.zfill(4)

    return f"https://finance.yahoo.com/quote/{ticker_limpio}{sufijo}"

st.title("🌍 Cazador Global de Valor y Dividendos (Top 5 por Región)")

if not os.path.exists("ranking_regiones.json"):
    with st.spinner("Ejecutando primer escaneo global..."):
        ejecutar_rastreo_global()

with open("ranking_regiones.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

col_info, col_btn = st.columns([4, 1])
with col_info:
    st.caption(
        f"⏱️ Último barrido automático: **{datos['ultima_actualizacion_utc']}** | "
        "Pulsa sobre cualquier empresa o enlace para ver su gráfico y balances en Yahoo! Finance"
    )
with col_btn:
    if st.button("🔄 Escanear ahora", use_container_width=True):
        with st.spinner("Actualizando mercados..."):
            ejecutar_rastreo_global()
            st.rerun()

st.divider()

# Tarjetas con la #1 de cada región (con enlace directo)
st.subheader("🎯 Líder Actual por Región")
cols = st.columns(3)
for idx, region in enumerate(["América", "Europa", "Asia"]):
    lista = datos["regiones"].get(region, [])
    with cols[idx]:
        if lista:
            top1 = lista[0]
            url_top1 = generar_url_yahoo(top1["Ticker"], top1["Bolsa"], top1["País"])
            st.metric(
                label=f"{region} — {top1['Empresa']} ({top1['Ticker']})",
                value=f"{top1['Precio']} {top1['Divisa']}",
                delta=f"Div: {top1['Div (%)']}% | PER: {top1['PER']}x",
            )
            st.markdown(f"📈 [Ver gráfico y cuentas de {top1['Ticker']} en Yahoo! Finance]({url_top1})")
            st.caption(f"📍 {top1['País']} ({top1['Bolsa']}) · ROE: {top1['ROE (%)']}% · Deuda: {top1['Deuda/Patrim.']}x")
        else:
            st.warning(f"Sin candidatas en {region} hoy")

st.divider()

# Pestañas detalladas con el Top 5 de cada región y columna clicable
tab_am, tab_eu, tab_as = st.tabs(["🇺🇸 América (Top 5)", "🇪🇺 Europa (Top 5)", "🇯🇵 Asia (Top 5)"])

for tab, region in zip([tab_am, tab_eu, tab_as], ["América", "Europa", "Asia"]):
    with tab:
        registros = datos["regiones"].get(region, [])
        if registros:
            df_reg = pd.DataFrame(registros)
            df_reg["Ficha Web"] = df_reg.apply(
                lambda r: generar_url_yahoo(r["Ticker"], r["Bolsa"], r["País"]), axis=1
            )

            # Reordenar para poner el enlace junto al nombre de la empresa
            columnas_ordenadas = ["Ficha Web"] + [c for c in df_reg.columns if c != "Ficha Web"]
            df_reg = df_reg[columnas_ordenadas]

            st.dataframe(
                df_reg,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ficha Web": st.column_config.LinkColumn(
                        "Análisis",
                        help="Abrir cotización, gráficos y estados financieros en Yahoo! Finance",
                        display_text="🔎 Ver ficha",
                    )
                },
            )
        else:
            st.info(f"Ninguna empresa en {region} cumple todos los filtros estrictos en esta sesión.")
