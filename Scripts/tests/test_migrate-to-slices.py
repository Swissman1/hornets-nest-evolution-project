import os
import shutil
import pytest
import geopandas as gpd
from shapely.geometry import Point
from datetime import date

from migrate_to_slices import pull_features

@pytest.fixture
def temp_shapefile(tmp_path):
    # Create a temporary GeoDataFrame
    data = {
        'First Seen': [date(2022, 11, 30), date(2023, 1, 1), date(2023, 11, 30)],
        'Name': ['A', 'B', 'C'],
        'date Rem': [None, date(2023, 12, 2), date(2023, 12, 5)],
        'Type': ['road', 'road', 'road'],
        'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]
    }
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
    shapefile_path = tmp_path / "source.shp"
    gdf.to_file(shapefile_path)
    return str(shapefile_path), gdf

@pytest.fixture
def cleanup(tmp_path):
    yield
    # Remove all files and folders created in tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)

def test_pull_features_successful_migration(temp_shapefile, tmp_path, cleanup):
    source_shapefile, original_gdf = temp_shapefile
    destination_folder = str(tmp_path / "dest")
    destination_name = "output.shp"
    last_year = "2022"
    year = 2023
    date_field = "First Seen"
    fields_mapping = {"First Seen": "first_seen", "Name": "name"}
    # Ensure destination folder does not exist before test
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    # Call the function
    pull_features(
        source_shapefile=source_shapefile,
        destination_shapefile_folder=destination_folder,
        destinationShapeFileName=destination_name,
        last_year=last_year,
        year=year,
        date_field=date_field,
        fields_mapping=fields_mapping,
        missing=False
    )
    # Check that the destination shapefile exists
    expected_dir = os.path.join(destination_folder, str(year))
    expected_file = os.path.join(expected_dir, f"{last_year}-{year} {destination_name}")
    assert os.path.exists(expected_file)
    # Read the output and check contents
    result_gdf = gpd.read_file(expected_file)
    # Should only include features with First Seen < threshold_date (2023-12-01) and > last_date (2022-12-01)
    # That is, only the features with First Seen == 2023-01-01 and 2023-11-30
    expected_names = ['B', 'C']
    assert set(result_gdf['name']) == set(expected_names)
    assert set(result_gdf['first_seen']) == set(['2023-01-01', '2023-11-30'])
    # Geometry should be preserved
    assert len(result_gdf) == 2
    assert all(result_gdf.geometry.type == "Point")