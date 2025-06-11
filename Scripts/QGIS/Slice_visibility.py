# -*- coding: utf-8 -*-
"""
QGIS Python script to apply specific colors to layers based on their names
(representing time slices) AND apply scale-dependent visibility based on
the 'road type' attribute *within* each of those layers.

This script iterates through all vector layers in the current QGIS project.
For each layer whose name matches an entry in the LAYER_TIME_SLICES dictionary:
1. It identifies the layer's specific color.
2. It then applies a rule-based renderer to that layer.
3. The rules are based on the 'road type' attribute, and each rule uses the
   layer's specific color, but with scale-dependent visibility defined for
   each road type.

HOW TO USE:
1. Open your QGIS project with the time slice layers.
2. Go to 'Plugins' -> 'Python Console' to open the QGIS Python console.
3. In the console, click on 'Show Editor' button (usually a notepad icon)
   or paste the entire script directly into the console.
4. CUSTOMIZE THE 'LAYER_TIME_SLICES' DICTIONARY:
   - Ensure the layer names (keys) exactly match your layer names in QGIS.
   - Set the desired hexadecimal color code for each layer.
5. CUSTOMIZE THE 'ROAD_TYPE_SCALES' DICTIONARY:
   - Ensure the 'road type' values (keys) exactly match your attribute values.
   - Adjust the scale ranges (minimum_scale, maximum_scale) for each road type.
     Use 0 for no minimum scale (visible at largest scales)
     Use 0 for no maximum scale (visible at smallest scales)
6. If using the editor, save the script (e.g., 'apply_time_slice_road_type_styles.py')
   and then click the 'Run script' button (green play icon).
7. If pasting directly, press Enter to execute.
"""

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRuleBasedRenderer,  # Reverted to rule-based renderer
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
ROAD_TYPE_FIELD_NAME = "road type" # Assuming this is the attribute name

# Define common line width for all layers and road types
COMMON_LINE_WIDTH = 0.6  # Line width in mm

# Define colors for each time slice layer.
# Keys should EXACTLY match your layer names in QGIS.
# Values are "hex_color_code"
LAYER_TIME_SLICES = {
    "Pre 1800 roads": "#A52A2A",     # Brown
    "1800-1860": "#D2691E",          # Chocolate
    "1860-1880": "#FF8C00",          # Dark Orange
    "1880-1900": "#FFD700",          # Gold
    "1900-1920": "#ADFF2F",          # Green Yellow
    "1920-1950": "#32CD32",          # Lime Green
    "1950-1980": "#1E90FF",          # Dodger Blue
    "1980-1995": "#4169E1",          # Royal Blue
    "1995-2025": "#8A2BE2"           # Blue Violet
}

# Define scale visibility for each road type.
# Keys should match the values in your "road type" attribute exactly.
# Values are tuples: (minimum_scale, maximum_scale)
# Use 0 for no minimum scale (visible at largest scales)
# Use 0 for no maximum scale (visible at smallest scales)
# --- CONFIGURATION ---
# Define the field name for road type (case-insensitive check will be performed)
ROAD_TYPE_FIELD_NAME = "Road Type"

# --- SCRIPT LOGIC ---

"""
Applies specific colors to time-slice layers and then applies
scale-dependent visibility based on 'road type' attribute within each layer.
"""
project = QgsProject.instance()
layers = project.mapLayers().values()
processed_layers_count = 0
print("--- Starting apply_combined_styles script ---")
if not layers:
    iface.messageBar().pushWarning("No Layers", "No layers found in the current project.")
    print("No layers found in the current project.")
    exit()

for layer in layers:
    # Only process vector layers
    if isinstance(layer, QgsVectorLayer):
        print(f"Checking layer: {layer.name()}")

        # Check if the layer name is in our time slice configuration
        if layer.name() in LAYER_TIME_SLICES:
            layer_color_hex = LAYER_TIME_SLICES[layer.name()]
            print(f"  Found '{layer.name()}' in time slices config. Preparing styles.")
            processed_layers_count += 1

            # Find the 'road type' field, case-insensitively
            field_index = -1
            for i, field in enumerate(layer.fields()):
                if field.name().lower() == ROAD_TYPE_FIELD_NAME.lower():
                    field_index = i
                    break

            if field_index != -1:
                print(f"    Found '{ROAD_TYPE_FIELD_NAME}' field within layer '{layer.name()}'.")

                # Create a generic base symbol for this layer's color
                geom_type = layer.geometryType()
                base_symbol = None
                if geom_type == QgsWkbTypes.LineGeometry:
                    base_symbol = QgsLineSymbol.createSimple({'color': layer_color_hex,
                                                                'width': str(COMMON_LINE_WIDTH),
                                                                'width_unit': 'mm'})
                elif geom_type == QgsWkbTypes.PointGeometry:
                    base_symbol = QgsMarkerSymbol.createSimple({'color': layer_color_hex,
                                                                'name': 'circle'})
                elif geom_type == QgsWkbTypes.PolygonGeometry:
                    base_symbol = QgsFillSymbol.createSimple({'color': layer_color_hex,
                                                                'outline_width': str(COMMON_LINE_WIDTH),
                                                                'outline_width_unit': 'mm'})
                else:
                    print(f"    Warning: Unknown geometry type for layer {layer.name()}. Defaulting to LineSymbol.")
                    base_symbol = QgsLineSymbol.createSimple({'color': layer_color_hex,
                                                                'width': str(COMMON_LINE_WIDTH),
                                                                'width_unit': 'mm'})

                if base_symbol:
                    # Create the root rule for the rule-based renderer
                    root_rule = QgsRuleBasedRenderer.Rule(base_symbol, '1', 'Root')
                    root_rule.setKey("root") # Assign a key to the root rule

                    # Add rules for each road type, using the layer's specific color
                    for road_type_value, (min_scale, max_scale) in ROAD_TYPE_SCALES.items():
                        expression = f'"{layer.fields()[field_index].name()}" = \'{road_type_value}\''
                        symbol_for_rule = base_symbol.clone() # Clone the base symbol to modify scale

                        rule = QgsRuleBasedRenderer.Rule(
                            f"rule_{road_type_value.replace(' ', '_')}", # Unique ID for the rule
                            road_type_value, # Description for the rule
                            expression,
                            symbol_for_rule
                        )

                        rule.setScaleBasedVisibility(True)
                        rule.setMinimumScale(min_scale)
                        rule.setMaximumScale(max_scale)

                        root_rule.appendChild(rule)

                    # Create the rule-based renderer and apply it to the layer
                    renderer = QgsRuleBasedRenderer(root_rule)
                    layer.setRenderer(renderer)

                    # Refresh the layer symbology in the legend and map canvas
                    layer.triggerRepaint()
                    iface.mapCanvas().refresh()
                    print(f"    Applied combined style (color by time-slice, visibility by road type) to layer: {layer.name()}")
                else:
                    print(f"    Could not create base symbol for layer: {layer.name()}. Skipping styling.")
            else:
                print(f"    Field '{ROAD_TYPE_FIELD_NAME}' not found in layer: {layer.name()}. Skipping road type visibility for this layer.")
        else:
            print(f"  Layer name '{layer.name()}' not found in time slices configuration. Skipping.")

if processed_layers_count > 0:
    iface.messageBar().pushMessage(
        "Script Complete",
        f"Applied combined styles to {processed_layers_count} layers.",
        level=0,  # Info level
        duration=5 # Display for 5 seconds
    )
    print(f"\nScript completed. Applied combined styles to {processed_layers_count} layers.")
else:
    iface.messageBar().pushWarning(
        "Script Complete",
        f"No layers matching the configured time slices were found and processed.",
        level=1, # Warning level
        duration=7 # Display for 7 seconds
    )
    print(f"\nScript completed. No layers matching the configured time slices were found and processed.")


