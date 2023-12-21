# CROWD COUNTING DOCUMENTATION (technical users)

## System requirements

* Debian-based Unix system like Ubuntu.

* Able to execute Bash scripts with root access.

* Git installed.

* Internet access.

## Step-by-step guide

1. Clone the repository at [https://github.com/anirv20/crowd-safety](https://github.com/anirv20/crowd-safety).

1. Run the init.sh using `bash backend/init.sh`.

1. Download the SHHA.pth model weights from [SASNet](https://drive.google.com/drive/folders/1uTkJLQOn-jQg81yNAluBpGpIJ-XaZaGI).

1. In main.py: Configure the path to the SHHA.pth model weights. (MODEL_PATH)

1. In main.py: Configure the output directory. (OUTPUT_DIR)

1. In main.py: Configure the frame sampling interval. (FRAME_INTERVAL)

1. In main.py: If the intended use is with the frontend: Set UPSAMPLING_FACTOR to 1 and COLOR_MAP to None.

1. In main.py: Define the corners of the cropped area on the video in (x, y) pairs in local_coordinates for each Camera instance. 

1. In main.py: Define the global coordinates based on the land survey for each Camera instance.

1. In main.py: Define the path to the camera video for each Camera instance.

1. In main.py: Add the Camera instance to the same or different Camera collections.

1. Run main.py and download the output video from the specified OUTPUT_DIR. This can now be uploaded to the frontend if step 7 was followed. 