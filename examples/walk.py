#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO walk.

WARNING: Make sure NAO has space to walk and won't fall off a table!

Usage:
    python2 walk.py <robot_ip>
"""

import sys
import os
import time
# Add parent directory to path to import nao_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Make NAO walk forward, then stop."""
    
    # Create proxies
    motion = ALProxy("ALMotion", robot_ip, port)
    posture = ALProxy("ALRobotPosture", robot_ip, port)
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    
    # Wake up the robot
    motion.wakeUp()
    
    # First, make sure NAO is standing
    print("Standing up...")
    posture.goToPosture("Stand", 0.5)
    
    tts.say("I will now walk forward")
    
    # Initialize walk
    motion.moveInit()
    
    print("Walking forward...")
    
    # Walk forward 0.3 meters (x direction)
    # Parameters: x (forward), y (sideways), theta (rotation)
    motion.moveTo(0.3, 0.0, 0.0)
    
    tts.say("Now I will turn around")
    
    print("Turning 180 degrees...")
    # Rotate 180 degrees (pi radians)
    motion.moveTo(0.0, 0.0, 3.14159)
    
    tts.say("Walking back")
    
    print("Walking back...")
    motion.moveTo(0.3, 0.0, 0.0)
    
    # Turn back to original orientation
    motion.moveTo(0.0, 0.0, 3.14159)
    
    tts.say("Done walking!")
    print("Walk complete!")

if __name__ == "__main__":
    robot_ip = get_robot_ip()
    if not robot_ip:
        print("Usage: python walk.py [robot_ip]")
        print("Or set NAO_IP_ADDRESS in .env file")
        print("WARNING: Make sure NAO has clear space to walk!")
        sys.exit(1)
    
    print("Connecting to NAO at: %s" % robot_ip)
    main(robot_ip)


