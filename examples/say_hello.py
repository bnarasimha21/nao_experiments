#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO speak!

Usage:
    python2 say_hello.py <robot_ip>
    
Example:
    python2 say_hello.py 192.168.1.100
"""

import sys
import os
# Add parent directory to path to import nao_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip
from naoqi import ALProxy

def main(robot_ip, port=9559):
    """Make NAO say hello."""
    
    # Create a proxy to the Text-to-Speech service
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    
    # Make NAO speak
    tts.say("Hello! I am NAO. Nice to meet you!")
    
    # You can also change voice parameters
    tts.setParameter("speed", 100)  # Speed percentage (80-120 is normal)
    tts.setParameter("pitchShift", 1.0)  # Pitch multiplier
    
    tts.say("I can speak at different speeds and pitches!")

if __name__ == "__main__":
    robot_ip = get_robot_ip()
    if not robot_ip:
        print("Usage: python say_hello.py [robot_ip]")
        print("Or set NAO_IP_ADDRESS in .env file")
        print("Example: python say_hello.py 192.168.1.100")
        sys.exit(1)
    
    print("Connecting to NAO at: %s" % robot_ip)
    main(robot_ip)

