import os, arcpy, csv, logging, urllib2, json
import xml.dom.minidom as DOM
scratch_ws = "C:\Users\Admin\Desktop\Crowd Hydrology\scratch_ws"
data = "C:\Users\Admin\Desktop\Crowd Hydrology\data"
arcpy.env.overwriteOutput = True
arcpy.env.workspace = "in_memory"
logging.basicConfig(filename= scratch_ws + os.sep + 'history.log', level=logging.INFO)
logging.info('Started')

#Load contents from Buffalo server in JSON format
pageURL = 'http://crowdhydrology.geology.buffalo.edu:8040/api/stations'
response = urllib2.urlopen(pageURL)
text = json.loads(response.read())
total_results = text["pagination"]["total_results"] #total number of stations. This will inform us about how many rows we need to make in the csv file.

#Create csv file from JSON contents
with open(scratch_ws + os.sep + 'gauges.csv', 'wb') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    headerwriter = csv.DictWriter(csvfile, fieldnames = ["id","data_url","name", "POINT_X", "POINT_Y",\
                                                         "name","online","state"], delimiter = ',')
    headerwriter.writeheader()
    for index in range(total_results):
        data_url = text["data"][index]["data_url"]
        station_id = text["data"][index]["id"]
        latitude = text["data"][index]["latitude"]
        longitude = text["data"][index]["longitgude"]
        name = text["data"][index]["name"]
        online = text["data"][index]["online"]
        state = text["data"][index]["state"]
        csvwriter.writerow([str(id_counter),data_url,station_id,longitude,latitude,name,online,state])

#Create a new stream gauges shapefile
print "Creating shapefile from .csv file"
logging.info('Creating shapefile from .csv file')
sr = "C:\Users\Admin\Desktop\Crowd Hydrology\projection\GCS_WGS_1984.prj"
arcpy.MakeXYEventLayer_management(scratch_ws + os.sep + 'gauges.csv', "POINT_X", "POINT_Y", "temp_layer", sr)
arcpy.CopyFeatures_management("temp_layer", data + os.sep + "gauges.shp")
desc = arcpy.Describe(data + os.sep + "gauges.shp")
gauges_extent = desc.extent

#Create stage definition draft
print "Creating stage definition draft"
logging.info('Creating stage definition draft')
mapDoc = arcpy.mapping.MapDocument("C:\Users\Admin\Desktop\Crowd Hydrology\map\map.mxd")
mapDoc.activeDataFrame.extent = gauges_extent
sddraft = scratch_ws + os.sep + 'crowd_hydro.sddraft'
summary = 'Crowd Hydrology Map Service'
tags = 'water, streamflow, crowd sourcing'
#draft = arcpy.mapping.CreateMapSDDraft(mapDoc, sddraft, "crowdHydrology", 'ARCGIS_SERVER', con, True, None, summary, tags)
draft = arcpy.mapping.CreateMapSDDraft(mapDoc, sddraft, "crowdHydrology", 'ARCGIS_SERVER')

#Stage and upload the service if the sddraft analysis did not contain errors
if draft['errors'] == {}:
    #Configure sddraft file to overwrite the existing service
    newType = 'esriServiceDefinitionType_Replacement'
    xml = draftPath + in_sddraft
    doc = DOM.parse(xml)
    descriptions = doc.getElementsByTagName('Type')
    for desc in descriptions:
        if desc.parentNode.tagName == 'SVCManifest':
            if desc.hasChildNodes():
                desc.firstChild.data = newType
    outXml = xml
    f = open(outXml, 'w')
    doc.writexml( f )
    f.close()
    #Create service definition
    print "Staging service"
    logging.info('Staging service')
    sd = scratch_ws + os.sep + "crowd_hydro.sd"
    arcpy.StageService_server(sddraft, sd)
    in_server = "C:/Users/Administrator/AppData/Roaming/ESRI/Desktop10.1/ArcCatalog/arcgis on GISSERVER2_6080 (publisher).ags"
    arcpy.UploadServiceDefinition_server(sd, in_server)
else:
    #If the sddraft analysis contained errors, display them
    print draft['errors']

print "Finished"
logging.info('Finished')
