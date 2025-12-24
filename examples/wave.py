#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO wave its arm.

Usage:
    python2 wave.py <robot_ip>
"""

import sys
import time
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
    if len(sys.argv) < 2:
        print("Usage: python2 wave.py <robot_ip>")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)


