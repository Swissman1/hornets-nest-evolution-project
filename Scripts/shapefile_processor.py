import os
import geopandas as gpd
import pandas as pd
from datetime import date, datetime
from typing import Dict, Any
from feature_filter import FeatureFilter

# These should be imported or passed in, but for now, we keep them as module-level variables for compatibility
destination_missing_roadname = 'Missing Roads.shp'
destination_large_roadname = "Large Roads.shp"
destination_roadname = "Roads.shp"
destination_railname = "Rail.shp"
date_field = 'dateadded'
missing_date_field = 'date Rem'
name_field = 'wholestnam'
typeField = 'thoroughfa'
roadTypeField = 'Road Type'
road_fields_mapping: Dict[str, str] = {
    date_field :'First Seen',
    name_field: 'Name',
    typeField: roadTypeField
}
missing_road_fields_mapping: Dict[str,str] = {
    date_field: 'First Seen',
    'Name': 'Name',
    missing_date_field: 'Last Seen'
}
rail_fields_mapping: Dict[str, str] = {
    date_field: 'First Seen',
}

class ShapefileProcessor:
    def __init__(self, source_folder, destination_folder):
        self.source_shapefilefolder = source_folder
        self.destination_shapefilefolder = destination_folder

    def convert_field_to_dt(self, date_field, source_gdf):
        if date_field in source_gdf.columns:
            try:
                source_gdf[date_field] = gpd.pd.to_datetime(source_gdf[date_field], errors='coerce').dt.date
            except Exception as e:
                print(f"Error converting '{date_field}' to date: {e}")
                exit()
        else:
            print(f"Error: '{date_field}' not found in the source shapefile.")
            exit()
    def map_throughfareToType(self, series_data: pd.Series) -> pd.Series:
        # Define your mapping here
        # Keys are original values, values are desired new values
        mapping = {
            'EXMJTH': 'Major Road',
            'C2EX': 'Trunk Road',
            'LOCAL': 'Neighborhood Road',
            'EXCOLLMJ': 'Minor Road',
            'EXMJTHC3C': 'Trunk Road',
            'EXMINTH': 'Collecting Residential Road',
            'EXFRY': 'Highway',
            'PROPFRY': 'Freeway',
            'HISTCOLL': 'Neighborhood Road' # Changed from 'LOCAL' to 'Neighborhood Road' for consistency
        }
        # Use .map() to apply the mapping.
        # .fillna(series_data) ensures that values not in the 'mapping' dictionary
        # retain their original value instead of becoming NaN.
        return series_data.map(mapping).fillna(series_data)

        return
    def pull_features_generic(
        self,
        source_shapefile, destination_shapefile_folder: str, destinationShapeFileName: str, last_year: int,
        year: int, date_field: str, fields_mapping: Dict[str, str], missing: bool = False,
        filter_func=None, isRail: bool = False
    ):
        destination_dir = os.path.join(destination_shapefile_folder, str(year))
        os.makedirs(destination_dir, exist_ok=True)
        if last_year != '0000':
            destinationShapeFileName = os.path.join(destination_dir, f"{last_year}-{year} {destinationShapeFileName}")
        else:
            destinationShapeFileName = os.path.join(destination_dir, f"{year} {destinationShapeFileName}")
        try:
            source_gdf: gpd.GeoDataFrame = gpd.read_file(source_shapefile)
        except FileNotFoundError:
            print(f"Error: Source shapefile not found at {source_shapefile}")
            exit()
        threshold_date_str: str = f"{year}-12-01"
        last_date_str: str = f"{last_year}-12-01"
        last_date: date = None
        if last_year != '0000':
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
        print(f"loading time :{last_year}-{year} for {source_shapefile} to {destinationShapeFileName}")
        threshold_date: date = datetime.strptime(threshold_date_str, '%Y-%m-%d').date()
        self.convert_field_to_dt(date_field, source_gdf)
        if missing:
            self.convert_field_to_dt(missing_date_field, source_gdf)
        filtered_gdf = filter_func(last_year, date_field, missing, source_gdf, last_date, threshold_date, isRail)
        print(f"Filtered GDF length: {len(filtered_gdf)}")
        if not filtered_gdf.empty:
            geom_types = filtered_gdf.geometry.geom_type.unique()
            print(f"Geometry types in filtered_gdf BEFORE writing: {geom_types}")

            # Check for POINT geometries explicitly
            if 'Point' in geom_types or 'MultiPoint' in geom_types:
                point_features = filtered_gdf[filtered_gdf.geometry.geom_type.isin(['Point', 'MultiPoint'])]
                print(f"WARNING: {len(point_features)} Point/MultiPoint features found in filtered_gdf.")
                # Save these problematic features to a temporary shapefile for inspection
                temp_point_shapefile = destinationShapeFileName.replace(".shp", "_POINTS_ERROR.shp")
                point_features.to_file(temp_point_shapefile)
                print(f"Problematic POINT features saved to: {temp_point_shapefile} for inspection.")
                # You might choose to remove them for now to allow the main script to run
                filtered_gdf = filtered_gdf[~filtered_gdf.geometry.geom_type.isin(['Point', 'MultiPoint'])].copy()
                print(f"Filtered GDF length AFTER removing points: {len(filtered_gdf)}")
                if filtered_gdf.empty:
                    print("No non-point features left to write. Exiting this slice.")
                    return

        
        destination_data: Dict[str, Any] = {}
        for source_field, destination_field in fields_mapping.items():
            if source_field in filtered_gdf.columns:
                    if source_field == typeField: 
                        destination_data[destination_field] = self.map_throughfareToType(filtered_gdf[source_field])
                    else:
                        destination_data[destination_field] = filtered_gdf[source_field]
            else:
                print(f"Warning: Source field `{source_field}` not found in the source shapefile.")
        destination_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
            destination_data, geometry=filtered_gdf.geometry, crs=source_gdf.crs
        )
        try:
            destination_gdf.to_file(destinationShapeFileName)
            print(f"Successfully migrated {len(filtered_gdf)} features to {destinationShapeFileName}")
        except FileNotFoundError:
            print(f"Error: destination shapefile not found at {destinationShapeFileName}")
        except Exception as e:
            print(f"Error saving the destination shapefile: {e}")
        return


    
    def pull_slice(self, year, last_year_str):
        missing_streets_path = os.path.join(self.source_shapefilefolder, "Missing", "Missing Streets.shp")
        streets_path = os.path.join(self.source_shapefilefolder, "Streets", "Streets.shp")
        missing_rail_path = os.path.join(self.source_shapefilefolder, "Missing", "Missing Rail.shp")
        railroads_path = os.path.join(self.source_shapefilefolder, "Railroads", "Railroads.shp")

        is_missing_streets_rail = FeatureFilter.determine_rail(missing_streets_path)
        is_streets_rail = FeatureFilter.determine_rail(streets_path)
        is_missing_rail_rail = FeatureFilter.determine_rail(missing_rail_path)
        is_railroads_rail = FeatureFilter.determine_rail(railroads_path)

        self.pull_features_generic(
            missing_streets_path,
            self.destination_shapefilefolder,
            destination_missing_roadname,
            last_year_str,
            year,
            date_field,
            missing_road_fields_mapping,
            True,
            filter_func=FeatureFilter.filter_features,
            isRail=is_missing_streets_rail
        )
        # self.pull_features_generic(
        #     streets_path,
        #     self.destination_shapefilefolder,
        #     destination_large_roadname,
        #     last_year_str,
        #     year,
        #     date_field,
        #     road_fields_mapping,
        #     False,
        #     filter_func=FeatureFilter.filter_big_features,
        #     isRail=is_streets_rail
        # )
        self.pull_features_generic(
            streets_path,
            self.destination_shapefilefolder,
            destination_roadname,
            last_year_str,
            year,
            date_field,
            road_fields_mapping,
            False,
            filter_func=FeatureFilter.filter_features,
            isRail=is_streets_rail
        )


