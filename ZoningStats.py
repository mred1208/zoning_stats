# This script performs spatial analysis to calculate zoning area statistics and the number of address points 
# that intersect with each zoning classification. The results are written to a CSV file.
# 
# Parameters:
# - zoning_input: Polygon layer representing zoning areas.
# - address_input: Point layer representing address points.
# - zoning_field: Field in the zoning layer representing the zoning classification.
# - output_csv: Output file path where results are saved in CSV format.
# 
# Process:
# - The script loops through all unique zoning classes.
# - For each zoning class, it calculates the total area (in both square feet and acres).
# - It selects address points that fall within each zoning class area and counts them.
# - Results are saved into a CSV file with columns: zoning class, total area (sq ft), total area (acres), 
#   units allowed, units existing (based on addresses), and the difference in units.
# 
# Requires: ArcPy and Pandas libraries.

import arcpy
import pandas as pd
import os

def main():
    # --- Get parameters from GP tool ---
    zoning_input = arcpy.GetParameterAsText(0)      # Polygon layer (zoning)
    address_input = arcpy.GetParameterAsText(1)     # Point layer (address points)
    zoning_field = arcpy.GetParameterAsText(2)      # Zoning classification field
    output_csv = arcpy.GetParameterAsText(3)        # Output CSV path

    arcpy.AddMessage("Starting analysis...")

    # --- Use inputs directly (they're already layers) ---
    zoning_layer = zoning_input
    address_layer = address_input

 # --- Get unique zoning classes ---
    zoning_classes = sorted({row[0] for row in arcpy.da.SearchCursor(zoning_layer, [zoning_field]) if row[0] is not None})

    results = []

    for zone_class in zoning_classes:
        arcpy.AddMessage(f"Processing zoning class: {zone_class}")

        # --- Create temporary layer for current zoning class ---
        zone_query = f"{arcpy.AddFieldDelimiters(zoning_layer, zoning_field)} = '{zone_class}'"
        arcpy.MakeFeatureLayer_management(zoning_layer, "zone_temp", zone_query)

        # --- Calculate total area ---
        total_area = sum(row[0] for row in arcpy.da.SearchCursor("zone_temp", ["SHAPE@AREA"]))
        acres = total_area / 43560.0

        # --- Select address points within zoning area ---
        arcpy.SelectLayerByLocation_management(address_layer, "INTERSECT", "zone_temp", selection_type="NEW_SELECTION")
        count_result = int(arcpy.GetCount_management(address_layer)[0])

        # --- Add result row ---
        results.append({
            "zone class": zone_class,
            "sq ft": round(total_area, 2),
            "acres": round(acres, 2),
            "units per area allowed": "",
            "calc units allowed": "",
            "units per area existing": count_result,
            "diff units": ""
        })

        arcpy.Delete_management("zone_temp")

    # --- Write to CSV ---
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    arcpy.AddMessage(f"Export complete: {output_csv}")

if __name__ == "__main__":
    main()
