import streamlit as st
import pandas as pd
import altair as alt
import io
from PIL import Image
from fpdf import FPDF

st.set_page_config(page_title="Stromtarif-Rechner", layout="centered")

# Logo anzeigen
logo = Image.open("logo.png")
st.sidebar.image(logo, use_container_width=True)

# Begrüßung in der Seitenleiste
st.sidebar.title("💡 Willkommen!")
st.sidebar.markdown("**Familie Mestaje hilft euch, den günstigsten Stromtarif zu bekommen.**")

st.title("🔌 Stromtarif-Vergleichsrechner")

col1, col2 = st.columns(2)
with col1:
    verbrauch_kwh = st.number_input("🔋 Jahresverbrauch (kWh)", min_value=0, step=100)

    optionen = {
        "Jährlich (1)": 1,
        "Halbjährlich (2)": 2,
        "Vierteljährlich (4)": 4,
        "Alle 2 Monate (6)": 6,
        "Monatlich mit Abschlag (11)": 11,
        "Monatlich (12)": 12,
        "Monatlich + Jahresabschluss (13)": 13
    }
    auswahl = st.selectbox("📅 Abschläge pro Jahr", list(optionen.keys()), index=5)
    anzahl_abschlaege = optionen[auswahl]

with col2:
    abschlagszahlung = st.number_input("💶 Monatliche Abschlagszahlung (€)", min_value=0.0, format="%.2f")
    anzahl_tarife = st.slider("📦 Anzahl Tarife", 1, 10, 3)

tarife = []
st.markdown("## 🧾 Tarifdetails")
for i in range(1, anzahl_tarife + 1):
    with st.expander(f"Tarif {i}"):
        name = st.text_input(f"Name für Tarif {i}", value=f"Tarif {i}", key=f"name{i}")
        ap = st.number_input("Arbeitspreis (ct/kWh)", min_value=0.0, format="%.2f", key=f"ap{i}")
        gp = st.number_input("Grundpreis (€/Jahr)", min_value=0.0, format="%.2f", key=f"gp{i}")
        tarife.append({
            "Tarif": name,
            "Arbeitspreis (ct/kWh)": ap,
            "Grundpreis (€)": gp
        })

if st.button("🔍 Vergleich starten"):
    daten = []
    gezahlt = abschlagszahlung * anzahl_abschlaege

    for tarif in tarife:
        ap_euro = tarif["Arbeitspreis (ct/kWh)"] / 100
        kosten = ap_euro * verbrauch_kwh + tarif["Grundpreis (€)"]
        differenz = round(gezahlt - kosten, 2)
        ideal = round(kosten / anzahl_abschlaege, 2)
        daten.append({
            "Tarif": tarif["Tarif"],
            "Gesamtkosten (€)": round(kosten, 2),
            "Gezahlt (€)": round(gezahlt, 2),
            "Differenz (€)": differenz,
            "Idealer Abschlag (€)": ideal
        })

    df = pd.DataFrame(daten)
    st.success("✅ Vergleich abgeschlossen")
    st.dataframe(df, use_container_width=True)

    günstigster = df.loc[df["Gesamtkosten (€)"].idxmin()]
    st.info(f"🏆 Günstigster Tarif: **{günstigster['Tarif']}** mit **{günstigster['Gesamtkosten (€)']:.2f} €**")

    chart = alt.Chart(df).mark_bar().encode(
        x='Tarif',
        y='Gesamtkosten (€)',
        color=alt.condition(
            alt.datum['Tarif'] == günstigster['Tarif'],
            alt.value('green'), alt.value('gray')
        )
    ).properties(title="📊 Jahreskosten je Tarif", width=500)

    st.altair_chart(chart, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 CSV herunterladen", csv, "tarifvergleich.csv", "text/csv")

    def generate_pdf(dataframe):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Stromtarif-Vergleich", ln=True, align='C')
        pdf.ln(10)

        def clean(t):
            return str(t).replace("€", "EUR").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")

        for _, row in dataframe.iterrows():
            pdf.cell(200, 10, txt=clean(row['Tarif']), ln=True)
            pdf.cell(200, 10, txt=f"  Gesamtkosten: {clean(row['Gesamtkosten (€)'])} EUR", ln=True)
            pdf.cell(200, 10, txt=f"  Gezahlt: {clean(row['Gezahlt (€)'])} EUR", ln=True)
            pdf.cell(200, 10, txt=f"  Differenz: {clean(row['Differenz (€)'])} EUR", ln=True)
            pdf.cell(200, 10, txt=f"  Idealer Abschlag: {clean(row['Idealer Abschlag (€)'])} EUR", ln=True)
            pdf.ln(5)

        return pdf.output(dest='S').encode('latin1')

    pdf_bytes = generate_pdf(df)
    st.download_button("📄 PDF herunterladen", pdf_bytes, "tarifvergleich.pdf", "application/pdf")

st.markdown("---")
st.markdown("🔗 [Check24](https://www.check24.de/gas/) | [Verivox](https://www.verivox.de/gas/)")