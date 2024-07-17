# Author: Casey Betts, 2024
# This file contains the function for isolating the available orders for today and tomorrow's revs

import arcpy
import json
import os
import shutil

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

def create_order_layers(local, sharepoint_location, orders_layer_name, onv_layer_names):
    """ Create feature classes of available orders and add them to the map """
    
    # Get the active map document and data frame
    project = arcpy.mp.ArcGISProject("CURRENT")
    map = project.activeMap
    output_file_names = []

    # Save the order layer and it's symbology in a variable
    orders_layer = map.listLayers(orders_layer_name)[0]
    orders_layer_symbology = orders_layer.symbology

    # Create a dictionary of: { onv layer name: onv layer }
    onv_dict = {k: map.listLayers(k)[0] for k in onv_layer_names}
    
    # Create and export a feature class of available ordres for each ona layer in the list
    for onv in onv_dict:

        # Get the text before the second underscore in the layer name
        split_name = onv.split('_')
        scid = split_name[0]
        output_name = "available_orders_" + '_'.join(split_name[:2])
        output_file_names.append(output_name)


        # Select the orders available on the given spacecraft and day
        select_available_orders(orders_layer, onv_dict[onv], scid)

        # Export to desired location(s) and add to the map if local
        if sharepoint_location:
            # Export as a shapefile to the sharepoint location
            arcpy.conversion.ExportFeatures(orders_layer, sharepoint_location + "\\" + output_name)

            if local:
                # Export as a feature class in the default geodatabase
                arcpy.conversion.ExportFeatures(orders_layer, local + "\\" + output_name)
                            
                # Add the feature layer to the map and apply symbology
                map.addDataFromPath(local + "\\" + output_name)
                map.listLayers()[0].symbology = orders_layer_symbology

        else:
            # Export as a feature class in the default geodatabase
            arcpy.conversion.ExportFeatures(orders_layer, local + "\\" + output_name)

            # Add the feature layer to the map and apply symbology
            map.addDataFromPath(local + "\\" + output_name)
            map.listLayers()[0].symbology = orders_layer_symbology


    return output_file_names

def delete_current_files(file_location, file_names):
    """ Deletes out the current files in the folder """

    for file in file_names:
        file_path = os.path.join(file_location,  file)
        if os.path.exists(file_path):
            os.remove(file_path)
            arcpy.AddMessage(f"Deleted: {file}")

def move_new_files(staging_location, output_location, file_names):
    """ Moves the newly generated files to the output folder """

    for file in os.listdir(staging_location):
        source_path = os.path.join(staging_location, file)
        dest_path = os.path.join(output_location, file)
        shutil.move(source_path, dest_path)
        arcpy.AddMessage(f"Moved: {file}")


def run(local, sharepoint):
    """ This function controls what is run by the tool """

    # Load .json file with parameters
    with open('config.json', 'r', errors="ignore") as file:
        configs = json.load(file)

    # Define the sharepoint and local locations location if applicable
    if sharepoint: 
        staging_location = configs["staging_location"]
        output_location = configs["output_location"]
    if local: local = arcpy.env.workspace

    # Define the file names
    orders_layer_name = configs["orders_layer_name"]
    onv_layer_names = configs["onv_layer_names"]

    # Create the order layers and save the outputed file names to a list 
    file_names = create_order_layers(local, 
                        staging_location, 
                        orders_layer_name, 
                        onv_layer_names)
    
    # Creating a list of file names
    file_types = ['.cpg', '.dbf', '.prj', '.sbn', '.sbx', '.shp', '.shp.xml', '.shx']
    all_files = [f"{name}{type}" for name in file_names for type in file_types]
    
    delete_current_files(output_location, all_files)

    move_new_files(staging_location, output_location, all_files)



    
