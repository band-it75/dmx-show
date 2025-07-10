# dmx.py

- Base class for DMX devices.
- Communication class for sending dmw signals. DMX class takes device classes, and start address as parameters in an array. 

# Prolights_LumiPar7UTRI_8ch.py

Based on base class dmx.py, this file contains the implementation for the Prolights LumiPar 7 UTRI 8-channel DMX device.

# main.py

- Main script to run the DMX Communication.
- For test it starts one Prolights_LumiPar7UTRI_8ch on start address 1 and toggles red and green every 1 second. 
- COM port 4