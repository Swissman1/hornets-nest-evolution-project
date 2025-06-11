# -*- coding: utf-8 -*-
"""
QGIS Python script to apply scale-dependent visibility based on 'road type' attribute.

This script iterates through all vector layers in the current QGIS project.
For each layer that contains a field named 'road type' (case-insensitive),
it applies a rule-based renderer. Each rule corresponds to a unique 'road type'
value, using the same symbol (color and width) but with different minimum and
maximum scale visibility settings.

HOW TO USE:
1. Open your QGIS project.
2. Go to 'Plugins' -> 'Python Console' to open the QGIS Python console.
3. In the console, click on 'Show Editor' button (usually a notepad icon)
   or paste the entire script directly into the console.
4. If using the editor, save the script (e.g., 'apply_road_type_visibility.py')
   and then click the 'Run script' button (green play icon).
5. If pasting directly, press Enter to execute.

Remember to customize the ROAD_TYPE_SCALES dictionary to match your
actual 'road type' values and desired scale ranges.
"""

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRuleBasedRenderer,
    QgsSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsFillSymbol,
    QgsWkbTypes,
    QgsUnitTypes
)
from qgis.utils import iface
from PyQt5.QtGui import QColor

# --- CONFIGURATION ---
# Define the field name for road type (case-insensitive check will be performed)
ROAD_TYPE_FIELD_NAME = "Road Type"

# Define the common symbol properties for all road types
# You can customize color, width, etc.
COMMON_LINE_COLOR = QColor("#1f78b4")  # A nice blue color (hex code)
COMMON_LINE_WIDTH = 0.6               # Line width in mm

# Define scale visibility for each road type.
# Keys should match the values in your "road type" attribute exactly.
# Values are tuples: (minimum_scale, maximum_scale)
# Use 0 for no minimum scale (visible at largest scales)
# Use 0 for no maximum scale (visible at smallest scales)
ROAD_TYPE_SCALES = {
    "Freeway": (0, 50000),     # Visible from largest scale down to 1:50,000
    "Major Road": (0, 25000), # Visible from largest scale down to 1:25,000
    "Trunk Road": (0, 10000),# Visible from largest scale down to 1:10,000
    "Collecting Residental Road": (0, 5000),  # Visible from largest scale down to 1:5,000
    "Neighborhood Road": (5000, 250000), # Visible between 1:5,000 and 1:250,000
    "RAMP": (10000, 500000),   # Visible between 1:10,000 and 1:500,000
    "Footpath": (25000, 1000000), # Visible between 1:25,000 and 1:1,000,000
    "Bridleway": (50000, 0)     # Visible from 1:50,000 onwards to smallest scales
}

# --- SCRIPT LOGIC ---

def apply_road_type_visibility():
    """
    Applies rule-based visibility scaling to vector layers based on
    the 'road type' attribute.
    """
    project = QgsProject.instance()
    layers = project.mapLayers().values()
    processed_layers_count = 0

    if not layers:
        iface.messageBar().pushWarning("No Layers", "No layers found in the current project.")
        print("No layers found in the current project.")
        return

    for layer in layers:
        # Only process vector layers (shapefiles, PostGIS, etc.)
        if isinstance(layer, QgsVectorLayer):
            print(f"Checking layer: {layer.name()}")
            # Find the 'road type' field, case-insensitively
            field_index = -1
            for i, field in enumerate(layer.fields()):
                if field.name().lower() == ROAD_TYPE_FIELD_NAME.lower():
                    field_index = i
                    break

            if field_index != -1:
                print(f"  Found '{ROAD_TYPE_FIELD_NAME}' field.")
                processed_layers_count += 1

                # Create a base symbol that all rules will use
                # The type of symbol depends on the layer's geometry type
                geom_type = layer.geometryType()
                if geom_type == QgsWkbTypes.LineGeometry:
                    base_symbol = QgsLineSymbol.createSimple({'color': COMMON_LINE_COLOR.name(),
                                                              'width': str(COMMON_LINE_WIDTH),
                                                              'width_unit': 'mm'})
                elif geom_type == QgsWkbTypes.PointGeometry:
                    base_symbol = QgsMarkerSymbol.createSimple({'color': COMMON_LINE_COLOR.name(),
                                                                'name': 'circle'})
                elif geom_type == QgsWkbTypes.PolygonGeometry:
                    base_symbol = QgsFillSymbol.createSimple({'color': COMMON_LINE_COLOR.name(),
                                                              'outline_width': str(COMMON_LINE_WIDTH),
                                                              'outline_width_unit': 'mm'})
                else:
                    # Fallback for unknown or mixed geometry types, usually line
                    base_symbol = QgsLineSymbol.createSimple({'color': COMMON_LINE_COLOR.name(),
                                                              'width': str(COMMON_LINE_WIDTH),
                                                              'width_unit': 'mm'})


                # Create the root rule for the rule-based renderer
                # QgsRendererRule is now accessed via QgsRuleBasedRenderer.Rule
                root_rule = QgsRuleBasedRenderer.Rule("root", "Root", "1", base_symbol)
                root_rule.setFilter("") # Make it catch all

                for road_type, (min_scale, max_scale) in ROAD_TYPE_SCALES.items():
                    # Create a rule for each road type
                    # The filter expression targets features with the specific road type value
                    expression = f'"{layer.fields()[field_index].name()}" = \'{road_type}\''
                    symbol_for_rule = base_symbol.clone() # Clone the base symbol for each rule

                    # QgsRendererRule is now accessed via QgsRuleBasedRenderer.Rule
                    rule = QgsRuleBasedRenderer.Rule(
                        f"rule_{road_type.replace(' ', '_')}", # Unique ID for the rule
                        road_type, # Description for the rule in the symbology dialog
                        expression,
                        symbol_for_rule
                    )

                    # Set scale-based visibility for the rule
                    rule.setScaleBasedVisibility(True)
                    rule.setMinimumScale(min_scale)
                    rule.setMaximumScale(max_scale)

                    # Add the rule to the root rule
                    root_rule.appendChild(rule)

                # Create the rule-based renderer and apply it to the layer
                renderer = QgsRuleBasedRenderer(root_rule)
                layer.setRenderer(renderer)

                # Refresh the layer symbology in the legend
                layer.triggerRepaint()
                print(f"  Applied rule-based visibility to layer: {layer.name()}")
            else:
                print(f"  Field '{ROAD_TYPE_FIELD_NAME}' not found in layer: {layer.name()}")

    if processed_layers_count > 0:
        iface.messageBar().pushMessage(
            "Script Complete",
            f"Applied visibility scaling to {processed_layers_count} layers.",
            level=0,  # Info level
            duration=5 # Display for 5 seconds
        )
        print(f"\nScript completed. Applied visibility scaling to {processed_layers_count} layers.")
    else:
        iface.messageBar().pushWarning(
            "Script Complete",
            f"No layers with the '{ROAD_TYPE_FIELD_NAME}' field were found and processed.",
            level=1, # Warning level
            duration=7 # Display for 7 seconds
        )
        print(f"\nScript completed. No layers with the '{ROAD_TYPE_FIELD_NAME}' field were found and processed.")


# Execute the function
if __name__ == '__main__':
    apply_road_type_visibility()
