# Tersedia - Calibration

## Description
This tool produces four outputs which contain the current calibration orders available to collect on a specific satellite on a specific day. The four outputs are the combinations of LG01 and LG02 spacecraft with today or tomorrow's groundtracks. 
The user has the option for the results to be output to their local geodatabase or to a shapefile in a shared location or both. Output to a local database will automatically add the data to the map and with the symbology of the input layer. Output to the shared location will replace
the current files so that layer source connections will not be broken.

## How to use
In the ArcPro Catalog pane create a file connection to the folder. Open the toolbox dropdown and double click the tool. When the tool opens in the Geoprocessing pane the user has the option to choose Local (output to defalut geodatabase) or SharePoint (output to the shared
folder location) or both. By default it will output to the SharePoint location. Then click 'Run'.

## Requirements
The tool will require inputs of the orders layer and the satellite onv layers. A layer file with layers can be found in the same folder. Once this is loaded, no other input is needed, but be sure to make sure the layers are functional. 

## Alterations
This tool can be used for more general purposes. The specific customer for calibration is queried for within the input orders layer. If you desire to know the accessible orders for a different customer, for all customers, or any other criteria, simply edit the definition 
query in the input layer. Likewise, editing the input onv layers can produce results for a different day (change from 'days = 1' to 'days = 4' for example). In this case it is strongly recommended to not use the SharePoint option as this would result other users seeing 
results that they may not be expecting.
