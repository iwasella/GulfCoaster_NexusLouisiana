"This script acts as a biological calculator. It predicts how the population of a specific bird."

import rasterio
import numpy as np
import pandas as pd
import os

# --- STEP 1: LOAD BIOLOGICAL BASELINE ---
csv_file = 'SummaryFileGenerated.csv'
if not os.path.exists(csv_file):
    print("❌ Error: Run your Excel-to-CSV converter first.")
    exit()

df = pd.read_csv(csv_file)

# Focus exclusively on American Oystercatcher in Biloxi
# AMOY is an 'obligate' species—if the marsh/reef goes, they go.
target_species = 'AMOY'
biloxi_data = df[(df['GeoRegion'].str.contains('Biloxi')) & (df['SpeciesCode'] == target_species)]
baseline_birds = biloxi_data['Birds'].sum()

# --- STEP 2: SPATIAL HABITAT ANALYSIS ---
fwoa_file = 'MP2023_Higher_FWOA_U00_02_52_lndchg.tif'
fwmp_file = 'MP2023_Higher_FWMP_U00_02_52_lndtypdiff.tif'
biloxi_window = rasterio.windows.Window(col_off=15000, row_off=3500, width=5000, height=4500)

def get_habitat_score(path, is_mp):
    with rasterio.open(path) as src:
        data = src.read(1, window=biloxi_window)
        # FWOA: Count only existing Brackish Marsh (Code 12)
        if not is_mp:
            return np.sum(data == 12)
        # FWMP: Count maintained and newly restored habitat (200 series)
        else:
            return np.sum((data >= 200) & (data < 300))

# Calculate the habitat "carrying capacity"
habitat_fwoa = get_habitat_score(fwoa_file, False)
habitat_fwmp = get_habitat_score(fwmp_file, True)

# --- STEP 3: THE PREDICTION ENGINE ---
# We assume the current CSV count exists on 'current' habitat. 
# Since we don't have a 'current' TIF, we treat FWOA as the 'decayed' baseline 
# and FWMP as the 'restored' future.
if habitat_fwoa == 0: habitat_fwoa = 1 # Avoid division by zero

# Predicted birds without action (The Crash)
# Based on your previous 8% land result, this will be low.
crash_factor = habitat_fwoa / (habitat_fwmp if habitat_fwmp > 0 else 1)
predicted_fwoa = baseline_birds * crash_factor

# Predicted birds with Master Plan (The Recovery)
# If habitat doubles, we project the population capacity doubles.
growth_factor = habitat_fwmp / habitat_fwoa
predicted_fwmp = baseline_birds * growth_factor

# --- STEP 4: OUTPUT RESULTS ---
print(f"\n--- 🦅 SPECIES REPORT: AMERICAN OYSTERCATCHER (AMOY) ---")
print(f"Location: Biloxi Regional Marsh")
print(f"Current Recorded Population: {baseline_birds} birds")

print(f"\n[ SCENARIO 1: FUTURE WITHOUT ACTION ]")
print(f"📉 Habitat Availability: {habitat_fwoa:,} pixels")
print(f"🔴 Predicted Population: ~{int(predicted_fwoa)} birds")
print(f"Message: Extreme habitat fragmentation leads to local extinction risk.")

print(f"\n[ SCENARIO 2: WITH MASTER PLAN ]")
print(f"📈 Habitat Availability: {habitat_fwmp:,} pixels")
print(f"🟢 Predicted Population: ~{int(predicted_fwmp)} birds")
print(f"Message: Restoration projects act as a 'Nexus' for population recovery.")

print(f"\n[ SUMMARY ]")
net_birds = int(predicted_fwmp - predicted_fwoa)
print(f"The Master Plan 'saves' approximately {net_birds} Oystercatchers in the Biloxi region alone.")