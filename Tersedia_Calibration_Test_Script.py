# Author: Casey Betts, 2024
# This file contains the function for isolating the available orders for today and tomorrow's revs

import arcpy

# Create feature class of available orders
def select_available_orders(orders_layer, onv_layer, scid):
    """ Select orders accessable on a given rev based on the order's max ONA vlaue """

    arcpy.AddMessage(f"Running available_orders for {scid}.....")

    # Definition query values
    ona_values = [35, 30, 25, 20, 15]
    
    # Select orders intersecting the 45deg segments of the rev (max selection)
    arcpy.management.SelectLayerByLocation(orders_layer, "INTERSECT", onv_layer, None, "NEW_SELECTION")

    # Select only the orders that are avaialble based on their max ONA value    
    for ona in ona_values:

        # Deselect orders with ONA under current value
        arcpy.management.SelectLayerByAttribute(orders_layer, "REMOVE_FROM_SELECTION", "max_ona < " + str(ona + 1), None)

        # Create an onv feature
        feature_layer = arcpy.management.MakeFeatureLayer(onv_layer, "FeatureLayer", f"ona = {ona}")

        # Select orders intersecting the current onv feature layer
        arcpy.management.SelectLayerByLocation(orders_layer, "INTERSECT", feature_layer, None, "ADD_TO_SELECTION")

    # Deselect orders that do not use the spacecraft consitant with the onv
    arcpy.management.SelectLayerByAttribute(orders_layer, "REMOVE_FROM_SELECTION", scid + " = 0", None)

    arcpy.AddMessage("Done")

def run(local, sharepoint):
    """ This function controls what is run by the tool """

    # Get the active map document and data frame
    project = arcpy.mp.ArcGISProject("CURRENT")
    map = project.activeMap
    current_workspace = arcpy.env.workspace
    sharepoint_location = r"C:\Users\ca003927\OneDrive - Maxar Technologies Holdings Inc\Private Drop\Git\Tersedia-Calibration\Shapefile_Output"

    # Save the order layer and it's symbology in a variable
    orders_layer = map.listLayers("Calibration_Orders_Tersedia")[0]
    orders_layer_symbology = orders_layer.symbology

    # List of onv layer names
    onv_layer_names = [ "lg01_today_onv_Tersedia", 
                        "lg01_tomorrow_onv_Tersedia", 
                        "lg02_today_onv_Tersedia", 
                        "lg02_tomorrow_onv_Tersedia"]

    # Create a dictionary of: { onv layer name: onv layer }
    onv_dict = {k: map.listLayers(k)[0] for k in onv_layer_names}
    
    # Create and export a feature class of available ordres for each ona layer in the list
    for onv in onv_dict:

        # Get the text before the second underscore in the layer name
        split_name = onv.split('_')
        scid = split_name[0]
        output_name = "available_orders_" + '_'.join(split_name[:2])

        # Select the orders available on the given spacecraft and day
        select_available_orders(orders_layer, onv_dict[onv], scid)

        # Export to desired location(s)
        if sharepoint:
            arcpy.conversion.ExportFeatures(orders_layer, sharepoint_location + "\\" + output_name)

            if local:
                arcpy.conversion.ExportFeatures(orders_layer, current_workspace + "\\" + output_name)

        else:
            arcpy.conversion.ExportFeatures(orders_layer, current_workspace + "\\" + output_name)

        # Add the feature layer to the map
        map.addDataFromPath(current_workspace + "\\" + output_name)

        # Save the layer just added to the map in a variable
        map.listLayers()[0].symbology = orders_layer_symbology
