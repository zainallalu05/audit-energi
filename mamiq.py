import streamlit as st
import pandas as pd
import math

# =====================================================
# KONFIGURASI HALAMAN
# =====================================================
st.set_page_config(
    page_title="Kalkulator PLTS Lengkap",
    layout="wide",
    page_icon="☀"
)

st.title("☀ Kalkulator PLTS Lengkap")
st.write("Hitung konsumsi energi, biaya PLN, kebutuhan PLTS, dan estimasi balik modal.")
st.markdown("---")

# =====================================================
# INISIALISASI SESSION STATE (WAJIB)
# =====================================================
if "beban" not in st.session_state:
    st.session_state.beban = []

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.header("🔧 Jenis Sistem")
    sistem = st.radio("Pilih Sistem PLTS", ["On-Grid", "Off-Grid", "Hybrid"])

    st.header("⚙️ Parameter Teknis")
    jam_matahari = st.slider("Jam Matahari Efektif", 3.0, 6.0, 4.5)
    loss = st.slider("Loss Sistem (%)", 10, 50, 30)
    tegangan = st.selectbox("Tegangan Sistem (V)", [12, 24, 48], index=1)

    if sistem != "On-Grid":
        dod = st.slider("Depth of Discharge (%)", 20, 90, 50)
        cadangan_hari = st.slider("Cadangan Hari", 1, 3, 1)
        kapasitas_baterai = st.number_input("Kapasitas 1 Baterai (Ah)", 50, 300, 100)

    st.header("☀ Panel & Harga")
    panel_wp = st.number_input("Kapasitas Panel (Wp)", 100, 1000, 550)
    harga_panel_wp = st.number_input("Harga Panel (Rp/Wp)", value=4000)

    st.header("💡 Tarif PLN")
    tarif_pln = st.number_input("Tarif PLN (Rp/kWh)", value=1444)

    st.header("💰 Biaya Lain")
    harga_inverter = st.number_input("Harga Inverter (Rp)", value=3000000)
    harga_scc = st.number_input("Harga SCC (Rp)", value=1500000)
    biaya_instalasi = st.number_input("Biaya Instalasi (Rp)", value=3000000)
    harga_baterai_wh = st.number_input("Harga Baterai (Rp/Wh)", value=3000)

    st.header("🔌 Input Beban Listrik")
    with st.form("form_beban", clear_on_submit=True):
        nama = st.text_input("Nama Peralatan")
        daya = st.number_input("Daya (Watt)", min_value=0)
        jumlah = st.number_input("Jumlah", min_value=1)
        jam = st.number_input("Jam Pakai per Hari", min_value=0.0, max_value=24.0, step=0.5)
        submit = st.form_submit_button("➕ Tambahkan")

        if submit and daya > 0 and jam > 0:
            st.session_state.beban.append({
                "Peralatan": nama,
                "Daya (W)": daya,
                "Jumlah": jumlah,
                "Jam/Hari": jam
            })
            st.rerun()

    if st.button("🗑️ Reset Semua Beban"):
        st.session_state.beban = []
        st.rerun()

# =====================================================
# HALAMAN UTAMA
# =====================================================
if len(st.session_state.beban) == 0:
    st.info("⬅️ Masukkan beban listrik di sidebar.")
else:
    df = pd.DataFrame(st.session_state.beban)

    # ================= VALIDASI KOLOM =================
    kolom_wajib = ["Daya (W)", "Jumlah", "Jam/Hari"]
    for k in kolom_wajib:
        if k not in df.columns:
            st.error("Data tidak valid. Silakan reset beban.")
            st.stop()

    # ================= HITUNG ENERGI =================
    df["Energi (Wh/Hari)"] = df["Daya (W)"] * df["Jumlah"] * df["Jam/Hari"]
    df["Energi (kWh/Hari)"] = df["Energi (Wh/Hari)"] / 1000

    st.subheader("📋 Daftar Beban Listrik")
    st.dataframe(df, use_container_width=True)

    energi_harian = df["Energi (kWh/Hari)"].sum()
    energi_bulanan = energi_harian * 30
    energi_tahunan = energi_harian * 365

    beban_puncak = (df["Daya (W)"] * df["Jumlah"]).sum()

    # ================= KONSUMSI =================
    st.subheader("⚡ Konsumsi Energi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Harian", f"{energi_harian:.2f} kWh")
    c2.metric("Bulanan", f"{energi_bulanan:.2f} kWh")
    c3.metric("Tahunan", f"{energi_tahunan:.2f} kWh")

    # ================= BIAYA PLN =================
    biaya_harian = energi_harian * tarif_pln
    biaya_bulanan = energi_bulanan * tarif_pln
    biaya_tahunan = energi_tahunan * tarif_pln

    st.subheader("💸 Biaya Listrik PLN")
    b1, b2, b3 = st.columns(3)
    b1.metric("Harian", f"Rp {biaya_harian:,.0f}")
    b2.metric("Bulanan", f"Rp {biaya_bulanan:,.0f}")
    b3.metric("Tahunan", f"Rp {biaya_tahunan:,.0f}")

    # ================= HITUNG PLTS =================
    total_wh = energi_harian * 1000
    total_wp = (total_wh * (1 + loss / 100)) / jam_matahari
    jumlah_panel = math.ceil(total_wp / panel_wp)
    biaya_panel = total_wp * harga_panel_wp

    jumlah_baterai = 0
    biaya_baterai = 0

    if sistem != "On-Grid":
        kebutuhan_baterai_wh = (total_wh * cadangan_hari) / (dod / 100)
        total_ah = kebutuhan_baterai_wh / tegangan
        jumlah_baterai = math.ceil(total_ah / kapasitas_baterai)
        biaya_baterai = kebutuhan_baterai_wh * harga_baterai_wh

    inverter_min = math.ceil(beban_puncak * 1.3)

    total_biaya = (
        biaya_panel +
        biaya_baterai +
        harga_inverter +
        harga_scc +
        biaya_instalasi
    )

    # ================= HASIL =================
    st.markdown("---")
    st.subheader("🔋 Rekomendasi Sistem PLTS")

    r1, r2, r3, r4 = st.columns(4)
    r1.success(f"☀ Panel\n{jumlah_panel} unit")
    r2.success(f"🔋 Baterai\n{jumlah_baterai} unit")
    r3.info(f"🔌 Inverter\n{inverter_min} W")
    r4.info(f"⚡ Beban Puncak\n{beban_puncak} W")

    st.subheader("💰 Biaya Pembangunan")
    st.metric("Total Investasi", f"Rp {total_biaya:,.0f}")

    st.subheader("📈 Estimasi Balik Modal")
    if sistem == "Off-Grid":
        st.info("Sistem Off-Grid tidak memiliki perhitungan balik modal PLN.")
    else:
        payback = total_biaya / biaya_tahunan if biaya_tahunan > 0 else 0
        st.metric("Payback Period", f"{payback:.1f} tahun")

st.markdown("---")
st.caption("Kalkulator PLTS Lengkap – Versi Stabil (Final)")
