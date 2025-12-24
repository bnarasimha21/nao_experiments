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
    if len(sys.argv) < 2:
        print("Usage: python2 say_hello.py <robot_ip>")
        print("Example: python2 say_hello.py 192.168.1.100")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)

