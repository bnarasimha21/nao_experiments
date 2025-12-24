#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Make NAO stand up or sit down using predefined postures.

Usage:
    python2 stand_sit.py <robot_ip> <action>
    
Where <action> is one of:
    stand   - Make robot stand up
    sit     - Make robot sit down
    crouch  - Make robot crouch
    lyingback - Make robot lie on its back
    lyingbelly - Make robot lie on its belly
"""

import sys
import os
# Add parent directory to path to import nao_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip
from naoqi import ALProxy

def main(robot_ip, action, port=9559):
    """Control NAO's posture."""
    
    # Create proxies
    motion = ALProxy("ALMotion", robot_ip, port)
    posture = ALProxy("ALRobotPosture", robot_ip, port)
    
    # Wake up robot (turn on motors)
    motion.wakeUp()
    
    # Map actions to posture names
    posture_map = {
        "stand": "Stand",
        "sit": "Sit",
        "crouch": "Crouch",
        "lyingback": "LyingBack",
        "lyingbelly": "LyingBelly"
    }
    
    if action.lower() not in posture_map:
        print("Unknown action: %s" % action)
        print("Valid actions: stand, sit, crouch, lyingback, lyingbelly")
        return
    
    posture_name = posture_map[action.lower()]
    
    print("Going to %s posture..." % posture_name)
    
    # Go to posture with speed 0.5 (range 0.0 to 1.0)
    result = posture.goToPosture(posture_name, 0.5)
    
    if result:
        print("Successfully reached %s posture!" % posture_name)
    else:
        print("Failed to reach posture.")

if __name__ == "__main__":
    robot_ip = get_robot_ip()
    if not robot_ip:
        if len(sys.argv) < 2:
            print("Usage: python stand_sit.py [robot_ip] <action>")
            print("Or set NAO_IP_ADDRESS in .env file")
            print("Actions: stand, sit, crouch, lyingback, lyingbelly")
            print("Example: python stand_sit.py stand")
            sys.exit(1)
        robot_ip = sys.argv[1]
        action = sys.argv[2] if len(sys.argv) > 2 else "stand"
    else:
        action = sys.argv[1] if len(sys.argv) > 1 else "stand"
    
    if not action:
        print("Usage: python stand_sit.py [robot_ip] <action>")
        print("Actions: stand, sit, crouch, lyingback, lyingbelly")
        sys.exit(1)
    
    print("Connecting to NAO at: %s" % robot_ip)
    main(robot_ip, action)


