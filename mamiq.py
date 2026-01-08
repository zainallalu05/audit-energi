import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go

# =====================================================
# KONFIGURASI HALAMAN
# =====================================================
st.set_page_config(
    page_title="Kalkulator PLTS Pro Lengkap 2026",
    layout="wide",
    page_icon="☀"
)

st.title("☀ Kalkulator PLTS Pro: Solusi Energi Terpadu")
st.write("Analisis komprehensif konsumsi energi, investasi detail, dan spesifikasi teknis material.")
st.markdown("---")

# =====================================================
# INISIALISASI SESSION STATE
# =====================================================
if "beban" not in st.session_state:
    st.session_state.beban = []

# =====================================================
# SIDEBAR - PARAMETER INPUT
# =====================================================
with st.sidebar:
    st.header("🔧 Pengaturan Sistem")
    sistem = st.radio("Pilih Sistem PLTS", ["On-Grid", "Off-Grid", "Hybrid"])
    tegangan_sistem = st.selectbox("Tegangan Sistem DC (V)", [12, 24, 48], index=1)
    jam_matahari = st.slider("Jam Matahari Efektif (PSH)", 3.0, 6.0, 4.5)

    st.header("☀ Spesifikasi Panel")
    jenis_panel = st.selectbox("Jenis Panel Surya", ["Monocrystalline (Efisien)", "Polycrystalline (Ekonomis)"])
    panel_wp = st.number_input("Kapasitas 1 Panel (Wp)", value=550)
    vmp_panel = st.number_input("Tegangan Panel (Vmp)", value=42.0)
    imp_panel = st.number_input("Arus Panel (Imp)", value=13.0)
    loss = st.slider("Loss Sistem (%)", 10, 50, 30)

    st.header("🔋 Spesifikasi Baterai")
    if sistem != "On-Grid":
        tipe_baterai = st.selectbox("Pilih Teknologi Baterai", ["Lithium LiFePO4", "VRLA / AGM (Gel)"])
        default_dod = 80 if tipe_baterai == "Lithium LiFePO4" else 50
        dod = st.slider("Depth of Discharge (%)", 10, 90, default_dod)
        cadangan_hari = st.slider("Cadangan Hari (Autonomy)", 1, 3, 1)
        kapasitas_baterai_ah = st.number_input("Kapasitas 1 Baterai (Ah)", value=100)
        tegangan_baterai_unit = st.selectbox("Tegangan 1 Baterai (V)", [12, 24, 48], index=0)
        harga_baterai_per_unit = st.number_input("Harga 1 Unit Baterai (Rp)", value=2500000)
    else:
        st.write("Sistem On-Grid tidak menggunakan baterai.")

    st.header("💰 Parameter Ekonomi")
    tarif_pln = st.number_input("Tarif PLN (Rp/kWh)", value=1444)
    harga_panel_per_unit = st.number_input("Harga 1 Unit Panel (Rp)", value=2200000)
    harga_inverter = st.number_input("Harga Inverter (Rp)", value=5000000)
    harga_scc = st.number_input("Harga SCC (Rp)", value=1500000)
    biaya_instalasi = st.number_input("Biaya Instalasi & Rak (Rp)", value=3000000)

    st.header("🔌 Input Beban Listrik")
    with st.form("form_beban", clear_on_submit=True):
        nama = st.text_input("Nama Peralatan")
        daya = st.number_input("Daya (Watt)", min_value=0)
        jumlah = st.number_input("Jumlah", min_value=1)
        jam = st.number_input("Jam Pakai per Hari", min_value=0.0, max_value=24.0, step=0.5)
        submit = st.form_submit_button("➕ Tambahkan Beban")
        if submit and daya > 0 and jam > 0:
            st.session_state.beban.append({"Peralatan": nama, "Daya (W)": daya, "Jumlah": jumlah, "Jam/Hari": jam})
            st.rerun()

    if st.button("🗑️ Reset Semua Beban"):
        st.session_state.beban = []
        st.rerun()

# =====================================================
# PERHITUNGAN & TAMPILAN UTAMA
# =====================================================
if not st.session_state.beban:
    st.info("⬅️ Masukkan beban listrik di sidebar untuk mulai mensimulasikan sistem PLTS Anda.")
else:
    # --- LOGIKA PERHITUNGAN ---
    df = pd.DataFrame(st.session_state.beban)
    df["Wh/Hari"] = df["Daya (W)"] * df["Jumlah"] * df["Jam/Hari"]
    df["kWh/Hari"] = df["Wh/Hari"] / 1000
    
    energi_harian = df["kWh/Hari"].sum()
    biaya_harian = energi_harian * tarif_pln
    beban_puncak = (df["Daya (W)"] * df["Jumlah"]).sum()

    total_wh_loss = (energi_harian * 1000) * (1 + loss / 100)
    jumlah_panel = math.ceil((total_wh_loss / jam_matahari) / panel_wp)
    biaya_panel_total = jumlah_panel * harga_panel_per_unit

    biaya_baterai_total = 0
    total_unit_baterai = 0
    seri_bat = 0
    paralel_bat = 0
    if sistem != "On-Grid":
        wh_storage = (energi_harian * 1000 * cadangan_hari) / (dod / 100)
        seri_bat = tegangan_sistem // tegangan_baterai_unit
        ah_total_req = wh_storage / tegangan_sistem
        paralel_bat = math.ceil(ah_total_req / kapasitas_baterai_ah)
        total_unit_baterai = max(1, seri_bat * paralel_bat)
        biaya_baterai_total = total_unit_baterai * harga_baterai_per_unit

    inverter_min = math.ceil(beban_puncak * 1.3)
    scc_min = math.ceil((jumlah_panel * panel_wp) / tegangan_sistem * 1.2)
    total_investasi = biaya_panel_total + biaya_baterai_total + harga_inverter + harga_scc + biaya_instalasi

    # --- BAGIAN 1: DAFTAR BEBAN & KONSUMSI ---
    st.header("1. 📋 Analisis Beban & Energi")
    col_beban1, col_beban2 = st.columns([2, 1])
    
    with col_beban1:
        st.subheader("Daftar Peralatan Listrik")
        st.dataframe(df, use_container_width=True)
    
    with col_beban2:
        st.subheader("Estimasi Konsumsi & Biaya PLN")
        data_pln = {
            "Periode": ["Harian", "Bulanan (30 hr)", "Tahunan (365 hr)"],
            "Energi (kWh)": [f"{energi_harian:.2f}", f"{energi_harian*30:.2f}", f"{energi_harian*365:.2f}"],
            "Biaya PLN": [f"Rp {biaya_harian:,.0f}", f"Rp {biaya_harian*30:,.0f}", f"Rp {biaya_harian*365:,.0f}"]
        }
        st.table(pd.DataFrame(data_pln))

    st.markdown("---")

    # --- BAGIAN 2: RINCIAN INVESTASI & DIAGRAM ---
    st.header("2. 💰 Analisis Investasi")
    col_inv1, col_inv2 = st.columns([1, 1])

    with col_inv1:
        st.subheader("Rincian Biaya Material")
        rincian_biaya = [
            {"Komponen": "Panel Surya", "Subtotal": biaya_panel_total},
            {"Komponen": "Baterai", "Subtotal": biaya_baterai_total},
            {"Komponen": "Inverter", "Subtotal": harga_inverter},
            {"Komponen": "SCC", "Subtotal": harga_scc},
            {"Komponen": "Instalasi & Rak", "Subtotal": biaya_instalasi},
        ]
        df_biaya = pd.DataFrame(rincian_biaya)
        df_tampilan = df_biaya.copy()
        df_tampilan["Subtotal"] = df_tampilan["Subtotal"].apply(lambda x: f"Rp {x:,.0f}")
        st.table(df_tampilan)
        st.metric("Total Investasi", f"Rp {total_investasi:,.0f}")

    with col_inv2:
        st.subheader("Distribusi Anggaran")
        labels_list = df_biaya["Komponen"].tolist()
        values_list = df_biaya["Subtotal"].tolist()
        fig = go.Figure(data=[go.Pie(labels=labels_list, values=values_list, hole=.3)])
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- BAGIAN 3: SPESIFIKASI TEKNIS ---
    st.header("3. 📦 Detail Spesifikasi Komponen")
    col_spec1, col_spec2 = st.columns(2)

    with col_spec1:
        st.info(f"### ☀ Panel Surya ({jenis_panel})")
        st.write(f"- **Kapasitas Per Panel:** {panel_wp} Wp")
        st.write(f"- **Jumlah Panel:** {jumlah_panel} Unit")
        st.write(f"- **Total Kapasitas:** {jumlah_panel * panel_wp} Wp")
        st.write(f"- **Arus Output Total (Imp):** {jumlah_panel * imp_panel:.2f} A")

        st.info("### 🔌 Inverter & SCC")
        st.write(f"- **Kapasitas Inverter:** Min {inverter_min} Watt (PSW)")
        st.write(f"- **Rating Arus SCC:** Min {scc_min} Ampere")
        st.write(f"- **Tegangan Sistem:** {tegangan_sistem} VDC")

    with col_spec2:
        if sistem != "On-Grid":
            st.success(f"### 🔋 Bank Baterai ({tipe_baterai})")
            st.write(f"- **Kapasitas Per Unit:** {kapasitas_baterai_ah} Ah / {tegangan_baterai_unit} V")
            st.write(f"- **Konfigurasi:** {seri_bat} Seri x {paralel_bat} Paralel")
            st.write(f"- **Total Unit:** {total_unit_baterai} Unit")
            st.write(f"- **DoD Aman:** {dod}%")
        else:
            st.warning("### 🔋 Bank Baterai\nSistem On-Grid tidak menggunakan baterai.")

        st.success("### 🏗️ Kabel & Keamanan")
        arus_dc = (jumlah_panel * panel_wp) / tegangan_sistem
        kabel = "4 mm²" if arus_dc < 25 else "6 mm²" if arus_dc < 45 else "10 mm²"
        st.write(f"- **Arus DC Utama:** {arus_dc:.2f} A")
        st.write(f"- **Ukuran Kabel:** Min {kabel}")
        st.write(f"- **Proteksi:** MCB DC & Arrester Surya")

    st.markdown("---")

    # --- BAGIAN 4: KESIMPULAN ---
    st.header("4. 📝 Kesimpulan Akhir")
    payback = (total_investasi / (biaya_harian * 365)) if biaya_harian > 0 else 0
    
    st.success(f"""
    * **Kapasitas PLTS**: Sistem Anda membutuhkan **{jumlah_panel * panel_wp} Wp** untuk mengcover energi **{energi_harian:.2f} kWh/hari**.
    * **Keuangan**: Dengan investasi sebesar **Rp {total_investasi:,.0f}**, titik balik modal (Payback Period) tercapai dalam **{payback:.1f} tahun**.
    * **Rekomendasi**: Gunakan kabel minimal **{kabel}** dan pastikan inverter berjenis **Pure Sine Wave** untuk menjaga keawetan alat elektronik Anda.
    """)

st.caption("Kalkulator PLTS Pro Lengkap - Versi Stabil 2026")
