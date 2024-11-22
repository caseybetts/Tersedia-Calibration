# Author: Casey Betts, 2024
# This file contains the function for isolating the available orders for today and tomorrow's revs

import arcpy
import json
import os
import shutil


class Tersedia():
    """ Creates shapefiles of accessible calibration orders for each spacecraft """

    def __init__(self, path):

        # Load .json file with parameters
        with open('config.json', 'r', errors="ignore") as file:
            configs = json.load(file)

        # Define the sharepoint and local locations location if applicable
        self.staging_location = os.path.join(path, configs["staging_name"])
        self.output_location = os.path.join(path, configs["output_name"])

        # Define variables
        self.map = arcpy.mp.ArcGISProject("CURRENT").activeMap
        self.scids = configs["scids"]
        self.onv_layer_source = configs["onv_layer_source"]

        # Define feature layers
        self.orders_layer = self.find_layer_by_source(configs["orders_layer_source"] + "\\" + configs["orders_layer_name"], "")
        self.original_orders_layer_query = self.orders_layer.definitionQuery
        self.orders_layer.definitionQuery = configs["orders_layer_query"]
        
        # run main program
        self.iterate()
        self.cleanup()

    def find_layer_by_source(self, source_path, query_req):
        """ Returns a layer of the given source and name

        :param source_path: String, Url to the geoserver location
        :param query_req: String, an SQL query expression
        """

        # Loop through layers looking for matching URL and Name
        for layer in self.map.listLayers():
            arcpy.AddMessage(str(layer.name))
            try:
                desc = arcpy.Describe(layer)
                query = layer.listDefinitionQueries()[0]

                # Return the layer if Url matches the given path and the query requirement is in the query
                # (the onv layers will have a query specifying the day)
                if desc.catalogPath == source_path and query_req in query['sql']:
                    return layer

            except:
                continue

        return None

    def get_selected(self, layer, field):
        """ Returns a list of order ids from the given layer that are currently selected 
        
        :param layer: Feature Layer, the layer with the selection
        :param field: String, the field from which to gather the values from selected rows
        """

        desc = arcpy.Describe(layer)
        oid_field = desc.OIDFieldName 

        # Create a list of selected rows
        with arcpy.da.SearchCursor(layer, [oid_field]) as cursor:
            selected_ids = [str(row[0]) for row in cursor]

        selected_values = []
        # Create a list of values from the given field
        with arcpy.da.SearchCursor(layer, [oid_field, field]) as cursor:
            for row in cursor:
                selected_values.append(row[1])

        return selected_values

    def select_orders_by_ona(self, orders_layer, onv_layer):
        """ Select orders accessable based on the order's max ONA vlaue with the given onv layer
        
        :param orders_layer: Feature Layer, layer of orders to select from
        :param onv_layer: Feature Layer, layer of spacecraft onv to intersect the orders layer 
        """

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

    def select_orders_by_sun_el(self, orders_layer, onv_layer):
        """ Select orders accessable based on the order's min sun el vlaue with the given onv layer
        
        :param orders_layer: Feature Layer, layer of orders to select from
        :param onv_layer: Feature Layer, layer of spacecraft onv to intersect the orders layer 
        """
        sun_els = [10, 15, 30]

        # Select orders intersecting the entire onv layer
        arcpy.management.SelectLayerByLocation(orders_layer, "INTERSECT", onv_layer, None, "NEW_SELECTION")

        for sun_el in sun_els:

            # Deselect orders with sun el above current value
            arcpy.management.SelectLayerByAttribute(orders_layer, "REMOVE_FROM_SELECTION", "min_sun_elevation > " + str(sun_el), None)

            # Create a sun el feature
            feature_layer = arcpy.management.MakeFeatureLayer(onv_layer, "FeatureLayer", f"sun_el > {sun_el}")

            # Select orders intersecting the current sun el feature layer
            arcpy.management.SelectLayerByLocation(orders_layer, "INTERSECT", feature_layer, None, "ADD_TO_SELECTION")

    def delete_files(self, folder):
        """ 
        Deletes out the files in the given folder

        :param folder: String, the path to the folder of files to delete 
        """

        for file in os.listdir(folder):
            file_path = os.path.join(folder,  file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    arcpy.AddMessage(f"Deleted: {file}")
                except:
                    arcpy.AddMessage(f"Could not delete: {file}")
                    continue

    def move_files(self, source_folder, target_folder):
        """ 
        Moves all files in a given folder to the given output folder  

        :param souce_folder: String, the path of the folder to move files from
        "param target_folder: String, the path of the folder to move files to  
        """

        for file in os.listdir(source_folder):
            source_path = os.path.join(source_folder, file)
            dest_path = os.path.join(target_folder, file)
            shutil.move(source_path, dest_path)

    def produce_shape(self, scid, day):
        """ Identifies the accessible orders based on the given spacecraft and day and exports a shapefile of these orders to a location 
        
        :param scid: String, the spacecraft ID
        :param day: Integer, the given day to assess; 0 = today, 1 = tomorrow 
        """

        # Get the onv layer
        onv_source = self.onv_layer_source + "\\" + f"onv_{scid}"
        onv_layer = self.find_layer_by_source(onv_source, f'days = {day}')
        
        # Create list of orders available by scid
        arcpy.management.SelectLayerByAttribute(self.orders_layer, "NEW_SELECTION", scid + " = 1", None)
        available_by_scid = self.get_selected(self.orders_layer, 'external_id')

        # Create list of orders available by ONA
        self.select_orders_by_ona(self.orders_layer, onv_layer)
        available_by_ona = self.get_selected(self.orders_layer, 'external_id')

        # Create list of orders available by sun el
        self.select_orders_by_sun_el(self.orders_layer, onv_layer)
        available_by_sun_el = self.get_selected(self.orders_layer, 'external_id')

        # Create list of the intersection of scid and ONA
        intersect_1 = [value for value in available_by_scid if value in available_by_ona]

        # Create list of intersection of previous union and sun el
        accessible_orders = [value for value in intersect_1 if value in available_by_sun_el]

        # Select orders by order id
        if accessible_orders:
            criteria = "external_id IN (" + ",".join("'" + str(x) + "'" for x in accessible_orders)+ ")"
            arcpy.AddMessage(criteria)
        else:
            criteria = "external_id IN ('0')"

        # Determine naming label based on day
        if day == 0:
            day = "today"
        elif day == 1:
            day = "tomorrow"

        # Create output shapefile in staging location
        outtput = os.path.join(self.staging_location, f"available_on_{scid}_{day}")
        arcpy.conversion.ExportFeatures(self.orders_layer, outtput, criteria)

    def iterate(self):
        """ This function iterates through the spacecrafts and days calling the function to produce the shapefiles
        """

        # Loop throuhg each spacecraft and produce the 
        for scid in self.scids:

            for day in [0,1]:

                self.produce_shape(scid, day)

    def cleanup(self):
        """ Thid function takes the final actions needed including moving the shapefiles from the staging location to the final location 
        """

        # Set the orders layer definition query back to the original
        self.orders_layer.definitionQuery = self.original_orders_layer_query
        
        # Delete current files in output location
        self.delete_files(self.output_location)

        # Move files from staging location to output location
        self.move_files(self.staging_location, self.output_location)


        
