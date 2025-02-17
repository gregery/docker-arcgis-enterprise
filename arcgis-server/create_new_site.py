#
#  Send a very generic request to configure a site to ArcGIS Server.
#
#  This returns a response almost instantly but site creation takes
#  longer. You can test if from the host (you don't need
#  to be inside the docker container to run it) but hostname
#  has to resolve correctly. Also it probably silently fails... :-)
#
# See example:  http://server.arcgis.com/en/server/latest/administer/linux/example-create-a-site.htm
#
from __future__ import print_function
import os
import requests
import json

# HTTPS calls will generate warnings about the self-signed certificate if you delete this.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

hostname = "server" # localhost would almost always work here I think

class arcgis(object):

    defaultdir = "/home/arcgis/server/usr"

    def __init__(self):
        return

    def create_site(self, user, passwd):

        configstorepath = os.path.join(self.defaultdir,"config-store")
        configstoreJSON = json.dumps({"connectionString":configstorepath, "type":"FILESYSTEM"})

        # Set up paths for server directories             
        cacheDirPath = os.path.join(self.defaultdir, "arcgiscache")
        jobsDirPath = os.path.join(self.defaultdir, "arcgisjobs")
        outputDirPath = os.path.join(self.defaultdir, "arcgisoutput")
        systemDirPath = os.path.join(self.defaultdir, "arcgissystem")
    
        cacheDir = dict(name = "arcgiscache",physicalPath = cacheDirPath,directoryType = "CACHE",cleanupMode = "NONE",maxFileAge = 0,description = "Stores tile caches used by map, globe, and image services for rapid performance.", virtualPath = "")    
        jobsDir = dict(name = "arcgisjobs",physicalPath = jobsDirPath, directoryType = "JOBS",cleanupMode = "TIME_ELAPSED_SINCE_LAST_MODIFIED",maxFileAge = 360,description = "Stores results and other information from geoprocessing services.", virtualPath = "")
        outputDir = dict(name = "arcgisoutput",physicalPath = outputDirPath,directoryType = "OUTPUT",cleanupMode = "TIME_ELAPSED_SINCE_LAST_MODIFIED",maxFileAge = 10,description = "Stores various information generated by services, such as map images.", virtualPath = "")
        systemDir = dict(name = "arcgissystem",physicalPath = systemDirPath,directoryType = "SYSTEM",cleanupMode = "NONE",maxFileAge = 0,description = "Stores files that are used internally by the GIS server.", virtualPath = "")
 
        # Serialize directory information to JSON    
        directoriesJSON = json.dumps(dict(directories = [cacheDir, jobsDir, outputDir, systemDir]))
    
        # Form contents gleaned from ESRI ArcGIS Chef Cookbooks in Github.

        log_level = "INFO"
        
        log_settings = {
            'logLevel' : log_level,
            'logDir'   : os.path.join(self.defaultdir, "logs"),
            'maxErrorReportsCount' : 30,
            'maxLogFileAge' : 100,  # I wonder what units... seconds? centuries?
        }
        log_settingsJSON = json.dumps(log_settings)

        form_data = {
            "username"              : user,
            "password"              : passwd,
            "configStoreConnection" : configstoreJSON,
            "directories"           : directoriesJSON,
            "settings"              : log_settingsJSON,
            "cluster"  : "",
            "f"        : "json"
        }

        uri = "https://%s:6443/arcgis/admin/createNewSite" % hostname

        response = None
        try:
            response = requests.post(uri, data=form_data,
                                     timeout=30, verify=False # allow self-signed certificate
            )
        except Exception as e:
            print("Error:",e)
            print("A timeout here might not mean anything. Try accessing your server.")
            return False

        if response.status_code != 200:
            print("Server not available; code ", r.status_code)
            return False

        rj = json.loads(response.text)
        if rj["status"]=="error":
            print("\n".join(rj["messages"]))
            return False
        
        return True

# ------------------------------------------------------------------------

if __name__ == "__main__":

    try:
        u = os.environ["AGE_USER"]
        p = os.environ["AGE_PASSWORD"]
    except KeyError:
        u = "siteadmin"
        p = "changeit"
        print("Using default username and password.")

    ag = arcgis()
    if ag.create_site(u,p):
        print("Site created.")

    print("https://localhost:6443/arcgis/manager/")

# That's all!
