#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO do a simple dance!

WARNING: Make sure NAO has space and won't fall.

Usage:
    python2 dance.py <robot_ip>
"""

import sys
import time
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Make NAO perform a simple dance routine."""
    
    # Create proxies
    motion = ALProxy("ALMotion", robot_ip, port)
    posture = ALProxy("ALRobotPosture", robot_ip, port)
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    leds = ALProxy("ALLeds", robot_ip, port)
    
    # Wake up and stand
    motion.wakeUp()
    posture.goToPosture("Stand", 0.5)
    
    tts.say("Let's dance!")
    
    # Set stiffness for arms
    motion.setStiffnesses("LArm", 1.0)
    motion.setStiffnesses("RArm", 1.0)
    
    # Dance moves!
    for i in range(2):
        # Arms up
        leds.fadeRGB("FaceLeds", 1.0, 0.0, 0.0, 0.2)
        motion.setAngles(["LShoulderPitch", "RShoulderPitch"], [-1.0, -1.0], 0.4)
        motion.setAngles(["LShoulderRoll", "RShoulderRoll"], [0.3, -0.3], 0.4)
        time.sleep(0.5)
        
        # Arms out to sides
        leds.fadeRGB("FaceLeds", 0.0, 1.0, 0.0, 0.2)
        motion.setAngles(["LShoulderPitch", "RShoulderPitch"], [0.0, 0.0], 0.4)
        motion.setAngles(["LShoulderRoll", "RShoulderRoll"], [1.3, -1.3], 0.4)
        time.sleep(0.5)
        
        # Arms crossed
        leds.fadeRGB("FaceLeds", 0.0, 0.0, 1.0, 0.2)
        motion.setAngles(["LShoulderRoll", "RShoulderRoll"], [-0.2, 0.2], 0.4)
        motion.setAngles(["LShoulderPitch", "RShoulderPitch"], [0.5, 0.5], 0.4)
        time.sleep(0.5)
        
        # Lean left
        leds.fadeRGB("FaceLeds", 1.0, 1.0, 0.0, 0.2)
        motion.setAngles("LHipRoll", 0.2, 0.3)
        motion.setAngles("RHipRoll", 0.2, 0.3)
        time.sleep(0.4)
        
        # Lean right
        leds.fadeRGB("FaceLeds", 1.0, 0.0, 1.0, 0.2)
        motion.setAngles("LHipRoll", -0.2, 0.3)
        motion.setAngles("RHipRoll", -0.2, 0.3)
        time.sleep(0.4)
        
        # Center
        motion.setAngles("LHipRoll", 0.0, 0.3)
        motion.setAngles("RHipRoll", 0.0, 0.3)
    
    # Finish with arms up
    leds.fadeRGB("FaceLeds", 1.0, 1.0, 1.0, 0.3)
    motion.setAngles(["LShoulderPitch", "RShoulderPitch"], [-1.5, -1.5], 0.3)
    motion.setAngles(["LShoulderRoll", "RShoulderRoll"], [0.2, -0.2], 0.3)
    time.sleep(0.5)
    
    tts.say("Thank you!")
    
    # Return to stand
    posture.goToPosture("Stand", 0.5)
    
    print("Dance complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python2 dance.py <robot_ip>")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)


