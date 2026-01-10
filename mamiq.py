import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go

# =====================================================
# 1. DATABASE KOMPONEN LENGKAP
# =====================================================
# Database Panel Surya
DB_PANEL = {
    "Monocrystalline 550 Wp (Tier 1 - Project Grade)": {"wp": 550, "harga": 2100000},
    "Bifacial 600 Wp (Premium - 2 Sisi)": {"wp": 600, "harga": 2800000},
    "Monocrystalline 450 Wp (Standar Rumah)": {"wp": 450, "harga": 1750000},
    "Polycrystalline 330 Wp (Budget)": {"wp": 330, "harga": 1300000},
}

# Database Baterai
DB_BATTERY = {
    "Lithium LiFePO4 48V 100Ah (Rack Server - Awet)": {"volt": 48, "ah": 100, "dod": 80, "harga": 14500000},
    "Lithium Pack 12V 100Ah (Residential)": {"volt": 12, "ah": 100, "dod": 80, "harga": 3500000},
    "Lithium High Volt 10kWh (All-in-One Industrial)": {"volt": 200, "ah": 50, "dod": 90, "harga": 65000000},
    "VRLA Gel 12V 200Ah (Deep Cycle)": {"volt": 12, "ah": 200, "dod": 50, "harga": 4200000},
    "OpzV Tubular 2V 1000Ah (Tower Industrial)": {"volt": 2, "ah": 1000, "dod": 60, "harga": 7500000},
}

# Database Inverter (DITAMBAH OPSI OFF-GRID)
DB_INVERTER = {
    # 1 Phase (Rumah/Ruko Kecil)
    "Hybrid 5kW (1 Phase) - Residential": {"watt": 5000, "phase": 1, "type": "Hybrid", "harga": 9500000},
    "On-Grid 5kW (1 Phase) - Residential": {"watt": 5000, "phase": 1, "type": "On-Grid", "harga": 8000000},
    "Off-Grid 3kW (1 Phase) - Villa Kecil": {"watt": 3000, "phase": 1, "type": "Off-Grid", "harga": 4500000},
    "Off-Grid 5kW (1 Phase) - Rumah Besar": {"watt": 5000, "phase": 1, "type": "Off-Grid", "harga": 7500000}, # BARU
    
    # 3 Phase (Kantor/Pabrik/Hotel)
    "Hybrid 10kW (3 Phase) - Commercial": {"watt": 10000, "phase": 3, "type": "Hybrid", "harga": 28000000},
    "Hybrid 50kW (3 Phase) - Industrial": {"watt": 50000, "phase": 3, "type": "Hybrid", "harga": 110000000},
    "On-Grid 10kW (3 Phase) - Office/Ruko": {"watt": 10000, "phase": 3, "type": "On-Grid", "harga": 18000000},
    "On-Grid 50kW (3 Phase) - Hotel/Pabrik": {"watt": 50000, "phase": 3, "type": "On-Grid", "harga": 65000000},
    "Off-Grid 10kW (3 Phase) - Remote Area": {"watt": 10000, "phase": 3, "type": "Off-Grid", "harga": 22000000}, # BARU
}

# Database SCC
DB_SCC = {
    "Built-in (Menyatu di Inverter)": {"amp": 0, "harga": 0},
    "MPPT 60A (External)": {"amp": 60, "harga": 1800000},
    "MPPT 100A (High Voltage)": {"amp": 100, "harga": 4500000},
}

# =====================================================
# 2. SETUP PAGE
# =====================================================
st.set_page_config(page_title="Dashboard Investasi PLTS Pro", layout="wide", page_icon="📊")
st.title("📊 Dashboard Investasi PLTS & Analisis Keuangan")
st.markdown("Analisis teknis dan finansial lengkap dengan visualisasi data.")

# =====================================================
# 3. INPUT DATA (BAGIAN ATAS)
# =====================================================
with st.expander("⚙️ Konfigurasi Proyek & Bangunan (Klik untuk Edit)", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.subheader("1. Profil Bangunan")
        tipe_bangunan = st.selectbox("Jenis Properti", ["Rumah Tinggal", "Kantor / Ruko", "Hotel / Villa", "Pabrik / Gudang"])
        # UPDATED: Menambahkan opsi Off-Grid ke semua rekomendasi
        if "Kantor" in tipe_bangunan: Rekomen = ["On-Grid (Hemat Siang)", "Hybrid", "Off-Grid (Mandiri)"]
        elif "Hotel" in tipe_bangunan: Rekomen = ["Hybrid (Backup 24Jam)", "On-Grid", "Off-Grid (Mandiri)"]
        else: Rekomen = ["Hybrid (Canggih)", "On-Grid", "Off-Grid (Mandiri)"]
        
    with c2:
        st.subheader("2. Kelistrikan")
        fasa = st.selectbox("Fasa Listrik", ["1 Phase (220V)", "3 Phase (380V)"])
        
        # Logic default value: jika rumah 1jt, selain itu 10jt, tapi harus >= 10.000
        default_val = 1000000 if "Rumah" in tipe_bangunan else 10000000
        tagihan = st.number_input("Tagihan Listrik (Rp/Bulan)", min_value=10000, max_value=1000000000, value=default_val, step=10000)
        
        tarif = st.number_input("Tarif PLN (Rp/kWh)", value=1444 if "Rumah" in tipe_bangunan else 1699)

    with c3:
        st.subheader("3. Area Pasang")
        lokasi = st.selectbox("Lokasi Instalasi", ["Atap Genteng (Miring)", "Dak Beton (Datar)", "Tanah (Grounding)"])
        jam_matahari = st.slider("Sun Hours", 3.0, 6.0, 4.0)
    
    with c4:
        st.subheader("4. Sistem PLTS")
        tipe_sistem = st.selectbox("Pilih Sistem", Rekomen)
        # Kalkulasi Target
        kwh_bulan = tagihan / tarif
        target_wh = (kwh_bulan / 30) * 1000
        peak_load = (target_wh / 6) * 1.2 # Estimasi kasar
        st.metric("Target Produksi", f"{target_wh/1000:.1f} kWh/hari")

# =====================================================
# 4. PEMILIHAN KOMPONEN
# =====================================================
st.markdown("---")
st.subheader("🛠️ Pemilihan Komponen Utama")
ck1, ck2, ck3, ck4 = st.columns(4)

with ck1:
    pv_select = st.selectbox("Panel Surya", list(DB_PANEL.keys()))
    data_pv = DB_PANEL[pv_select]

with ck2:
    # Filter Inverter Logic
    phase_filter = 3 if "3 Phase" in fasa else 1
    type_filter = "On-Grid" if "On-Grid" in tipe_sistem else "Hybrid" if "Hybrid" in tipe_sistem else "Off-Grid"
    
    # Logic filter diperbarui agar Hybrid juga muncul saat pilih Off-Grid (karena hybrid bisa offgrid)
    inv_list = [k for k,v in DB_INVERTER.items() if v["phase"] == phase_filter and (type_filter in v["type"] or "Hybrid" in v["type"])]
    if not inv_list: inv_list = list(DB_INVERTER.keys()) # Fallback
    
    inv_select = st.selectbox("Inverter", inv_list)
    data_inv = DB_INVERTER[inv_select]

with ck3:
    if "On-Grid" in tipe_sistem:
        st.info("Sistem On-Grid Tanpa Baterai")
        data_bat = {"harga": 0, "volt": 0, "ah": 0}
        bat_select = "-"
        days_backup = 0
    else:
        # Off-Grid atau Hybrid pasti butuh baterai
        bat_select = st.selectbox("Baterai", list(DB_BATTERY.keys()))
        data_bat = DB_BATTERY[bat_select]
        days_backup = st.number_input("Backup (Hari)", 0.2, 3.0, 0.5, step=0.1)

with ck4:
    # Logic: Jika Hybrid atau On-Grid biasanya built-in. Jika Pure Off-Grid Inverter, butuh SCC External
    if "Hybrid" in data_inv["type"] or "On-Grid" in tipe_sistem:
        scc_select = "Built-in (Integrated)"
        data_scc = {"harga": 0, "amp": 0}
        st.success("SCC sudah Built-in")
    else:
        # Masuk sini jika pilih Inverter tipe "Off-Grid" murni
        scc_select = st.selectbox("SCC (Charge Controller)", list(DB_SCC.keys()))
        data_scc = DB_SCC[scc_select]

# =====================================================
# 5. ENGINE PERHITUNGAN
# =====================================================
# 1. Panel
req_pv_wh = target_wh * 1.25
jml_pv = math.ceil(req_pv_wh / (data_pv["wp"] * jam_matahari))
total_wp = jml_pv * data_pv["wp"]
biaya_pv = jml_pv * data_pv["harga"]

# 2. Inverter
jml_inv = math.ceil(peak_load / data_inv["watt"])
jml_inv = max(1, jml_inv)
biaya_inv = jml_inv * data_inv["harga"]

# 3. Baterai
biaya_bat = 0
jml_bat_total = 0
if "On-Grid" not in tipe_sistem:
    req_wh_bat = (target_wh * days_backup) / (data_bat["dod"]/100)
    if data_bat["volt"] == 200: # High Volt
        jml_bat_total = math.ceil(req_wh_bat / (data_bat["volt"]*data_bat["ah"]))
    else: # Low Volt
        sys_volt = 48
        jml_seri = 1 if data_bat["volt"] > sys_volt else sys_volt // data_bat["volt"]
        jml_paralel = math.ceil((req_wh_bat/sys_volt) / data_bat["ah"])
        jml_bat_total = int(jml_seri * jml_paralel)
    biaya_bat = jml_bat_total * data_bat["harga"]

# 4. Biaya Lain
biaya_scc = data_scc["harga"] if scc_select != "Built-in (Integrated)" else 0
lokasi_factor = 1.2 if "Beton" in lokasi else 1.3 if "Tanah" in lokasi else 1.0
biaya_pasang = (3000000 + (jml_pv * 150000)) * lokasi_factor
if "3 Phase" in fasa: biaya_pasang *= 1.5

total_investasi = biaya_pv + biaya_inv + biaya_bat + biaya_scc + biaya_pasang
hemat_thn = (total_wp * jam_matahari * 0.8 / 1000) * tarif * 365
roi = total_investasi / hemat_thn if hemat_thn > 0 else 0

# =====================================================
# 6. VISUALISASI GRAFIK
# =====================================================
st.markdown("---")
st.header("📈 Analisis Visual & Keuangan")

col_grafik_kiri, col_grafik_kanan = st.columns([1, 2])

# --- GRAFIK 1: PIE CHART (KOMPOSISI BIAYA) ---
with col_grafik_kiri:
    st.subheader("Distribusi Anggaran")
    labels = ["Panel Surya", "Inverter", "Baterai", "SCC / Controller", "Instalasi & Material"]
    values = [biaya_pv, biaya_inv, biaya_bat, biaya_scc, biaya_pasang]
    
    # Filter 0 values
    clean_l = [l for l,v in zip(labels, values) if v > 0]
    clean_v = [v for v in values if v > 0]
    
    fig_pie = go.Figure(data=[go.Pie(labels=clean_l, values=clean_v, hole=.4)])
    fig_pie.update_layout(showlegend=False, margin=dict(t=0,b=0,l=0,r=0), height=300)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    st.info(f"**Total Modal: Rp {total_investasi:,.0f}**")

# --- GRAFIK 2: CASHFLOW CHART (ROI) ---
with col_grafik_kanan:
    st.subheader(f"Proyeksi Balik Modal (ROI: {roi:.1f} Tahun)")
    
    years = list(range(0, 21))
    cashflow = [-total_investasi] # Tahun 0
    cumulative = -total_investasi
    
    cf_data = [cumulative]
    
    for y in range(1, 21):
        # Asumsi kenaikan tarif listrik 5% per tahun
        saving_year = hemat_thn * ((1.05) ** (y-1))
        cumulative += saving_year
        cf_data.append(cumulative)
        
    fig_roi = go.Figure()
    # Area Merah (Minus)
    fig_roi.add_trace(go.Scatter(
        x=years, y=cf_data, 
        mode='lines+markers', 
        name='Cashflow Bersih',
        fill='tozeroy',
        line=dict(color='green' if cf_data[-1] > 0 else 'red', width=3)
    ))
    
    # Garis Nol (BEP)
    fig_roi.add_hline(y=0, line_dash="dot", annotation_text="Titik Impas (BEP)", annotation_position="top left")
    
    fig_roi.update_layout(
        xaxis_title="Tahun Ke-",
        yaxis_title="Keuntungan Bersih (Rupiah)",
        height=350,
        margin=dict(t=10,b=10,l=10,r=10)
    )
    st.plotly_chart(fig_roi, use_container_width=True)

# =====================================================
# 7. TABEL RINCIAN
# =====================================================
st.markdown("---")
t1, t2 = st.tabs(["📋 Rincian RAB Lengkap", "🏢 Spesifikasi Teknis"])

with t1:
    df_rab = pd.DataFrame([
        {"Komponen": f"Panel ({pv_select})", "Qty": f"{jml_pv}", "Total": biaya_pv},
        {"Komponen": f"Inverter ({inv_select})", "Qty": f"{jml_inv}", "Total": biaya_inv},
        {"Komponen": f"Baterai ({bat_select})", "Qty": f"{jml_bat_total}", "Total": biaya_bat},
        {"Komponen": f"SCC ({scc_select})", "Qty": "1", "Total": biaya_scc},
        {"Komponen": "Jasa Pasang, Kabel, Rak", "Qty": "1 Lot", "Total": biaya_pasang},
    ])
    df_rab = df_rab[df_rab["Total"] > 0]
    st.table(df_rab.assign(Total=[f"Rp {x:,.0f}" for x in df_rab["Total"]]))

with t2:
    c_s1, c_s2, c_s3 = st.columns(3)
    c_s1.success(f"**PV Generator:** {total_wp/1000:.1f} kWp ({jml_pv} Panel)")
    c_s2.warning(f"**Inverter:** {jml_inv * data_inv['watt']/1000:.1f} kW ({fasa})")
    if jml_bat_total > 0:
        c_s3.info(f"**Storage:** {jml_bat_total*data_bat['ah']*data_bat['volt']/1000:.1f} kWh")
    else:
        c_s3.info("**Storage:** Tanpa Baterai")
