#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO wave its arm.

Usage:
    python2 wave.py <robot_ip>
"""

import sys
import os
import time
# Add parent directory to path to import nao_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Make NAO wave hello."""
    
    # Create proxies
    motion = ALProxy("ALMotion", robot_ip, port)
    posture = ALProxy("ALRobotPosture", robot_ip, port)
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    
    # Wake up robot
    motion.wakeUp()
    
    # Stand up first
    posture.goToPosture("Stand", 0.5)
    
    # Arm joint names for right arm:
    # RShoulderPitch, RShoulderRoll, RElbowYaw, RElbowRoll, RWristYaw, RHand
    
    # Set stiffness for right arm
    motion.setStiffnesses("RArm", 1.0)
    
    tts.say("Hello!")
    
    # Raise arm up
    names = ["RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RWristYaw"]
    
    # Position 1: Arm up
    angles_up = [-0.5, -0.3, 0.5, 0.0]
    motion.setAngles(names, angles_up, 0.3)
    time.sleep(0.5)
    
    # Wave back and forth
    for i in range(3):
        # Wave right
        motion.setAngles("RWristYaw", 0.5, 0.5)
        time.sleep(0.3)
        # Wave left
        motion.setAngles("RWristYaw", -0.5, 0.5)
        time.sleep(0.3)
    
    # Return to neutral
    motion.setAngles("RWristYaw", 0.0, 0.3)
    time.sleep(0.3)
    
    # Lower arm
    posture.goToPosture("Stand", 0.3)
    
    print("Wave complete!")

if __name__ == "__main__":
    robot_ip = get_robot_ip()
    if not robot_ip:
        print("Usage: python wave.py [robot_ip]")
        print("Or set NAO_IP_ADDRESS in .env file")
        sys.exit(1)
    
    print("Connecting to NAO at: %s" % robot_ip)
    main(robot_ip)


