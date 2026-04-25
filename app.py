import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="RRHH PRO", layout="wide")

st.title("📊 Sistema Inteligente de Fichajes RRHH")

archivo = st.file_uploader("Sube el Excel de Sesame", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    # Normalizar columnas
    df["Entrada"] = pd.to_datetime(df["Entrada"])
    df["Salida"] = pd.to_datetime(df["Salida"])
    df["Fecha"] = pd.to_datetime(df["Fecha"])

    # Horas totales
    df["Horas_totales"] = (df["Salida"] - df["Entrada"]).dt.total_seconds() / 3600 - df["Pausa"]

    # Cálculo nocturnas
    def nocturnas(row):
        inicio = row["Entrada"]
        fin = row["Salida"]
        total = 0
        current = inicio
        while current < fin:
            if current.hour >= 22 or current.hour < 6:
                total += 1/60
            current += pd.Timedelta(minutes=1)
        return total

    df["Nocturnas"] = df.apply(nocturnas, axis=1)
    df["Diurnas"] = df["Horas_totales"] - df["Nocturnas"]

    # Sábados
    df["Sabado"] = df["Fecha"].dt.weekday == 5
    df["Horas_sabado"] = df.apply(lambda x: x["Horas_totales"] if x["Sabado"] else 0, axis=1)

    # Extras
    df["Extras"] = df["Horas_totales"].apply(lambda x: max(0, x - 8))

    # ALERTAS
    st.subheader("⚠️ Alertas")
    exceso = df[df["Horas_totales"] > 10]
    if not exceso.empty:
        st.warning(f"{len(exceso)} registros con más de 10h trabajadas")
        st.dataframe(exceso)

    # DASHBOARD
    st.subheader("📊 Dashboard")

    resumen = df.groupby("Empleado")[["Horas_totales", "Extras", "Nocturnas"]].sum().reset_index()

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(resumen, x="Empleado", y="Horas_totales", title="Horas totales por empleado")
        st.plotly_chart(fig)

    with col2:
        fig2 = px.bar(resumen, x="Empleado", y="Extras", title="Horas extra por empleado")
        st.plotly_chart(fig2)

    # DESCARGA
    st.subheader("📥 Exportar resultados")

    output = "reporte_rrhh_pro.xlsx"
    df.to_excel(output, index=False)

    with open(output, "rb") as f:
        st.download_button("Descargar Excel procesado", f, file_name=output)

    # INFORME RESUMEN
    st.subheader("🧾 Informe automático")

    total_horas = df["Horas_totales"].sum()
    total_extras = df["Extras"].sum()
    total_nocturnas = df["Nocturnas"].sum()

    st.write(f"Total horas trabajadas: {round(total_horas,2)}")
    st.write(f"Total horas extra: {round(total_extras,2)}")
    st.write(f"Total horas nocturnas: {round(total_nocturnas,2)}")
