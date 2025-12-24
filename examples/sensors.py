#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Read NAO's sensor values.

Usage:
    python2 sensors.py <robot_ip>
"""

import sys
import time
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Read and display various sensor values."""
    
    # Create memory proxy (sensors are accessed through ALMemory)
    memory = ALProxy("ALMemory", robot_ip, port)
    
    print("=" * 50)
    print("NAO Sensor Readings")
    print("=" * 50)
    
    # Battery
    print("\n--- Battery ---")
    battery = memory.getData("Device/SubDeviceList/Battery/Charge/Sensor/Value")
    print("Battery Level: %.0f%%" % (battery * 100))
    
    # Temperature
    print("\n--- Head Temperature ---")
    head_temp = memory.getData("Device/SubDeviceList/Head/Temperature/Sensor/Value")
    print("Head Temperature: %.1f°C" % head_temp)
    
    # Touch sensors
    print("\n--- Touch Sensors ---")
    touch_sensors = [
        ("Device/SubDeviceList/Head/Touch/Front/Sensor/Value", "Head Front"),
        ("Device/SubDeviceList/Head/Touch/Middle/Sensor/Value", "Head Middle"),
        ("Device/SubDeviceList/Head/Touch/Rear/Sensor/Value", "Head Rear"),
        ("Device/SubDeviceList/LHand/Touch/Back/Sensor/Value", "Left Hand"),
        ("Device/SubDeviceList/RHand/Touch/Back/Sensor/Value", "Right Hand"),
    ]
    
    for sensor_key, sensor_name in touch_sensors:
        try:
            value = memory.getData(sensor_key)
            status = "Touched" if value > 0.5 else "Not touched"
            print("%s: %s" % (sensor_name, status))
        except:
            print("%s: N/A" % sensor_name)
    
    # Sonar (distance sensors)
    print("\n--- Sonar Distance ---")
    try:
        left_sonar = memory.getData("Device/SubDeviceList/US/Left/Sensor/Value")
        right_sonar = memory.getData("Device/SubDeviceList/US/Right/Sensor/Value")
        print("Left Sonar: %.2f m" % left_sonar)
        print("Right Sonar: %.2f m" % right_sonar)
    except:
        print("Sonar: N/A")
    
    # Foot bumpers
    print("\n--- Foot Bumpers ---")
    bumpers = [
        ("Device/SubDeviceList/LFoot/Bumper/Left/Sensor/Value", "Left Foot Left"),
        ("Device/SubDeviceList/LFoot/Bumper/Right/Sensor/Value", "Left Foot Right"),
        ("Device/SubDeviceList/RFoot/Bumper/Left/Sensor/Value", "Right Foot Left"),
        ("Device/SubDeviceList/RFoot/Bumper/Right/Sensor/Value", "Right Foot Right"),
    ]
    
    for sensor_key, sensor_name in bumpers:
        try:
            value = memory.getData(sensor_key)
            status = "Pressed" if value > 0.5 else "Not pressed"
            print("%s: %s" % (sensor_name, status))
        except:
            print("%s: N/A" % sensor_name)
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python2 sensors.py <robot_ip>")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)


