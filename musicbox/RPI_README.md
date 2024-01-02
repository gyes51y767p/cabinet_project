To run the cabinet project the script needs to be run in Python below the 3.10 version.
This script is running on RPI Bookworm and Bullseye 64-bit OS, python 3.9
Run pip install -r requirements, then run ./setup.sh to install the supervisor tool for running when RPI boots.
The command to play sound "mpg123" is not compatible with Python 3.11 which causes a "jack"-related error
