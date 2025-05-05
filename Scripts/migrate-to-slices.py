import geopandas as gpd
from datetime import datetime
from typing import Dict, Any

# Define the file paths for your source and destination shapefiles
source_shapefile: str = 'path/to/your/source.shp'
destination_shapefile: str = 'path/to/your/destination.shp'

# Define the field in the source shapefile to use for the date condition
date_field: str = 'dateadded'
missing_date_field: str
year : int = 1910
# Define the threshold date (you can change this variable)
threshold_date_str: str = '{year}-06-01'
threshold_date: datetime = datetime.strptime(threshold_date_str, '%Y-%m-%d')

# Define the field mapping from the source to the destination
road_fields_mapping: Dict[str, str] = {
    date_field :'First Seen',
    'wholestnam': 'Name',
}
missing_road_fields_mapping: Dict[str,str] = {
    date_field: 'First Seen',
    'Name': 'Name',
    'date Rem': 'Last Seen'
}

# Load the source shapefile
try:
    source_gdf: gpd.GeoDataFrame = gpd.read_file(source_shapefile)
except FileNotFoundError:
    print(f"Error: Source shapefile not found at {source_shapefile}")
    exit()

# Ensure the date field is in datetime format
if date_field in source_gdf.columns:
    try:
        source_gdf[date_field] = gpd.pd.to_datetime(source_gdf[date_field], errors='coerce')
        # 'errors='coerce'' will turn invalid parsing into NaT (Not a Time)
    except Exception as e:
        print(f"Error converting '{date_field}' to datetime: {e}")
        exit()
else:
    print(f"Error: '{date_field}' not found in the source shapefile.")
    exit()

# Filter the source GeoDataFrame based on the date condition
filtered_gdf: gpd.GeoDataFrame = source_gdf[source_gdf[date_field] > threshold_date].copy()

# Create a new GeoDataFrame for the destination with the mapped fields
destination_data: Dict[str, Any] = {}
for source_field, destination_field in road_fields_mapping.items():
    if source_field in filtered_gdf.columns:
        destination_data[destination_field] = filtered_gdf[source_field]
    else:
        print(f"Warning: Source field '{source_field}' not found in the source shapefile.")

# Include the geometry from the filtered GeoDataFrame
destination_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
    destination_data, geometry=filtered_gdf.geometry, crs=filtered_gdf.crs
)

# Save the new GeoDataFrame to the destination shapefile
try:
    destination_gdf.to_file(destination_shapefile)
    print(f"Successfully migrated features to {destination_shapefile}")
except Exception as e:
    print(f"Error saving the destination shapefile: {e}")