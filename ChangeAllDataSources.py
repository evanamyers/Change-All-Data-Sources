"""
This script will change the sources of all the layers that share the same database as
the input layer (referenced as 'inDb_conn' below) to a specified
database (referenced as 'outDB_conn' below).
"""


def splitWord(pickedDB_Split, db):
    changeDB = re.sub(r'[^a-zA-Z0-9]', '_', pickedDB_Split)
    sourceDB = re.sub(r'[^a-zA-Z0-9]', '_', db)
    if changeDB == sourceDB:
        return True


def check_currDB_path():

    currDBPath = None
    if '.sde' in Database_to_Change:
        for db in dbList:
            if splitWord(changeDB_Split, db.lower()):
                dbPath = os.path.join(dbFolder, db)
                dbworkspace = dbPath.split('.sde')[0] + '.sde'
                currDBWS = arcpy.Describe(dbworkspace)
                currDBPath = currDBWS.catalogPath
                print('The "Current Path" exists in the W:\\GIS\\Database Connections folder.')
                break

    if '.gdb' in Database_to_Change:
        print('The "Current Path" is not in W:\\GIS\\Database Connections, trying something else')
        for lyr in lyrList:
            if lyr.isFeatureLayer and not lyr.isGroupLayer:
                lyrdesc = arcpy.Describe(lyr)
                lyrdescPath = lyrdesc.catalogPath
                lyrworkspace = lyrdescPath.split('.gdb')[0] + '.gdb'
                if Database_to_Change in lyrworkspace:
                    currDBPath = lyrworkspace
                    break

    if currDBPath:
        arcpy.AddMessage(f"The starting database exists")
    else:
        arcpy.AddError('The "Current Path" does not exist in the W:\\GIS\\Database Connections folder.'
                       '  This tool cannot work with unknown databases.')
    return currDBPath


def changeSoucePaths(currDBPath):

    # Feature Classes in new Database:
    newFCList = []
    arcpy.env.workspace = New_Database
    datasets = arcpy.ListDatasets(feature_type='Feature')
    datasets = [''] + datasets if datasets is not None else []
    for ds in datasets:
        for fc in arcpy.ListFeatureClasses(feature_dataset=ds):
            fcName = fc.split('.')[-1]
            newFCList.append(fcName)

    # Make a list of all the layers that are in the database listed in the "Database Source to Change" parameter
    # Note: These layers may be changed if another with the same name is found in the new database
    newDBdescWS = arcpy.Describe(New_Database)
    newDBPath = newDBdescWS.catalogPath
    currDBdescWS = arcpy.Describe(currDBPath)
    currDBcp = currDBdescWS.connectionProperties
    currDBcpServer = currDBcp.server.lower()
    currDBcpDB = currDBcp.database.lower()
    for lyr in lyrList:
        if lyr.isFeatureLayer:
            try:
                lyrdesc = arcpy.Describe(lyr)
                if lyrdesc.Name.split('.')[-1] in newFCList:
                    lyrdescPath = lyrdesc.catalogPath
                    dbPath = os.path.dirname(os.path.dirname(lyrdescPath))
                    # if currDBPath in dbPath:

                    def changedb():
                        lyrName = lyrdesc.featureClass.name.split('.')[-1]
                        if lyrName in newFCList:
                            print(f'{lyr.longName}, changing source.\n')
                            arcpy.AddMessage(f'{lyr.longName}, changing source.\n')
                            lyr.updateConnectionProperties(dbPath, newDBPath)
                    if ".sde" in dbPath:
                        dbPathdescWS = arcpy.Describe(dbPath)
                        dbPathcp = dbPathdescWS.connectionProperties
                        dbPathcpServer = dbPathcp.server.lower()
                        dbPathcpDatabase = dbPathcp.database.lower()
                        if dbPathcpServer == currDBcpServer and dbPathcpDatabase == currDBcpDB:
                            changedb()
                    else:
                        changedb()
            except (OSError, AttributeError):
                pass


if __name__ == '__main__':

    import arcpy
    import re
    import os

    aprx = arcpy.mp.ArcGISProject('current')
    currentMap = aprx.activeMap
    lyrList = currentMap.listLayers()

    for lyr in lyrList[:]:
        if lyr.isFeatureLayer and not lyr.isGroupLayer:
            continue
        else:
            lyrList.remove(lyr)

    Database_to_Change = arcpy.GetParameterAsText(0)
    changeDB_Split = os.path.basename(Database_to_Change).lower()
    New_Database = arcpy.GetParameterAsText(1)
    newDB_Split = os.path.basename(New_Database).lower()


    arcpy.AddMessage(changeDB_Split)
    arcpy.AddMessage(newDB_Split)

    dbFolder = "W:\\GIS\\Database Connections"  # change to folder that contains sde connections
    dbList = os.listdir(dbFolder)

    currDBPath = check_currDB_path()
    # newDBPath = check_newDB_path()
    changeSoucePaths(currDBPath)

"""
As of 5/21/2024, Pro version 3.3.0, Python 3.11
NOTE:  The weirdo tempfile that is made for each feature layer can be used to get connection properties
        and will work when changing connections.  **lyr.updateConnectionProperties(lyrworkspace, newDBPath)**

Script Tool's validation:

def initializeParameters(self):
    # Customize parameter properties. This method gets called when the
    # tool is opened.
        arcpy.env.overwriteOutput = True
        
        aprx = arcpy.mp.ArcGISProject('current')
        currentMap = aprx.activeMap
        lyrList = currentMap.listLayers()
        currentConns = []
        for lyr in lyrList:
            if lyr.isFeatureLayer:
                try:
                    lyrdesc = arcpy.Describe(lyr)
                    lyrdescPath = lyrdesc.catalogPath
                    if '.gdb' in lyrdescPath:
                        lyrworkspace = lyrdescPath.split('.gdb')[0] + '.gdb'
                        gdb = lyrworkspace.split('\\')[-1]
                        lyrConn = gdb
                        print(gdb)
                    elif '.sde' in lyrdescPath:
                        lyrworkspace = lyrdescPath.split('.sde')[0] + '.sde'
                        lyrdescWS = arcpy.Describe(lyrworkspace)
                        lyrcp = lyrdescWS.connectionProperties
                        print(f'{lyr.longName} {lyrcp.server}_{lyrcp.database}_{lyrcp.authentication_mode}')
                        lyrConn = f'{lyrcp.server}_{lyrcp.database}_{lyrcp.authentication_mode}' + '.sde'
                            
                    else:
                        continue
        
                    if lyrConn not in currentConns:
                        currentConns.append(lyrConn)
                except (AttributeError, OSError):
                    pass
        self.params[0].filter.list = currentConns
        
        # dbFolder = "W:\\GIS\\Database Connections"
        # itemList = os.listdir(dbFolder)
        # sdeConns = []
        # for each in itemList:
        #     if '.sde' in each:
        #         conn = os.path.basename(each)
        #         sdeConns.append(conn)
        # self.params[1].filter.list = currentConns + sdeConns
    
    return
"""

