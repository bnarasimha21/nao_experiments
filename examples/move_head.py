#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Move NAO's head (look around).

Usage:
    python2 move_head.py <robot_ip>
"""

import sys
import os
import time
# Add parent directory to path to import nao_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Move NAO's head to look around."""
    
    # Create proxy to motion service
    motion = ALProxy("ALMotion", robot_ip, port)
    
    # Wake up the robot (motors on)
    motion.wakeUp()
    
    # Head joint names:
    # - "HeadYaw": left/right rotation
    # - "HeadPitch": up/down rotation
    
    # Set stiffness (0.0 = relaxed, 1.0 = stiff)
    motion.setStiffnesses("Head", 1.0)
    
    print("Looking straight ahead...")
    motion.setAngles("HeadYaw", 0.0, 0.2)   # Center
    motion.setAngles("HeadPitch", 0.0, 0.2)  # Level
    time.sleep(1)
    
    print("Looking left...")
    motion.setAngles("HeadYaw", 0.7, 0.2)   # About 40 degrees left
    time.sleep(1)
    
    print("Looking right...")
    motion.setAngles("HeadYaw", -0.7, 0.2)  # About 40 degrees right
    time.sleep(1)
    
    print("Looking up...")
    motion.setAngles("HeadYaw", 0.0, 0.2)
    motion.setAngles("HeadPitch", -0.4, 0.2)  # Look up
    time.sleep(1)
    
    print("Looking down...")
    motion.setAngles("HeadPitch", 0.4, 0.2)  # Look down
    time.sleep(1)
    
    print("Returning to center...")
    motion.setAngles("HeadYaw", 0.0, 0.2)
    motion.setAngles("HeadPitch", 0.0, 0.2)
    time.sleep(1)
    
    print("Done!")

if __name__ == "__main__":
    robot_ip = get_robot_ip()
    if not robot_ip:
        print("Usage: python move_head.py [robot_ip]")
        print("Or set NAO_IP_ADDRESS in .env file")
        sys.exit(1)
    
    print("Connecting to NAO at: %s" % robot_ip)
    main(robot_ip)


