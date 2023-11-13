#!/bin/bash

sudo add-apt-repository -y ppa:deadsnakes/ppa   
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx

# Install Python 3.7 and the distutils package which is required for pip installation
sudo apt-get install -y python3.7 python3.7-distutils

# Set Python3.7 as the default python3 installation
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1
sudo update-alternatives --config python3

# Install pip for Python3
sudo apt-get install -y python3-pip

# Upgrade pip to the latest version
python3 -m pip install --upgrade pip

# Install packages from the requirements file
pip install -r CrowdCounting-SASNet/requirements.txt
pip install -r requirements.txt