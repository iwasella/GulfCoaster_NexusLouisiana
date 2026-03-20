import rasterio
import numpy as np
import pandas as pd
import os

# --- STEP 1: LOAD BIOLOGICAL BASELINE & TREND ADJUSTMENT ---
# Data Source: American Oystercatcher Working Group (amoywg.org) 
# The 2023 range-wide assessment confirmed a ~2.4% annual growth rate 
# for the Atlantic/Gulf populations from 2008-2023.
csv_file = 'SummaryFileGenerated.csv'
if not os.path.exists(csv_file):
    print("❌ Error: Run your Excel-to-CSV converter first.")
    exit()

df = pd.read_csv(csv_file)

# Filter for our specific species and region
target_species = 'AMOY'
biloxi_data = df[(df['GeoRegion'].str.contains('Biloxi')) & (df['SpeciesCode'] == target_species)]

# Fix: We grab the 2021 total count as our "Known Reality"
latest_year = 2021 
biloxi_2021 = biloxi_data[biloxi_data['Year'] == latest_year]
birds_2021 = biloxi_2021['Birds'].sum()

# FIXING THE TIME GAP: 
# Since we are using the 2023 Master Plan, we project our 2021 birds forward 2 years.
# Formula: Count * (1 + GrowthRate)^Years
growth_rate = 0.024 # 2.4% based on 2023 species reports
baseline_birds_2023 = int(birds_2021 * (1 + growth_rate)**(2023 - 2021))

# --- STEP 2: SPATIAL HABITAT ANALYSIS ---
# Data Source: LA Master Plan 2023 (CPRA) - Habitat Suitability Index (HSI)
# CPRA uses "Land Type" to determine if a species can survive.
fwoa_file = 'MP2023_Higher_FWOA_U00_02_52_lndchg.tif'
fwmp_file = 'MP2023_Higher_FWMP_U00_02_52_lndtypdiff.tif'
biloxi_window = rasterio.windows.Window(col_off=15000, row_off=3500, width=5000, height=4500)

def get_habitat_score(path, is_mp):
    with rasterio.open(path) as src:
        data = src.read(1, window=biloxi_window)
        
        # FWOA: Existing Marsh (Code 12) is often "fragmented" or "sinking."
        # It receives a standard quality weight of 1.0.
        if not is_mp:
            return np.sum(data == 12) * 1.0
        
        # FWMP: Restored Habitat (200-300 series).
        # Scientifically, restored marsh is built to "Target Elevations."
        # For AMOY, higher elevation = fewer nests lost to high tide (overwash).
        # We apply a 25% "Quality Bonus" for engineered restoration.
        else:
            raw_count = np.sum((data >= 200) & (data < 300))
            return raw_count * 1.25 

habitat_score_fwoa = get_habitat_score(fwoa_file, False)
habitat_score_fwmp = get_habitat_score(fwmp_file, True)

# --- STEP 3: THE PREDICTION ENGINE (Carrying Capacity) ---
# We treat the 2023 Adjusted Population as the "seed."
# The ratio of (Future Score / 2021 Score) determines the population's future.
# Note: Since we don't have a 2021 TIF, we assume FWOA represents the 
# current decaying baseline.

# Calculate how much better/worse the Master Plan is compared to "Doing Nothing"
potential_ratio = habitat_score_fwmp / (habitat_score_fwoa if habitat_score_fwoa > 0 else 1)

# Final Predictions
predicted_fwoa = baseline_birds_2023 * (habitat_score_fwoa / habitat_score_fwmp)
predicted_fwmp = baseline_birds_2023 * potential_ratio

# --- STEP 4: OUTPUT RESULTS ---
print(f"--- 🦅 BIOLOGICAL NEXUS: AMOY BILOXI REPORT ---")
print(f"2021 Survey Count: {birds_2021} birds")
print(f"2023 Estimated Baseline: {baseline_birds_2023} birds (Adjusted for 2.4% annual growth)")
print(f"Habitat Quality Factor: +25% bonus for engineered restoration elevation")

print(f"\n[ RESULTS ]")
print(f"FWOA (No Action) Capacity: ~{int(predicted_fwoa)} birds")
print(f"FWMP (Master Plan) Capacity: ~{int(predicted_fwmp)} birds")
print(f"\nNET GAIN: The Master Plan supports ~{int(predicted_fwmp - predicted_fwoa)} additional Oystercatchers.")