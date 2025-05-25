import os
import geopandas as gpd
from datetime import date, datetime
from typing import Dict, Any

# Define the file paths for your source and destination shapefiles
source_shapefilefolder: str = '../Derived-Layers'
destination_shapefilefolder: str = '../Derived-Layers/Time Slices'
destination_missing_roadname: str = 'Missing Roads.shp'
destination_roadname: str = "Roads.shp"
destination_railname: str = "Rail.shp"

# Define the field in the source shapefile to use for the date condition
date_field: str = 'dateadded'
missing_date_field: str = 'date Rem'
years : list[int]= [1800,1860,1880,1900,1910,1920,1950]

i =0
name_field: str = 'wholestnam'
road_fields_mapping: Dict[str, str] = {
    date_field :'First Seen',
    name_field: 'Name',
}
missing_road_fields_mapping: Dict[str,str] = {
    date_field: 'First Seen',
    'Name': 'Name',
    missing_date_field: 'Last Seen'
}
rail_fields_mapping: Dict[str, str] = {
    date_field: 'First Seen',
}

def pull_slice(source_shapefilefolder, destination_shapefilefolder, year, last_year_str):
  pull_features(f"{source_shapefilefolder}/Missing/"+"Missing Streets.shp",
                destination_shapefilefolder,
                destination_missing_roadname,
                last_year_str
                ,year,
                date_field,
                missing_road_fields_mapping, True)
  pull_features(f"{source_shapefilefolder}/Streets/Streets.shp", 
                destination_shapefilefolder,
                destination_roadname,last_year_str,
            year, date_field, road_fields_mapping)

  pull_features(f"{source_shapefilefolder}/Missing/Missing Rail.shp",destination_shapefilefolder,destination_railname,last_year_str,year, date_field,rail_fields_mapping)
  pull_features(f"{source_shapefilefolder}/Railroads/Railroads.shp", destination_shapefilefolder, destination_railname ,last_year_str, year, date_field, rail_fields_mapping)
  last_year = year
# Define the field mapping from the source to the destination
    
def convert_field_to_dt(date_field, source_gdf):
    if date_field in source_gdf.columns:
        try:
            source_gdf[date_field] = gpd.pd.to_datetime(source_gdf[date_field], errors='coerce').dt.date
            # Convert to datetime, handle errors, then extract only the date part
        except Exception as e:
            print(f"Error converting '{date_field}' to date: {e}")
            exit()
    else:
        print(f"Error: '{date_field}' not found in the source shapefile.")
        exit()



def pull_features(source_shapefile, destination_shapefile_folder:str, destinationShapeFileName:str, last_year: int,
year: int, date_field: str, 
fields_mapping: Dict[str,str], missing: bool = False):
    destination_dir = destination_shapefile_folder+f"/{year}"
    if last_year != '0000':
        destinationShapeFileName = f"{destination_dir}/{last_year}-{year} {destinationShapeFileName}"
    else :
        destinationShapeFileName = f"{destination_dir}/{year} {destinationShapeFileName}"
    try:
        source_gdf: gpd.GeoDataFrame = gpd.read_file(source_shapefile)
    except FileNotFoundError:
        print(f"Error: Source shapefile not found at {source_shapefile}")
        exit()
    threshold_date_str: str = f"{year}-12-01"
    last_date_str: str = f"{last_year}-12-01"
    last_date: date
    if last_year != '0000':
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
    print(f"loading time :{last_year}-{year} for {source_shapefile} to {destinationShapeFileName}")
    threshold_date: date = datetime.strptime(threshold_date_str, '%Y-%m-%d').date()

    convert_field_to_dt(date_field, source_gdf)
    if missing:
        convert_field_to_dt(missing_date_field, source_gdf)
    

# Filter the source GeoDataFrame based on the date condition
    filtered_gdf: gpd.GeoDataFrame
    if last_year == "0000":
        if missing :
            filtered_gdf = source_gdf[
                (source_gdf[date_field] < threshold_date) & 
                ((source_gdf[missing_date_field].isna()) | (source_gdf[missing_date_field] >= threshold_date))].copy()
        else:
            filtered_gdf = source_gdf[source_gdf[date_field] < threshold_date].copy()
    else:
        if missing:
            filtered_gdf = source_gdf[
    (source_gdf[date_field] < threshold_date) &
    (source_gdf[date_field] > last_date) &
    ((source_gdf[missing_date_field].isna()) | (source_gdf[missing_date_field] >= threshold_date))
].copy()
        else :
            filtered_gdf = source_gdf[ (source_gdf[date_field] < threshold_date) & (source_gdf[date_field] > last_date) ].copy()       
    features = len(filtered_gdf)


# Create a new GeoDataFrame for the destination with the mapped fields
    destination_data: Dict[str, Any] = {}
    for source_field, destination_field in fields_mapping.items():
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
        if f"{destination_shapefile_folder}/{year}" and not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            print(f"Created destination directory: {destination_dir}")
        destination_gdf.to_file(destinationShapeFileName)
        print(f"Successfully migrated {len(filtered_gdf)} features to {destinationShapeFileName}")
    except FileNotFoundError:
        print(f"Error: destination shapefile not found at {destinationShapeFileName}")
    except Exception as e:
        print(f"Error saving the destination shapefile: {e}")


last_year = "0000"
for year in years :
    pull_slice(source_shapefilefolder,destination_shapefilefolder,year, last_year)
    last_year = year 

    


