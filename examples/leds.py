#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Control NAO's LED lights.

Usage:
    python2 leds.py <robot_ip>
"""

import sys
import time
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Demonstrate NAO's LED controls."""
    
    # Create LED proxy
    leds = ALProxy("ALLeds", robot_ip, port)
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    
    tts.say("Watch my eyes!")
    
    # Eye LED groups:
    # "FaceLeds" - All face LEDs
    # "LeftFaceLeds" - Left eye
    # "RightFaceLeds" - Right eye
    # "ChestLeds" - Chest button
    # "FeetLeds" - Foot LEDs
    
    print("Setting eyes to red...")
    leds.fadeRGB("FaceLeds", 1.0, 0.0, 0.0, 0.5)  # Red, 0.5 second fade
    time.sleep(1)
    
    print("Setting eyes to green...")
    leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.5)  # Green
    time.sleep(1)
    
    print("Setting eyes to blue...")
    leds.fadeRGB("FaceLeds", 0.0, 0.0, 1.0, 0.5)  # Blue
    time.sleep(1)
    
    print("Rainbow effect...")
    colors = [
        (1.0, 0.0, 0.0),  # Red
        (1.0, 0.5, 0.0),  # Orange
        (1.0, 1.0, 0.0),  # Yellow
        (0.0, 1.0, 0.0),  # Green
        (0.0, 0.0, 1.0),  # Blue
        (0.5, 0.0, 1.0),  # Purple
    ]
    
    for r, g, b in colors:
        leds.fadeRGB("FaceLeds", r, g, b, 0.3)
        time.sleep(0.4)
    
    print("Blinking...")
    for i in range(3):
        leds.off("FaceLeds")
        time.sleep(0.2)
        leds.on("FaceLeds")
        time.sleep(0.2)
    
    # Reset to default white
    print("Resetting to white...")
    leds.fadeRGB("FaceLeds", 1.0, 1.0, 1.0, 0.5)
    
    tts.say("LED demo complete!")
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python2 leds.py <robot_ip>")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)


