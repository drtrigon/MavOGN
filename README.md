# MavOGN

> [!IMPORTANT]
**This code is in a PROOF-OF-CONCEPT kind of state, several rough edges will be present. E.g. the conversation of units (scaling factors) and the field assignments might be not optimal or just totally wrong! Be aware and check before doing something serious with it! Please commit improvements.**

This was heavily inspired by https://github.com/consider-it/MAVLink-ADSB_Emulator

## Description
Loads OGN data into Mission Planner or QGC without a need for a receiver (FLARM, SoftRF, etc). This data can be forwarded to the UAS (via telemetry link) for collision avoidance without the need for an onboard receiver or any additional hardware (however not recommended due to e.g. latency). Tested on linux and Android, should also work on Mac and Windows.

The traffic data gets injected as MAVLink `ADSB_VEHICLE` message into the UDP stream to localhost port 14550 (by default). In order for this to work the GCS needs to have a connection to a FC. This can be a physical FC or a SITL simulator instance.

<img width="1970" alt="image" src="https://github.com/MohammadAdib/MavADSB/assets/1324144/97b7e787-d24d-4bae-881f-30ecf718c9c8">

<img width="1970" alt="image" src="https://github.com/MohammadAdib/MavADSB/assets/1324144/51630334-e4dc-4995-af77-3b710f7a382f">

### Basic usage
Make sure to have Python3 installed along with `pymavlink` and `ogn-client` via pip. Clone this repo and type this into the terminal:

```
python3 helloworld/src/helloworld/mavlink_adsb_emulator_ogn_udp_injection.py --home lat,lon
```

Replace ```lat``` and ```lon``` with your location, and it will display all OGN data within 100km. You can also use `--help` to get more info about usage.

If you don't have a FC at hand, download a SITL binary from https://firmware.ardupilot.org/Copter/stable/SITL_x86_64_linux_gnu/ and run:

```
./arducopter --model quad --serial0=udpclient:127.0.0.1:14550 --home lat,lon,0.,0.
```

### Advanced usage
Install BeeWare dependencies and set up a virtual environment as described in https://tutorial.beeware.org/tutorial/tutorial-0/ and also install the BeeWare tools as shown in https://tutorial.beeware.org/tutorial/tutorial-1/

To run the GUI type in linux terminal (should work for Windows and Mac also):

```
(beeware-venv) $ cd helloworld
(beeware-venv) $ briefcase dev
```

To build, install and run the Android app use:

```
(beeware-venv) $ briefcase create android
(beeware-venv) $ briefcase build android
(beeware-venv) $ briefcase run android
```

I recommend using a physical device in which case you might want to install 
`android-sdk-platform-tools-common` to setup udev rules etc. Further more you have to:
  - Enable developer options
  - Enable USB debugging
  - after USB plugin unlock phone to finally allow for USB debugging
Once these steps have been completed, your device should appear in the list of available devices.

To make it work on Android a few points have to be paid caution to:
  - Energy Saving: must be turned OFF to make the app work!
  - Notification/Popup: Wi-Fi Connected but No Internet
    - Yes: Wi-Fi becomes the internet gateway and thus you will lose the internet connection
    - No: Wi-Fi will be disconnected
    - Ignore: Wi-Fi & mobile keep connected, mobile stays the gateway - this is the setting needed, however it will cause the MAVLink down stream (telemetrie) to WORK but the up stream (params modifications, missions upload and starting) to STOP WORKING

### GCS integration (Mission Planner and QGroundControl tested)
No setup needed. After running the script, please open Mission Planner and connect to a FC (physical or simulated).

### API & Docs
Install Python3 and BeeWare: https://tutorial.beeware.org/

MAVLink `ADSB_VEHICLE` message: https://mavlink.io/en/services/traffic_management.html#ADSB_VEHICLE

MavADSB: https://github.com/MUSTARDTIGERFPV/MavADSB and https://github.com/MohammadAdib/MavADSB

### Traditional methods
ArduPilot ADS-B (wiki): https://ardupilot.org/copter/docs/common-ads-b-receiver.html

SoftRF: https://github.com/lyusupov/SoftRF and https://github.com/moshe-braner/SoftRF

It is still recommended to use the above for least latency. However paired with this software the range is greatly extended. Enjoy :)
