import json
import os
import pandas as pd
import streamlit as st
from scanner import ejecutar_rastreo_global

st.set_page_config(page_title="Radar Global de Inversión", page_icon="🌍", layout="wide")

st.title("🌍 Cazador Global de Valor y Dividendos (Top 5 por Región)")

# Si aún no existe el archivo JSON, ejecutar primera carga
if not os.path.exists("ranking_regiones.json"):
    with st.spinner("Ejecutando primer escaneo global..."):
        ejecutar_rastreo_global()

with open("ranking_regiones.json", "r", encoding="utf-8") as f:
    datos = json.load(f)

col_info, col_btn = st.columns([4, 1])
with col_info:
    st.caption(f"⏱️ Último barrido automático: **{datos['ultima_actualizacion_utc']}** | Criterios: ROE > 12%, ROA > 6%, Deuda/Patrim < 1x, PER 5-20x, Dividendo 2.5%-9%")
with col_btn:
    if st.button("🔄 Escanear ahora", use_container_width=True):
        with st.spinner("Actualizando mercados..."):
            ejecutar_rastreo_global()
            st.rerun()

st.divider()

# Tarjetas con la #1 de cada región
st.subheader("🎯 Líder Actual por Región")
cols = st.columns(3)
for idx, region in enumerate(["América", "Europa", "Asia"]):
    lista = datos["regiones"].get(region, [])
    with cols[idx]:
        if lista:
            top1 = lista[0]
            st.metric(
                label=f"{region} — {top1['Empresa']} ({top1['Ticker']})",
                value=f"{top1['Precio']} {top1['Divisa']}",
                delta=f"Div: {top1['Div (%)']}% | PER: {top1['PER']}x"
            )
            st.caption(f"📍 {top1['País']} ({top1['Bolsa']}) · ROE: {top1['ROE (%)']}% · Deuda: {top1['Deuda/Patrim.']}x")
        else:
            st.warning(f"Sin candidatas en {region} hoy")

st.divider()

# Pestañas detalladas con el Top 5 de cada región
tab_am, tab_eu, tab_as = st.tabs(["🇺🇸 América (Top 5)", "🇪🇺 Europa (Top 5)", "🇯🇵 Asia (Top 5)"])

for tab, region in zip([tab_am, tab_eu, tab_as], ["América", "Europa", "Asia"]):
    with tab:
        registros = datos["regiones"].get(region, [])
        if registros:
            df_reg = pd.DataFrame(registros)
            st.dataframe(df_reg, use_container_width=True, hide_index=True)
        else:
            st.info(f"Ninguna empresa en {region} cumple todos los filtros estrictos en esta sesión.")
