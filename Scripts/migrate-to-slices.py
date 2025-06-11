from shapefile_processor import ShapefileProcessor
from migration_manager import MigrationManager

# Define the file paths and years
source_shapefilefolder: str = '../Derived-Layers'
destination_shapefilefolder: str = '../Derived-Layers/Time Slices'
years = [1800,1860,1880,1900,1920,1950,1980,1995,2025]

if __name__ == "__main__":
    processor = ShapefileProcessor(source_shapefilefolder, destination_shapefilefolder)
    manager = MigrationManager(processor, years)
    manager.run()
