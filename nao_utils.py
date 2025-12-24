#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions for NAO experiments.
Reads configuration from .env file.
"""

import os
import sys

def load_env_file(env_path='.env'):
    """Load environment variables from .env file."""
    env_vars = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env_vars[key] = value
        except Exception as e:
            print("Warning: Could not read .env file: %s" % e)
    return env_vars

def get_robot_ip(default_ip=None):
    """
    Get robot IP address from .env file or command line argument.
    
    Args:
        default_ip: Default IP to use if not found in .env or command line
    
    Returns:
        Robot IP address string
    """
    # Try to get from .env file first
    env_vars = load_env_file()
    robot_ip = env_vars.get('NAO_IP_ADDRESS')
    
    # Fall back to command line argument
    if not robot_ip and len(sys.argv) > 1:
        robot_ip = sys.argv[1]
    
    # Fall back to default
    if not robot_ip:
        robot_ip = default_ip
    
    return robot_ip

