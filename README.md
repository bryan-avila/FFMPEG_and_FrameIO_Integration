# What is this?
This is a CLI program made using Python that relies on arg-parse commands to probe video information and store it locally using MongoDB.
You may also upload snippets from a video file to FrameIO using your own token. 

# The Set Up
1) Check that you pip installed the following:
 * argparse
 * pymongo
 * subprocess
 * frameioclient

2) Have MongoDB Community Server [installed](https://www.youtube.com/watch?v=gB6WLkSrtJk)

3) Create a [FrameIO Account](https://developer.frame.io/docs/getting-started/authentication) and obtain your Token.

4) Logged in to FrameIO, create a folder under a new Project and copy the folder's unique id
	* The unique id can be found in the address bar.
   * For example, your address will look similar to _app.frame.io/projects/aaa-aa-aa/bbbbb-bbb-bb_. Copy the id that is found after the third forward slash (/)

# Running the Program
Place a .mp4 file in the same folder that grabVidInfo.py is in.
Run the command prompt while in that folder. As an example, you may now:
1) process a video and store its data using MongoDB: `python grabVidInfo.py --process demo.mp4`
3) query a video's information from MongoDB: `python grabVidInfo.py --query demo.mp4`
4) bypass query and use shortcuts that corresponds to desired information: `python grabVidInfo.py --query demo.mp4 --listQueries 2 4 5 8`
5) create video snippets by passing frame ranges: `python grabVidInfo.py --snippet demo.mp4 32-56 141-203 404-532`

# Troubleshooting
You may come across an issue when installing the frameioclient library via pip.
Downgrading `urllib3` to version `1.26.15` worked for me and hopefully it works for you! 

  
