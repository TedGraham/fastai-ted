from requests import exceptions
import argparse
import requests
from PIL import Image
from PIL import UnidentifiedImageError
import os

# Script requires EITHER --query (for command line use) or --keywords-file (for querying a list of keywords)
argumentParser = argparse.ArgumentParser(description="query bing image search and download the resulting images to the output directory")
argumentGroup = argumentParser.add_mutually_exclusive_group(required=True)
argumentGroup.add_argument("--query", help="search query to search Bing Image API for, group multiword searches with quotes")
argumentGroup.add_argument("--file", help="file with one or more keywords per line")
argumentParser.add_argument("--apikey", required=True, help="Microsoft Cognitive Services API key, find yours at https://azure.microsoft.com/en-us/try/cognitive-services/my-apis/")
argumentParser.add_argument("--output", required=True, help="output directory, image files will be created in this directory")
args = argumentParser.parse_args()

# if the output directory doesn't exist, create it
outputDirectory = args.output
if not os.path.exists( outputDirectory ):
  os.makedirs( outputDirectory )

# for a query we are only doing one search, for a file we might have many items.  Either way,
# build the list of terms we want to search
if args.query is not None:
    searchList = [args.query]
else:
    with open(args.file) as f:
        searchList = [line.strip() for line in f]

# set the endpoint API URL and the user provided Microsoft Cognitive Services API key
URL = "https://api.cognitive.microsoft.com/bing/v7.0/images/search"
headers = {"Ocp-Apim-Subscription-Key" : args.apikey}
# (1) the maximum number of results for a given search and 
# (2) the group size for results (maximum of 50 per request)
MAX_RESULTS = 100
GROUP_SIZE = 50

print("[INFO] Performing {} search(es), downloading a maximum of {} files for each search".format(len(searchList), MAX_RESULTS))

for term in searchList:
    params = {"q": term, "offset": 0, "count": GROUP_SIZE}
    search = requests.get(URL, headers=headers, params=params)
    search.raise_for_status()
    # grab the results from the search, including the total number of estimated results returned by the Bing API
    results = search.json()
    totalEstimatedMatches = min(results["totalEstimatedMatches"], MAX_RESULTS)
    print("[INFO] Bing API found {} results for '{}'".format(totalEstimatedMatches, term))

    # for each search term, we combine the search terms with _ to make a filename prefix and we track the highest filename number we have used to avoid overwriting
    filenamePrefix = "_".join(term.split(" "))
    filenameNumber = 1

    # loop over the estimated number of results in `GROUP_SIZE` groups
    for offset in range(0, totalEstimatedMatches, GROUP_SIZE):
        # update the search parameters using the current offset, then make the request to fetch the results
        print("[INFO] making request for group {}-{} of {}...".format(offset, offset + GROUP_SIZE, totalEstimatedMatches))
        params["offset"] = offset
        search = requests.get(URL, headers=headers, params=params)
        search.raise_for_status()
        results = search.json()
        print("[INFO] saving images for group {}-{} of {}...".format(offset, offset + GROUP_SIZE, totalEstimatedMatches))
            
        # loop over the results
        for v in results["value"]:
            try:
                # we only want jpg images
                extension = v["contentUrl"][v["contentUrl"].rfind("."):]
                if extension != ".jpg":
                    continue
                
                print("[INFO] fetching: {}".format(v["contentUrl"]))
                r = requests.get(v["contentUrl"], timeout=30)
                # build a name for the output image, avoiding collision with existing files
                filenameNumber += 1
                filename = os.path.sep.join([outputDirectory, "{}_{}{}".format(filenamePrefix,str(filenameNumber).zfill(5), extension)])
                while os.path.exists( filename ):
                    filenameNumber += 1
                    filename = os.path.sep.join([outputDirectory, "{}_{}{}".format(filenamePrefix,str(filenameNumber).zfill(5), extension)])
                    
                # write the image to disk
                with open(filename, "wb") as file:
                    file.write(r.content)
                
                # now open the file with Image and confirm it meets our minimum size requirements,
                # if we can't open it or it is too small, then delete it
                deleteTheFile = False
                try:                
                    with Image.open(filename) as image:
                        if( image.format != "JPEG" or image.width < 320 or image.height < 240 ):
                            deleteTheFile = True
                except UnidentifiedImageError:
                    deleteTheFile = True
                    
                if deleteTheFile:
                    print("[INFO] deleting: {}".format(filename))
                    os.remove(filename)
                
            # catch any errors that would not unable us to download the image
            except (IOError, FileNotFoundError, exceptions.RequestException, exceptions.HTTPError, exceptions.ConnectionError, exceptions.Timeout) as e:
                print("[INFO] exception {} for URL: {}".format(e, v["contentUrl"]))
                    