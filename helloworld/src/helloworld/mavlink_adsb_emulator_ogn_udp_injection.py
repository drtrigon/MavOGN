#!/usr/bin/env python3
"""
MAVLink ADSB_VEHILCE Emulator to inject OGN data via UDP

Generate MAVLink ADSB_VEHICLE messages from OGN data.

Tested on linux and android (BeeWare/Toga) with Mission Planner and QGroundControl.

Author:    Ursin Solèr <dr.trigon@surfeu.ch>
Author:    Jannik Beyerstedt <beyerstedt@consider-it.de>
License:   MIT
"""

# $ sudo apt update
# $ sudo apt install python3-pip
# $ pip3 install pymavlink ogn-client --break-system-packages

# connect to FC via UDP - FC can be real hardware or SITL
# use SITL: https://firmware.ardupilot.org/Copter/stable/SITL_x86_64_linux_gnu/
#           $ ./arducopter --model quad --serial0=udpclient:127.0.0.1:14550 [--home 47.,8.,0.,0.]
#           in MissionPlanner disable auto-pan on the map; use the checkbox at bottom of map view
#           (not recommended but possible to run SITL in MissionPlanner and open udp port for injection,
#           see: https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html#using-mission-planner-forwarding)
#           sim_vehicle.py is an automated wrapper that builds and runs the binary with a lot of nice options (look for docker, due to dep-hell)
#           see: https://github.com/ArduPilot/ardupilot/blob/master/Tools/autotest/sim_vehicle.py

# run this script to inject OGN as MAVLink ADSB data message
# $ python3 mavlink_adsb_emulator_ogn_udp_injection.py [-o udpout:localhost:14550] [-vv]

# TODO: check all units (scaling factors), check all fields (correct/proper assignment)
# TODO: reach out to ardupilot/missionplanner guys to figure out how to use on android (port in python or implement in missionplanner adsb feature?)
#       (reverse engineer pymavlink to get plain packet structure and build it by other means allows to omitt pymavlink)
#       see https://github.com/MohammadAdib/MavADSB
#       see https://github.com/MUSTARDTIGERFPV/MavADSB
#       see https://github.com/ArduPilot/MissionPlanner/pull/3251
#       see https://github.com/MUSTARDTIGERFPV/MissionPlanner/blob/059e065587d0182f8a24d1dc2dd8804cce870132/ExtLibs/Utilities/adsb.cs
# TODO: merge ADS-B traffic in
# TODO: allow too set home and range on android

import argparse
import logging
import sys
#from urllib.parse import urlparse
#from pymavlink.dialects.v10 import ardupilotmega as mavlink1
from pymavlink.dialects.v20 import common as mavlink2
mavlink = mavlink2
from pymavlink import mavutil
from ogn.client import AprsClient
from ogn.parser import parse, AprsParseError

#OWN_SYSID = 255   # comming from GCS and inject into FC
OWN_SYSID = 1     # comming from device (FC) and inject into GCS
OWN_COMPID = 0
UDP_CONNECT_TIMEOUT = 10

# TODO: fill this information or un-set the flags (down below)
ADSB_SQUAWK = 7000  # uint16_t (7000: Standard VFR (Sichtflug) in Europa)
ADSB_EMITTER_TYPE = mavlink.ADSB_EMITTER_TYPE_ROTOCRAFT


def main():
    log_format = '%(asctime)s %(levelname)s:%(name)s: %(message)s'
    log_datefmt = '%Y-%m-%dT%H:%M:%S%z'
    logging.basicConfig(format=log_format, datefmt=log_datefmt, level=logging.INFO)
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(description='MAVLink GNSS Status Display')
    #parser.add_argument("-o", "--output", default="udpout:localhost:14550",
    parser.add_argument("-o", "--output", default="udpout:127.0.0.1:14550",
                        help="connection address for ADS-B data, e.g. tcp:$ip:$port, udpout:$ip:$port")
    parser.add_argument("-O", "--home", type=ascii, default="47.,8.",
                        help="traffic 100km around home is displayed, e.g. 47.,8.")
    parser.add_argument("-s", "--sysID", type=int,
                        help="just use data from the specified system ID")
    parser.add_argument("-v", "--verbosity", action="count",
                        help="increase output and logging verbosity")
    args = parser.parse_args()

    if args.verbosity == 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbosity == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    #logger.setLevel(100)  # disable ALL logging output
    #logger.setLevel(0)    # enable ALL logging output

    # SETUP
    # open MAVLink output
    logger.info("Starting MAVLink connection to %s", args.output)
    try:
        mav_out = mavutil.mavlink_connection(
            args.output, source_system=OWN_SYSID, source_component=OWN_COMPID)
    except OSError:
        logger.error("MAVLink connection failed, exiting")
        sys.exit(-1)

    # open OGN input
    # https://github.com/glidernet/python-ogn-client
    # https://www.aprs-is.net/javAPRSFilter.aspx
    logger.info("Starting OGN connection")
    try:
        #client = AprsClient(aprs_user='N0CALL')
        client = AprsClient(aprs_user='N0CALL', aprs_filter='r/%f/%f/100.' % eval(f"({eval(args.home)})"))
        client.connect()
    except:
        logger.error("OGN connection failed, exiting")
        sys.exit(-1)

    # RUN
    def on_message(data):
        logger.debug("IN: %s", data)
        if 'address' not in data:     # WORK-A-ROUND: ANDROID
            data.update({'address': data['raw_message'][3:9]})
        if 'climb_rate' not in data:  # WORK-A-ROUND: ANDROID
            data.update({'climb_rate': 0.})

        # fill ADSB_VEHICLE message and send
        adbs_flags = mavlink.ADSB_FLAGS_VALID_COORDS + \
            mavlink.ADSB_FLAGS_VALID_ALTITUDE + \
            mavlink.ADSB_FLAGS_VALID_HEADING + \
            mavlink.ADSB_FLAGS_VALID_VELOCITY + \
            mavlink.ADSB_FLAGS_VALID_CALLSIGN + \
            mavlink.ADSB_FLAGS_VALID_SQUAWK

        adsb = mavlink.MAVLink_adsb_vehicle_message(
#            ADSB_ICAO_ADDR,                             # ICAO_address (uint32_t)
            int(data['address'], 16),                   # ICAO_address (uint32_t)
#            1234,                                       # ICAO_address (uint32_t)
            int(data["latitude"]*10000000),             # lat (int32_t, degE7)
            int(data["longitude"]*10000000),            # lon (int32_t, degE7)
            1,                                          # altitude type (0=QNH, 1=GNSS)
            int(data['altitude']*1000),                 # altitude (uint32_t, mm)
            int(data['track']*100),                     # heading (uint16_t, cdeg)
#            int(data['ground_speed']*100),              # hor_vel (uint16_t, cm/s)
            int(data['ground_speed']*1),                # hor_vel (uint16_t, cm/s)
            int(data['climb_rate']*100),                # ver_vel (int16_t, cm/s, positive up)
#            bytes(ADSB_CALLSIGN, 'ascii'),              # callsign (char[9])
#            bytes(data['name'], 'ascii'),               # callsign (char[9])
            bytes(data['name'][:8], 'ascii'),           # callsign (char[9])
            ADSB_EMITTER_TYPE,                          # emitter_type (uint8_t)
            0,                                          # TODO: time since last contact (uint8_t, s) - use delta to data['timestamp']
            adbs_flags,                                 # flags (uint16_t)
            ADSB_SQUAWK)                                # squawk (uint16_t)
        logger.info("OUT: %s", adsb)
        mav_out.mav.send(adsb)

    def process_beacon(raw_message):
        if "_HelloWorld__kill" in globals():  # ANDROID GUI (BeeWare/Toga)
            raise KeyboardInterrupt
        try:
            beacon = parse(raw_message)
            logger.debug('Received {aprs_type}: {raw_message}'.format(**beacon))
            #logger.debug(beacon)
            if (beacon['aprs_type'] == 'position') and (beacon['beacon_type'] not in ['receiver', 'fanet']):
                on_message(beacon)
        #except AprsParseError as e:
        except Exception as e:
            #logger.warning('Error, {}'.format(e.message))
            logger.warning('Error, {}'.format(e))
            globals()['_HelloWorld__exception'] = e  # ANDROID GUI (BeeWare/Toga)

    try:
        client.run(callback=process_beacon, autoreconnect=True)
    except KeyboardInterrupt:
        logger.info('\nStop ogn gateway')
        client.disconnect()
        logger.info('\nClose MAVLink connection')
        mav_out.close()

if __name__ == "__main__":
    main()
