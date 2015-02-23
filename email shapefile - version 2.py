#-------------------------------------------------------------------------------
# Name: Revised Email Shapefile Script
# Purpose: Incorporate shapefile query into request and email shapefile to user
#
# Author: Jason Piwarski
#
# Created: 2/23/2015
# Copyright:   (c) Jason Piwarski 2015
#-------------------------------------------------------------------------------

import os, arcpy, csv, logging, urllib2, json, sys, smtplib, zipfile, string, random, time
arcpy.env.workspace = "in_memory"
arcpy.env.overwriteOutput = True
from email import Encoders
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

gaugesFile = "C://Users//Admin//Desktop//Crowd Hydrology//scratch_ws//gauges.csv"
scratch_ws = "C://Users//Admin//Desktop//Crowd Hydrology//scratch_ws"
outgoing = "C://Users//Admin//Desktop//Crowd Hydrology//outgoing"
shapefile = "C://Users//Admin//Desktop//Crowd Hydrology//data"

#Delete previous work
def cleanUp():
    try:
        folders = sorted(os.listdir(scratch_ws))
        for folder in folders:
            if os.path.isdir(scratch_ws + os.sep + folder):
                secs_since_modified = time.time() - os.path.getmtime(scratch_ws + os.sep + folder)
            if secs_since_modified > 86400:
                #it's more than one day old
                shutil.rmtree(scratch_ws + os.sep + folder)
    except Exception as e:
        print e.message
        #arcpy.AddMessage(e.message)

def randomID():
    #we have to create a random ID to name the folder where the results will be created
    randid = str(random.randint(1,99999))
    workspace_exists = True
    while workspace_exists:
        if not os.path.exists(scratch_ws + '\\' + randid):
            workspace_exists = False
        else:
            randid = str(random.randint(1,99999))
    runid = randid
    d = time.localtime()
    year = str(d.tm_year)
    month = str(d.tm_mon)
    mday = str(d.tm_mday)
    hour = str(d.tm_hour)
    minutes = str(d.tm_min)
    seconds = str(d.tm_sec)
    if len(month) == 1: month = '0' + month
    if len(mday) == 1: mday = '0' + mday
    if len(hour) == 1: hour = '0' + hour
    if len(minutes) == 1: minutes = '0' + minutes
    if len(seconds) == 1: seconds = '0' + seconds
    runid += '-' + month + '-' + mday + '-' + year + '_' + hour + '-' + minutes + '-' + seconds
    os.mkdir(scratch_ws + '\\' + runid)
    user_ws = scratch_ws + '\\' + runid
    return user_ws

#Create CSV file containing the data for only the stations that were requested
def createCSV(user_ws,start_time,end_time,stations_list):
    with open(gaugesFile, 'rb') as f:
        reader = csv.reader(f)
        next(reader) # Ignore first row
        with open(user_ws + os.sep + 'data.csv', 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            headerwriter = csv.DictWriter(csvfile, fieldnames = ["name","created_at","image", "water_clarity", "water_level"], delimiter = ',')
            headerwriter.writeheader()
            for row in reader:
                name = row[2] #site name
                if name in stations_list:
                    response = urllib2.urlopen(row[1]) #data url = row[1]
                    text = json.loads(response.read())
                    total_results = text["pagination"]["total_results"]
                    for index in range(total_results):
                        created_at = text["data"][index]["created_at"]
                        image = text["data"][index]["image"]
                        water_clarity = text["data"][index]["water_clarity"]
                        water_level = text["data"][index]["water_level"]
                        if created_at > start_time and created_at < end_time: #filter csv to data only within a specific posix timeframe
                            csvwriter.writerow([name,image,water_clarity,water_level])

#Create a shapefile containing the data for only the stations that were requested
def queryShapefile(user_ws,stations_list):
    arcpy.MakeFeatureLayer_management(shapefile + os.sep + "gauges.shp","gauges_lyr")
    for station in stations_list:
        arcpy.SelectLayerByAttribute_management("gauges_lyr", "ADD_TO_SELECTION", '"name" = ' + "'" + station + "'") #SQL formatting must look the same as it does in ArcMap
    # Write the selected features to a new featureclass
    arcpy.CopyFeatures_management("gauges_lyr", user_ws + os.sep + "gauges.shp")

def zip(src, dst):
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            fileExtension = filename.split('.')[1]
            if fileExtension != 'zip': #don't want to zip .zip files
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zf.write(absname, arcname)
    zf.close()

def send_email_with_attachment(subject, host, from_addr, body_text, emails, file_to_attach):
    #Name the attachment here
    header = 'Content-Disposition', 'attachment; filename=gauges.zip'
    # create the message
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    if body_text:
        msg.attach( MIMEText(body_text) )
    msg["To"] = ', '.join(emails)
    attachment = MIMEBase('application', "octet-stream")
    try:
        with open(file_to_attach, "rb") as fh:
            data = fh.read()
        attachment.set_payload(data)
        Encoders.encode_base64(attachment)
        attachment.add_header(*header)
        msg.attach(attachment)
    except IOError:
        msg = "Error opening attachment file %s" % file_to_attach
        print msg
        sys.exit(1)
    server = smtplib.SMTP(host)
    server.ehlo()
    server.starttls()
    server.login("mmhiatoolkit", "MMHIA2014")
    server.sendmail(from_addr, emails, msg.as_string())
    server.quit()

if __name__ == '__main__':
    #start_time = sys.argv[1] #e.g. 1234567899
    #end_time = sys.argv[2] #e.g. 1234567990
    #stations_list = sys.argv[3] #e.g. ['NY1000','WI1005','NY1008']
    start_time = 1321368689
    end_time = 1416947601
    stations_list = ['NY1000','WI1005','NY1008']

    user_ws = randomID()
    createCSV(user_ws,start_time,end_time,stations_list)
    queryShapefile(user_ws,stations_list)
    zip(user_ws, user_ws + os.sep + 'data')

    #Email function parameters
    host = "smtp.gmail.com:587"
    from_addr = "mmhiatoolkit@gmail.com"
    #emails = sys.argv[4] #e.g. "jasonpiwarsk1@gmail.com"
    emails = "jasonpiwarsk1@gmail.com"
    subject = "Test email with attachment from Python"
    body_text = "This email contains an attachment!"
    file_to_attach = user_ws + os.sep + "data.zip"
    send_email_with_attachment(subject, host, from_addr, body_text, emails, file_to_attach)

    #Delete old data requests
    cleanUp()
    print 'done'
