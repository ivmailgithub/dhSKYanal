i'm reminded by a cn comment that photos can have gps info so that uploading a video file or fisheye exposes the user to internet robot spiders scanning for gps info .. not a good idea in a war zone.
so instead of a public claude artifact link i'm post the raw html or python code and people can pull down the code .. look at it .. generate the panorama.png, horizon.txt
landscape.ini file to C:\Users\<yoyou>\AppData\Roaming\Stellarium\landscapes\CustomLandscape.  The python version needs "pip install opencv-python" and the newer pythons
require you do use venv's.... easy to do when you've done it 100 times ... but the first time is kind of strange.  the nodejs version is huge but selfcontained; python is like 500 lines and done.

really this app is for people where 70% of the sky is hidden behind buildings, the side of your house, trees ...
1) take a video on your phone of the horizon 360 degrees copy a 50m or so mp4 to your pc
2) python .\zai-stellariumLandscapeCreatorFromPhoneVideo.py <yoyourvideo>.\backyarddeck20250928_VID_20250927_174630.mp4
Extracting frames from .\backyarddeck20250928_VID_20250927_174630.mp4...
Total frames in video: 608
Extracted 50 frames
Creating panorama from frames...
Processing 50 images for panorama...
Panorama stitching failed with status: 3
Trying alternative approach...
Using simple horizontal stitching...
Panorama saved to: stellarium_landscape\CustomHorizon\panorama.png
Panorama dimensions: 8192x291
Creating fog texture...
Fog texture created at: stellarium_landscape\CustomHorizon\fog.png
Creating landscape.ini configuration...
landscape.ini created at: stellarium_landscape\CustomHorizon\landscape.ini
Creating landscape package...
Landscape package created: stellarium_landscape\CustomHorizon.zip
Package size: 5.25 MB

==================================================
STELLARIUM LANDSCAPE CREATION COMPLETE!
==================================================
Landscape name: CustomHorizon
Output directory: stellarium_landscape
Package file: stellarium_landscape\CustomHorizon.zip

To install in Stellarium:
1. Copy the zip file to Stellarium's landscapes directory
   (usually: ~/.stellarium/landscapes/ on Linux)
   (usually: C:\Program Files\Stellarium\landscapes\ on Windows)
2. Extract the zip file in that directory
3. Restart Stellarium and select your landscape from the Sky View menu
==================================================
some 45 minutes in a windows terminal python .. 10 minutes in a wsl-ub24 python terminal so opencv-python cv2 is different win or linux

oh and remember 99.9% of this code is ai generated ... claude gemini-2.5 z.ai-glm46 ..and i alternate through out the day/week as the freebie tokens run out
i don't have my qwen3-coder setup locally yet
oops some typo bugs in argparser which i didn't bother to fix since i run from the cmdline and skip the errors .. but when in doubt let gemini fix it so it adds to horizon file for the panorama.png generated ... but i get all 0's since sky edge detection needs to be fixed...  still the parorama.png is pretty in stellarium...
