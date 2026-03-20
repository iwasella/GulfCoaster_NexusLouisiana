import streamlit as st
import rasterio
import numpy as np
import pandas as pd
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GulfCoaster", page_icon="Logo.png",layout="wide")

# --- 1. THE INTEGRATED BIOLOGICAL & GEOSPATIAL ENGINE ---
@st.cache_data
def run_biological_nexus(region_name):
    if region_name != "South Biloxi":
        return None

    # Paths
    fwoa_file = 'MP2023_Higher_FWOA_U00_02_52_lndchg.tif'
    fwmp_file = 'MP2023_Higher_FWMP_U00_02_52_lndtypdiff.tif'
    csv_file = 'SummaryFileGenerated.csv'
    biloxi_window = rasterio.windows.Window(col_off=15000, row_off=3500, width=5000, height=4500)

    if not os.path.exists(csv_file):
        return {"error": "CSV Missing"}
    
    # --- STEP 1: SPATIAL & LAND ANALYSIS ---
    def analyze_spatial(path, is_mp):
        with rasterio.open(path) as src:
            data = src.read(1, window=biloxi_window)
            res_x, res_y = src.res
            sq_mi_factor = abs(res_x * res_y) * 3.86102e-7
            
            if is_mp:
                marsh_mask = (data >= 100) & (data < 400)
                water_mask = (data >= 500) & (data < 600)
                # Habitat Score with +25% Engineering Bonus
                habitat_score = np.sum((data >= 200) & (data < 300)) * 1.25
            else:
                marsh_mask = np.isin(data, [11, 12, 13])
                water_mask = (data == 22)
                # Habitat Score (Marsh code 12 only)
                habitat_score = np.sum(data == 12) * 1.0
            
            marsh_count = np.sum(marsh_mask)
            total = marsh_count + np.sum(water_mask)
            ratio = (marsh_count / total * 100) if total > 0 else 0
            sq_mi = marsh_count * sq_mi_factor
            
            return ratio, sq_mi, habitat_score

    fwoa_ratio, fwoa_mi, score_fwoa = analyze_spatial(fwoa_file, False)
    fwmp_ratio, fwmp_mi, score_fwmp = analyze_spatial(fwmp_file, True)

    # --- STEP 2: BIOLOGICAL BASELINE ---
    df = pd.read_csv(csv_file)
    biloxi_data = df[(df['GeoRegion'].str.contains('Biloxi')) & (df['SpeciesCode'] == 'AMOY')]
    birds_2021 = biloxi_data[biloxi_data['Year'] == 2021]['Birds'].sum()
    
    # Baseline for 2023 (29 birds)
    baseline_2023 = birds_2021 * (1 + 0.024)**(2023 - 2021)

    # --- STEP 3: THE PREDICTION ENGINE ---
    # To match  script: 
    # FWMP Capacity = Baseline * (FWMP Score / FWOA Score)
    # FWOA Capacity = Baseline * (FWOA Score / FWMP Score)
    
    potential_ratio = score_fwmp / (score_fwoa if score_fwoa > 0 else 1)
    
    predicted_fwmp = baseline_2023 * potential_ratio
    predicted_fwoa = baseline_2023 * (score_fwoa / score_fwmp if score_fwmp > 0 else 0)

    return {
        "pred_fwoa": int(predicted_fwoa), # Should be ~2
        "pred_fwmp": int(predicted_fwmp), # Should be ~417
        "bird_gain": int(predicted_fwmp - predicted_fwoa),
        "fwoa_land_pct": round(fwoa_ratio, 2), # 8.44
        "fwoa_land_mi": round(fwoa_mi, 2),   # 151.02
        "fwmp_land_pct": round(fwmp_ratio, 2), # 100.0
        "fwmp_land_mi": round(fwmp_mi, 2),   # 1791.99
        "land_gain_mi": round(fwmp_mi - fwoa_mi, 2) # 1640.97
    }

# --- 2. THE UI STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #3770cc; }
    .main-title { font-size: 3rem; color: #1E3A8A; font-weight: bold; text-align: center; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.2rem; color: #4B5563; text-align: center; margin-bottom: 2rem; }
    .mock-map {
        background-color: #d1d5db; border: 1px solid #9ca3af; border-radius: 12px;
        display: flex; justify-content: center; align-items: center;
        height: 400px; margin-bottom: 20px; font-size: 1.5rem; color: #1f2937;
    }
    [data-testid="stSidebar"] { background-color: #2c6930; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'view_state' not in st.session_state: st.session_state['view_state'] = 'initial'

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("GulfCoaster.png", width=250)
    page = st.radio("Go to:", ["🏠 Dashboard", "📖 Methodology"])
    if st.button("🔄 Reset View"):
        st.session_state['view_state'] = 'initial'
        st.rerun()

# --- 5. MAIN CONTENT ---
if page == "🏠 Dashboard":
    st.markdown('<div class="main-title">Welcome</div>', unsafe_allow_html=True)
    data = pd.DataFrame({
    'latitude': [29.95, 30.05, 28.5, 27.8, 29.8], # New Orleans, Houston, offshore, Corpus, TX
    'longitude': [-90.07, -94.0, -90.0, -97.3, -93.8]
    
})  
    lighthouse_data = pd.DataFrame({
    'name': ['Biloxi Lighthouse'],
    'lat': [30.39445],
    'lon': [-88.90121]
})



    if st.session_state['view_state'] == 'initial':
        st.map(data, latitude='latitude', longitude='longitude', zoom=5)
        st.markdown("### ⚙️ Analysis Parameters")
        region = st.selectbox("Select Region", ['Select...', 'South Biloxi', 'Galveston'])
        if region == 'South Biloxi':
            st.session_state['view_state'] = 'active'
            st.rerun()
    else:
        # EMERGENCY VIEW
        st.map(lighthouse_data, color='#FF0000', size=40)
        
        with st.spinner("Calculating Biological & Geospatial Nexus..."):
            res = run_biological_nexus("South Biloxi")

        if res and "error" not in res:
            st.error("⚠️ **BIOLOGICAL Nexus Emergency:** The American Oystercatcher population is at critical risk in this region.")
            # --- ROW 1: BIRD POPULATION ---
            st.subheader("🦅 Biological Nexus: Population Capacity")
            c1, c2 = st.columns(2)
            c1.metric("FWOA (No Action)", f"~{res['pred_fwoa']} Birds", delta_color="inverse")
            c2.metric("FWMP (Master Plan)", f"~{res['pred_fwmp']} Birds", f"+{res['bird_gain']} Net Gain")

            # --- ROW 2: LAND GAIN ---
            st.subheader("🗺️ Geospatial Nexus: Land Change")
            c3, c4 = st.columns(2)
            c3.metric("FWOA Land", f"{res['fwoa_land_pct']}%", f"{res['fwoa_land_mi']} sq mi", delta_color="off")
            c4.metric("FWMP Land", f"{res['fwmp_land_pct']}%", f"+{res['land_gain_mi']} sq mi saved")
            
            st.success(f"**Impact Summary:** The Master Plan prevents a **{res['fwoa_land_pct']}%** collapse by saving **{res['land_gain_mi']} square miles** of Biloxi shoreline.")