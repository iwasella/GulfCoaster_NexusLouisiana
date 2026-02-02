import rasterio
import numpy as np

# Focus only on the new Master Plan file
fwmp_file = 'MP2023_Higher_FWMP_U00_02_52_lndtypdiff.tif'

with rasterio.open(fwmp_file) as dataset:
    # Read a sample of the data
    data = dataset.read(1)
    unique_values = np.unique(data)
    
    print("--- 🔍 FWMP CODE DIAGNOSTIC ---")
    print(f"Unique Codes found in Master Plan file: \n{unique_values}")