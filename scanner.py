import json
from datetime import datetime, timezone
import pandas as pd
from tradingview_screener import Query, Column

REGIONES = {
    "América": {"america": "EE.UU."},
    "Europa": {
        "spain": "España",
        "uk": "Reino Unido",
        "netherlands": "Países Bajos",
        "germany": "Alemania",
        "france": "Francia",
        "switzerland": "Suiza",
    },
    "Asia": {
        "japan": "Japón",
        "korea": "Corea del Sur",
        "hongkong": "Hong Kong / China",
    },
}

def rastrear_region(mercados: dict) -> list:
    bolsas = []
    for codigo, pais in mercados.items():
        try:
            _, df_m = (
                Query()
                .set_markets(codigo)
                .select(
                    "name", "description", "exchange", "sector", "close", "currency",
                    "market_cap_basic", "price_earnings_ttm", "return_on_equity",
                    "return_on_assets", "debt_to_equity", "dividends_yield_current",
                    "dividend_yield_recent", "dividend_payout_ratio_ttm"
                )
                .where(Column("type") == "stock")
                .order_by("market_cap_basic", ascending=False)
                .limit(250)
                .get_scanner_data()
            )
            if not df_m.empty:
                df_m["Pais"] = pais
                bolsas.append(df_m)
        except Exception as e:
            print(f"Aviso en {pais}: {e}")

    if not bolsas:
        return []

    df = pd.concat(bolsas, ignore_index=True)

    # Conversión numérica limpia
    div_actual = pd.to_numeric(df["dividends_yield_current"], errors="coerce")
    div_reciente = pd.to_numeric(df["dividend_yield_recent"], errors="coerce")
    df["Dividendo_%"] = div_actual.fillna(div_reciente)
    df["Deuda_Patrim"] = pd.to_numeric(df["debt_to_equity"], errors="coerce") / 100.0

    # Filtros fundamentales
    df = df[df["sector"] != "Finance"]
    df = df[df["Dividendo_%"].between(2.5, 9.0)]
    df = df[(df["return_on_equity"] > 12) & (df["return_on_assets"] > 6)]
    df = df[df["Deuda_Patrim"] < 1.0]
    df = df[df["price_earnings_ttm"].between(5, 20)]
    df = df[(df["dividend_payout_ratio_ttm"].isna()) | (df["dividend_payout_ratio_ttm"].between(10, 80))]

    # Priorizar divisas operables fácilmente en MyInvestor (USD/EUR/GBP) y eliminar duplicados
    df["prioridad_divisa"] = df["currency"].apply(lambda c: 0 if c in ["USD", "EUR", "GBP"] else 1)
    df = df.sort_values("prioridad_divisa").drop_duplicates(subset=["description"], keep="first")

    if df.empty:
        return []

    # Ranking relativo tipo Fórmula Mágica + Dividendo
    df["Score"] = (
        df["return_on_assets"].rank(ascending=False)
        + df["price_earnings_ttm"].rank(ascending=True)
        + df["Dividendo_%"].rank(ascending=False)
    )

    top_5 = df.sort_values("Score").head(5).copy()

    columnas = {
        "name": "Ticker",
        "description": "Empresa",
        "Pais": "País",
        "exchange": "Bolsa",
        "sector": "Sector",
        "close": "Precio",
        "currency": "Divisa",
        "price_earnings_ttm": "PER",
        "Dividendo_%": "Div (%)",
        "dividend_payout_ratio_ttm": "Pay-Out (%)",
        "return_on_equity": "ROE (%)",
        "return_on_assets": "ROA (%)",
        "Deuda_Patrim": "Deuda/Patrim.",
    }
    top_5 = top_5[list(columnas.keys())].rename(columns=columnas)
    return top_5.round(2).fillna("N/D").to_dict(orient="records")

def ejecutar_rastreo_global():
    salida = {
        "ultima_actualizacion_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "regiones": {}
    }
    for nombre_region, mercados in REGIONES.items():
        print(f"Rastreando {nombre_region}...")
        salida["regiones"][nombre_region] = rastrear_region(mercados)

    with open("ranking_regiones.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print("Actualización completada en ranking_regiones.json")

if __name__ == "__main__":
    ejecutar_rastreo_global()
