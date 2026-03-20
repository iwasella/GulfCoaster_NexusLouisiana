import rasterio  # Library for reading geographic "raster" images (TIFFs)
import numpy as np # Library for doing fast math on large grids of numbers

# These are the paths to our data files (spatial maps of the coast)
fwoa_file = 'MP2023_Higher_FWOA_U00_02_52_lndchg.tif'
fwmp_file = 'MP2023_Higher_FWMP_U00_02_52_lndtypdiff.tif'

# We define a "Window" to zoom into Biloxi. 
# It says: "Start 15,000 pixels from the left, 3,500 from the top, and grab a 5000x4500 box."
biloxi_window = rasterio.windows.Window(col_off=15000, row_off=3500, width=5000, height=4500)

def analyze_nexus(path, is_master_plan, window=None):
    # 'with' ensures the file closes automatically when we are done
    with rasterio.open(path) as src:
        
        # Read the pixel data from the first 'band' (layer) of the image
        data = src.read(1, window=window)
        
        # Get the physical size of one pixel (usually in meters or feet)
        res_x, res_y = src.res
        
        # Calculate the conversion factor to turn "one pixel" into "square miles"
        # Area = Width * Height. The scientific notation is the constant to convert to miles.
        sq_mi_factor = abs(res_x * res_y) * 3.86102e-7
        
        # These IF/ELSE statements tell the script which "pixel values" count as land
        if is_master_plan:
            # In the Master Plan file, codes 100-399 are various types of land/marsh
            marsh_mask = (data >= 100) & (data < 400)
            # Codes 500-599 are water
            water_mask = (data >= 500) & (data < 600)
        else:
            # In the "Without Action" file, land is specifically coded as 11, 12, or 13
            marsh_mask = np.isin(data, [11, 12, 13])
            # Water is specifically coded as 22
            water_mask = (data == 22)
            
        # Count how many pixels fell into the "Land" category and "Water" category
        marsh_count = np.sum(marsh_mask)
        water_count = np.sum(water_mask)
        total = marsh_count + water_count
        
        # Calculate the percentage of the area that is land
        ratio = (marsh_count / total * 100) if total > 0 else 0
        
        # Multiply the number of land pixels by our square mile conversion factor
        sq_mi = marsh_count * sq_mi_factor
        
        return ratio, sq_mi

# --- START THE REPORTING ---
print("--- 🌊 GULFCOASTER: REAL MASTER PLAN IMPACT 🌊 ---")

# Run the analysis for the WHOLE COAST (no window provided)
fwoa_ratio, fwoa_mi = analyze_nexus(fwoa_file, False) # Look for land using FWOA codes
fwmp_ratio, fwmp_mi = analyze_nexus(fwmp_file, True)  # Look for land using Master Plan codes

print(f"\n[ FULL COASTWIDE ANALYSIS ]")
print(f"Without Action: {fwoa_ratio:.2f}% Land ({fwoa_mi:.2f} sq mi)")
print(f"With Master Plan: {fwmp_ratio:.2f}% Land ({fwmp_mi:.2f} sq mi)")
# Subtract the two to find the "Saved" land
print(f"NET GAIN: +{fwmp_mi - fwoa_mi:.2f} sq miles saved by projects")

# Run the analysis again, but ONLY for the Biloxi "Window" box we defined earlier
b_fwoa_ratio, b_fwoa_mi = analyze_nexus(fwoa_file, False, window=biloxi_window)
b_fwmp_ratio, b_fwmp_mi = analyze_nexus(fwmp_file, True, window=biloxi_window)

print(f"\n[ BILOXI REGIONAL ANALYSIS ]")
print(f"Without Action: {b_fwoa_ratio:.2f}% Land ({b_fwoa_mi:.2f} sq mi)")
print(f"With Master Plan: {b_fwmp_ratio:.2f}% Land ({b_fwmp_mi:.2f} sq mi)")
print(f"REGIONAL GAIN: +{b_fwmp_mi - b_fwoa_mi:.2f} sq miles saved in Biloxi")