# dmx.py

- Base class for DMX devices.
 - Communication class for sending DMX signals. `DMX` now runs a background
   thread that repeats the last frame until new data is computed. Device classes
   and start addresses are passed to the constructor.

# Prolights_LumiPar7UTRI_8ch.py

Fixture implementation using the new `DmxDevice` base class. The class builds a
channel map from the provided start address and relies on base-class helpers
such as `set_color` and `set_dimmer` to construct DMX frames.

# main.py

- Main script to run the DMX communication.
- For testing it starts one `Prolights_LumiPar7UTRI_8ch` on start address 1 and
  toggles red and green every second.
- COM port 4
