#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO speak using the qi framework with explicit session connection.
This approach may work better in some network configurations.

Usage:
    python2 say_hello_web.py <robot_ip>
"""

import sys
import os
# Add parent directory to path to import nao_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip
import qi

def main(robot_ip, port=9559):
    """Make NAO say hello using qi session."""
    
    # Create a session and connect
    session = qi.Session()
    
    print("Connecting to robot at %s:%d..." % (robot_ip, port))
    
    try:
        session.connect("tcp://%s:%d" % (robot_ip, port))
        print("Connected!")
    except RuntimeError as e:
        print("Failed to connect: %s" % str(e))
        print("\nTroubleshooting:")
        print("  1. Check that NAO is on and connected to the network")
        print("  2. Try accessing http://%s/ in your browser" % robot_ip)
        print("  3. Make sure your Mac is on the same WiFi network")
        return
    
    # Get the TextToSpeech service
    tts = session.service("ALTextToSpeech")
    
    # Make NAO speak
    print("Making NAO speak...")
    tts.say("Hello! I am connected and ready to help you!")
    
    print("Done!")

if __name__ == "__main__":
    robot_ip = get_robot_ip()
    if not robot_ip:
        print("Usage: python say_hello_web.py [robot_ip]")
        print("Or set NAO_IP_ADDRESS in .env file")
        sys.exit(1)
    
    print("Connecting to NAO at: %s" % robot_ip)
    main(robot_ip)


