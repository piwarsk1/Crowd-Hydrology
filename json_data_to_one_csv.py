#-------------------------------------------------------------------------------
# Name: JSON to data table
# Purpose: Read JSON formatted data for each station and create one data.csv
#          file
#
# Author: Jason Piwarski
#
# Created:     29/01/2015
# Copyright:   (c) Jason Piwarski 2015
#-------------------------------------------------------------------------------

import os, arcpy, csv, logging, urllib2, json
baseURL = "http://crowdhydrology.geology.buffalo.edu:8040/api/data/"
gaugesFile = "C:\Users\Admin\Desktop\Crowd Hydrology\scratch_ws\gauges.csv"
scratch_ws = "C:\Users\Admin\Desktop\Crowd Hydrology\scratch_ws"

def main():
    with open(gaugesFile, 'rb') as f:
        reader = csv.reader(f)
        next(reader) # Ignore first row
        with open(scratch_ws + os.sep + 'data.csv', 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            headerwriter = csv.DictWriter(csvfile, fieldnames = ["name","created_at","image", "water_clarity", "water_level"], delimiter = ',')
            headerwriter.writeheader()
            for row in reader:
                name = row[2] #site name
                response = urllib2.urlopen(baseURL + name)
                text = json.loads(response.read())
                total_results = text["pagination"]["total_results"]
                for index in range(total_results):
                    created_at = text["data"][index]["created_at"]
                    image = text["data"][index]["image"]
                    water_clarity = text["data"][index]["water_clarity"]
                    water_level = text["data"][index]["water_level"]
                    csvwriter.writerow([name,image,water_clarity,water_level])

if __name__ == '__main__':
    main()
    print 'done'
