"This script is the surveyor. It calculates the literal physical footprint of the Master Plan in square miles."
import rasterio
import numpy as np

fwoa_file = 'MP2023_Higher_FWOA_U00_02_52_lndchg.tif'
fwmp_file = 'MP2023_Higher_FWMP_U00_02_52_lndtypdiff.tif'

# Biloxi Window Coordinates
biloxi_window = rasterio.windows.Window(col_off=15000, row_off=3500, width=5000, height=4500)

def analyze_nexus(path, is_master_plan, window=None):
    with rasterio.open(path) as src:
        data = src.read(1, window=window)
        res_x, res_y = src.res
        sq_mi_factor = abs(res_x * res_y) * 3.86102e-7
        
        if is_master_plan:
            # Master Plan Marsh codes start with 1, 2, or 3 (e.g., 111, 222, 333)
            # This represents land that stayed land or was created.
            marsh_mask = (data >= 100) & (data < 400)
            water_mask = (data >= 500) & (data < 600)
        else:
            # Original codes: 11, 12, 13
            marsh_mask = np.isin(data, [11, 12, 13])
            water_mask = (data == 22)
            
        marsh_count = np.sum(marsh_mask)
        water_count = np.sum(water_mask)
        total = marsh_count + water_count
        
        ratio = (marsh_count / total * 100) if total > 0 else 0
        sq_mi = marsh_count * sq_mi_factor
        return ratio, sq_mi

print("--- 🌊 GULFCOASTER: REAL MASTER PLAN IMPACT 🌊 ---")

# Coastwide Analysis
fwoa_ratio, fwoa_mi = analyze_nexus(fwoa_file, False)
fwmp_ratio, fwmp_mi = analyze_nexus(fwmp_file, True)

print(f"\n[ FULL COASTWIDE ANALYSIS ]")
print(f"Without Action: {fwoa_ratio:.2f}% Land ({fwoa_mi:.2f} sq mi)")
print(f"With Master Plan: {fwmp_ratio:.2f}% Land ({fwmp_mi:.2f} sq mi)")
print(f"NET GAIN: +{fwmp_mi - fwoa_mi:.2f} sq miles saved by projects")

# Biloxi Analysis
b_fwoa_ratio, b_fwoa_mi = analyze_nexus(fwoa_file, False, window=biloxi_window)
b_fwmp_ratio, b_fwmp_mi = analyze_nexus(fwmp_file, True, window=biloxi_window)

print(f"\n[ BILOXI REGIONAL ANALYSIS ]")
print(f"Without Action: {b_fwoa_ratio:.2f}% Land ({b_fwoa_mi:.2f} sq mi)")
print(f"With Master Plan: {b_fwmp_ratio:.2f}% Land ({b_fwmp_mi:.2f} sq mi)")
print(f"REGIONAL GAIN: +{b_fwmp_mi - b_fwoa_mi:.2f} sq miles saved in Biloxi")