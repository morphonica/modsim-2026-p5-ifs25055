import streamlit as st
import random
import plotly.express as px
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard Proyek FITE", layout="wide")

st.title("🏗️ Dashboard Simulasi Proyek Gedung FITE")

# =========================
# DATA PROYEK
# =========================
tasks = {
    "Persiapan": (1, 2, 3),
    "Pondasi": (2, 3, 5),
    "Struktur": (4, 6, 9),
    "Instalasi": (3, 5, 7),
    "Finishing": (2, 4, 6)
}

# Dependency (alur proyek)
dependencies = {
    "Persiapan": [],
    "Pondasi": ["Persiapan"],
    "Struktur": ["Pondasi"],
    "Instalasi": ["Struktur"],
    "Finishing": ["Instalasi"]
}

# =========================
# SIDEBAR (RISIKO)
# =========================
st.sidebar.header("⚠️ Risiko")

weather = st.sidebar.slider("Cuaca Buruk", 0.0, 0.5, 0.1)
material = st.sidebar.slider("Keterlambatan Material", 0.0, 0.5, 0.1)
design = st.sidebar.slider("Perubahan Desain", 0.0, 0.5, 0.1)
productivity = st.sidebar.slider("Produktivitas Pekerja", 0.0, 0.5, 0.1)

# =========================
# SIDEBAR (RESOURCE)
# =========================
st.sidebar.header("⚙️ Resource")

worker = st.sidebar.slider("Tambahan Pekerja", 0.5, 1.0, 1.0)
machine = st.sidebar.slider("Alat Berat", 0.5, 1.0, 1.0)
engineer = st.sidebar.slider("Insinyur", 0.5, 1.0, 1.0)

# =========================
# PARAMETER
# =========================
simulasi = st.sidebar.slider("Jumlah Simulasi", 1000, 10000, 3000)

# =========================
# FUNGSI PERT
# =========================
def pert(a, m, b):
    return (a + 4*m + b) / 6

# =========================
# CPM (CRITICAL PATH)
# =========================
def critical_path(tasks, dependencies):
    duration = {k: pert(a,m,b) for k,(a,m,b) in tasks.items()}

    ES, EF = {}, {}

    # Forward pass
    for task in dependencies:
        if not dependencies[task]:
            ES[task] = 0
        else:
            ES[task] = max(EF[d] for d in dependencies[task])
        EF[task] = ES[task] + duration[task]

    total_time = max(EF.values())

    LF, LS = {}, {}

    for task in reversed(list(dependencies.keys())):
        if task not in [d for deps in dependencies.values() for d in deps]:
            LF[task] = total_time
        else:
            LF[task] = min(LS[s] for s in dependencies if task in dependencies[s])
        LS[task] = LF[task] - duration[task]

    slack = {t: LS[t] - ES[t] for t in tasks}

    critical = [t for t in tasks if abs(slack[t]) < 1e-5]

    return critical, total_time, duration, ES, EF

# =========================
# MONTE CARLO
# =========================
def monte_carlo(tasks, n):
    results = []
    risk_log = {"Cuaca":0, "Material":0, "Desain":0, "Produktivitas":0}

    for _ in range(n):
        total = 0
        for a, m, b in tasks.values():
            d = random.triangular(a, b, m)

            # Risiko
            if random.random() < weather:
                d *= 1.2
                risk_log["Cuaca"] += 1

            if random.random() < material:
                d *= 1.25
                risk_log["Material"] += 1

            if random.random() < design:
                d *= 1.3
                risk_log["Desain"] += 1

            if random.random() < productivity:
                d *= 1.15
                risk_log["Produktivitas"] += 1

            # Resource mempercepat
            d *= worker * machine * engineer

            total += d

        results.append(total)

    return results, risk_log

# =========================
# PROBABILITAS DEADLINE
# =========================
def probability(results, deadline):
    return sum(r <= deadline for r in results) / len(results)

# =========================
# RUN
# =========================
results, risk_log = monte_carlo(tasks, simulasi)

avg = sum(results)/len(results)

prob16 = probability(results, 16)
prob20 = probability(results, 20)
prob24 = probability(results, 24)

# =========================
# CPM
# =========================
critical_tasks, total_time, duration, ES, EF = critical_path(tasks, dependencies)

# =========================
# METRICS
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("Rata-rata Durasi", f"{avg:.2f} bulan")
c2.metric("Total Waktu (CPM)", f"{total_time:.2f} bulan")
c3.metric("Simulasi", simulasi)

# =========================
# PROBABILITAS
# =========================
st.subheader("🎯 Probabilitas Deadline")

d1, d2, d3 = st.columns(3)
d1.metric("16 bulan", f"{prob16*100:.2f}%")
d2.metric("20 bulan", f"{prob20*100:.2f}%")
d3.metric("24 bulan", f"{prob24*100:.2f}%")

# =========================
# GRAFIK DISTRIBUSI
# =========================
st.subheader("📊 Distribusi Durasi Proyek")

df = pd.DataFrame({"Durasi": results})
fig = px.histogram(df, x="Durasi", nbins=40)
st.plotly_chart(fig, use_container_width=True)

# =========================
# ANALISIS RISIKO
# =========================
st.subheader("⚠️ Analisis Risiko")

risk_df = pd.DataFrame({
    "Faktor": list(risk_log.keys()),
    "Frekuensi": list(risk_log.values())
})

fig2 = px.bar(risk_df, x="Faktor", y="Frekuensi")
st.plotly_chart(fig2, use_container_width=True)

dominant = max(risk_log, key=risk_log.get)
st.write(f"Risiko paling dominan: **{dominant}**")

# =========================
# CRITICAL PATH
# =========================
st.subheader("🧠 Critical Path")

st.success(" ➝ ".join(critical_tasks))

df_cp = pd.DataFrame({
    "Task": list(tasks.keys()),
    "Durasi": [duration[t] for t in tasks],
    "ES": [ES[t] for t in tasks],
    "EF": [EF[t] for t in tasks]
})

st.dataframe(df_cp)

# =========================
# INTERPRETASI
# =========================
st.subheader("📌 Interpretasi")

if avg < 20:
    st.success("Proyek cenderung selesai tepat waktu.")
elif avg < 30:
    st.warning("Proyek memiliki risiko keterlambatan sedang.")
else:
    st.error("Proyek berisiko tinggi terlambat.")