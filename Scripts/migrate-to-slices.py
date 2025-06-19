from shapefile_processor import ShapefileProcessor
from migration_manager import MigrationManager

# Define the file paths and years
source_shapefilefolder: str = '../Derived-Layers'
destination_shapefilefolder: str = '../Derived-Layers/Time Slices'
years = [2025]

if __name__ == "__main__":
    processor = ShapefileProcessor(source_shapefilefolder, destination_shapefilefolder)
    manager = MigrationManager(processor, years)
    manager.run()
