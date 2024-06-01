# Sources Used: https://thepythoncode.com/article/extract-media-metadata-in-python

import argparse
import pymongo
import ffmpeg
import subprocess
import math 
from frameioclient import FrameioClient
import sys

# Convert frames to hh: mm : ss : ff timecode 
# Use divmod to find the quotient (if applicable) and remainder
# Continue doing divmod as long as quotient is large enough
def frameToTimeCode(frame, frameRate):
    result = ""
    x = divmod(frame, frameRate) 
    if(x[0] == 0): 
        result = f"00:00:00.{x[1]:02d}" 
    elif(x[0] > 0):
        y = divmod(x[0], frameRate) 
        if(y[0] > 0): 
            z = divmod(y[0], frameRate)
            if(z[0] > 0): 
                result = f"{z[0]:02d}:{z[1]:02d}:{y[1]:02d}.{x[1]:02d}"
            else: 
                result = f"00:{y[0]:02d}:{y[1]:02d}.{x[1]:02d}"
        else: 
            result = f"00:00:{x[0]:02d}.{x[1]:02d}"

    return result

# Convert seconds to hh: mm : ss time
# Similar to frameToTimeCode method 
def secondsToTimeCode(seconds):
    finalTimeCode = ""
    result = divmod(seconds, 60) 
    if(result[0] == 0): 
        finalTimeCode = f"00:{result[1]:02d}"
    elif(result[0] > 0): 
        result2 = divmod(result[0], 60)
        if(result2[0] > 0):
            finalTimeCode = f"{result2[0]:02d}:{result2[1]:02d}:{result[1]:02d}"
        else:
            finalTimeCode = f"00:{result[0]:02d}:{result[1]:02d}"

    return finalTimeCode


# Set up arg parse commands and store their values in destination variable
myParser = argparse.ArgumentParser(prog="Grab That Vid Info", description="NOTE: CLI Program using Python that pulls info from a video using ffmpeg")
myParser.add_argument("--process", dest="processVideoRequest", help="NOTE: Process a video by declaring the name of the video file. Example: --process demo.mp4")
myParser.add_argument("--query", dest="queryVideo", help="NOTE: Query the information you'd like to pull from a video. Example: --query demo.mp4")
myParser.add_argument("--listQueries", dest ="listOfQueries", nargs='+',type=int, help="NOTE: Combine this with query if you already know the shortcuts to query. Example: --query demo.mp4 --vidInfo 1 4 5 8")
myParser.add_argument("--snippet", dest="createSnippet", nargs='+', type=str, help="NOTE: Create a snippet from the video using frame ranges. Example: --snippet demo.mp4 32-67 55-90")
args = myParser.parse_args()

# --process handling
if args.processVideoRequest is not None:

    nameOfVideoFile = args.processVideoRequest
    print()
    print(f"Processing {nameOfVideoFile}....")

    # Establish connection to local MongoDB
    # Create new collection based off nameOfVideoFile, if it doesnt already exist.
    my_client = pymongo.MongoClient("mongodb://localhost:27017/")
    my_db = my_client["videos"]
    my_collection = my_db[nameOfVideoFile]

    videoData = ffmpeg.probe(nameOfVideoFile) 

    # Obtain key video information from probing with ffmpeg
    videoLength = int(videoData['streams'][0]['nb_frames']) 
    videoAvgFrameRate = str(videoData['streams'][0]['avg_frame_rate']) 
    calculatedAverageFrameRate = round(int(videoAvgFrameRate.split('/')[0]) / int(videoAvgFrameRate.split('/')[1])) # Round down the avg frame to whole number
    videoCodec = str(videoData['streams'][0]['codec_name']) 
    videoHeight = str(videoData['streams'][0]['coded_height']) 
    videoWidth = str(videoData['streams'][0]['coded_width']) 
    videoAspectRatio = str(videoData['streams'][0]['display_aspect_ratio']) 
    videoDuration = float(videoData['streams'][0]['duration']) 
    calculatedVideoDuration = secondsToTimeCode(round(videoDuration)) # Use method to get hh:mm:ss duration
    videoCheckIsAVC = str(videoData['streams'][0]['is_avc']) 
    videoBitRate = str(videoData['streams'][0]['bit_rate'])

    # Store key video information in a dictionary to be sent to DB
    videoInformationDictionary = {"nameOfVideo": nameOfVideoFile, "length": videoLength, "avg_frame_rate": calculatedAverageFrameRate,
                                  "codec": videoCodec, "height": videoHeight, "width": videoWidth,
                                  "aspect_ratio": videoAspectRatio, "duration": calculatedVideoDuration,
                                  "is_avc": videoCheckIsAVC, "bitrate": videoBitRate}
    
    # Has the video file already been placed in the db? 
    if my_collection.find_one({"nameOfVideo": nameOfVideoFile}, {"_id": 0}):
        print(f"{nameOfVideoFile} already exists in your database!")
        my_client.close()
        sys.exit(0)
    else:
        my_collection.insert_one(videoInformationDictionary)
        print(f"{nameOfVideoFile} information successfully placed in your database.")
        my_client.close()

# --query handling
if args.queryVideo is not None:
    my_client = pymongo.MongoClient("mongodb://localhost:27017/")
    my_db = my_client["videos"]
    my_collection = my_db[args.queryVideo]

    if not my_collection.find_one({"nameOfVideo": args.queryVideo}, {"_id": 0}):
        print()
        print(f"Could not find {args.queryVideo}. Exiting program....")
        sys.exit(0)

    # Initialize 
    userChoice = 0
    userSelection = []

    if args.listOfQueries is None:
        args.listOfQueries = [] # Create an empty list if --;listQueries is not entered
        print()
        print("Select which query/queries you would like to perform: ")
        print("1. Total Video Length in Frames")
        print("2. Average Frame Rate")
        print("3. Video Codec")
        print("4. Video Height")
        print("5. Video Width")
        print("6. Video Aspect Ratio")
        print("7. Video Duration in hh:mm:ss")
        print("8. Is Video using AVC?")
        print("9. Video Bitrate")
        print("10. Exit program")
        while(userChoice != 10):
            userChoice = int(input("Your choice: "))
            userSelection.append(userChoice)
    
    queriedVideo = my_collection.find({"nameOfVideo": args.queryVideo}, {"_id": 0})
    print()
    for dictionary in queriedVideo:
        for key, value in dictionary.items():
            if key == "length" and (1 in userSelection or 1 in args.listOfQueries):
                print(f"{args.queryVideo} has a length in frames of {value}")
            elif key == "avg_frame_rate" and (2 in userSelection or 2 in args.listOfQueries):
                print(f"{args.queryVideo} has an average frame rate of {value}")
            elif key == "codec" and (3 in userSelection or 3 in args.listOfQueries):
                 print(f"{args.queryVideo} uses the codec: {value}")
            elif key == "height" and (4 in userSelection or 4 in args.listOfQueries):
                print(f"{args.queryVideo} has a height of {value}")
            elif key == "width" and (5 in userSelection or 5 in args.listOfQueries):
                print(f"{args.queryVideo} has a width of {value}")
            elif key =="aspect_ratio" and (6 in userSelection or 6 in args.listOfQueries):
                print(f"{args.queryVideo} has an aspect ratio of {value}")
            elif key == "duration" and (7 in userSelection or 7 in args.listOfQueries):
                print(f"{args.queryVideo} has a duration (in hh:mm:ss) of {value}")
            elif key == "is_avc" and (8 in userSelection or 8 in args.listOfQueries):
                print(f"{args.queryVideo} is in AVC? It is {value}")
            elif key == "bitrate" and (9 in userSelection or 9 in args.listOfQueries):
                print(f"{args.queryVideo} has a bitrate of {value}")

    print(f"Finished obtaining {args.listOfQueries} information. Closing program....")
    my_client.close()

# --snippet handling
if args.createSnippet is not None:

    print()
    print(frameToTimeCode(532, 60), " LMAO!")

    # ***** IMPORTANT: Must replace DEFAULT with your OWN FrameIO account token to upload! *****
    me_client = FrameioClient('INSERT_YOUR_TOKEN_HERE') 

    # Intialize constants
    currentCommand = 0
    videoName = args.createSnippet[currentCommand]
    currentCommand += 1

    # Establish connections to local MongoDB
    my_client = pymongo.MongoClient("mongodb://localhost:27017/")
    my_db = my_client["videos"]
    my_collection = my_db[videoName]

    # Validate that the video file exists in DB
    if not my_collection.find_one({"nameOfVideo": videoName}, {"_id": 0}):
        print(f"Could not find {videoName}. Exiting program....")
        sys.exit(0)

    # Grab the length of the video (the final frame), and its frame rate
    videoDocument = my_collection.find_one({"nameOfVideo": videoName}, {"_id":0})
    videoLength = int(videoDocument['length'])
    videoFrameRate = int(videoDocument['avg_frame_rate'])

    print(f"Trimming {videoName} to the desired snippets....")
    # Iterate through each of the ranges or 'commands' from the user
    while currentCommand < len(args.createSnippet):
        print()
        thisFrame = args.createSnippet[currentCommand].split("-")

        # Validate that the range is within the length of the video 
        if int(thisFrame[0]) <= videoLength and int(thisFrame[1]) <= videoLength:
            # Run ffmpeg as a subprocess to trim a snippet from the video
            print(f"Creating snippet for range {thisFrame[0]}-{thisFrame[1]}")
            subprocess.run('ffmpeg -loglevel quiet -ss ' + str(frameToTimeCode(int(thisFrame[0]), videoFrameRate)) + ' -to ' + str(frameToTimeCode(int(thisFrame[1]), videoFrameRate)) + ' -i ' + videoName + ' -c copy ' + str(thisFrame[0] + '-' + thisFrame[1]) + '.mp4', shell=True)
            print(f"{thisFrame[0]}-{thisFrame[1]}.mp4 created...")

            # ***** IMPORTANT: Must replace the folder id with your own folder id to upload! *****
            me_client.assets.upload("INSERT_FOLDER_ID_HERE", str(thisFrame[0] + "-" + thisFrame[1]) + ".mp4") 
            print(f"{thisFrame[0]}-{thisFrame[1]}.mp4 uploaded to FrameIO successfully!")

        currentCommand += 1








                            

            