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
    
    # Try multiple paths to find .env file
    paths_to_try = [
        env_path,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        os.path.join(os.getcwd(), '.env'),
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
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
                break  # Found and loaded .env file
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


def get_openai_api_key():
    """
    Get OpenAI API key from .env file or environment variable.
    
    Returns:
        OpenAI API key string or None if not found
    """
    # Try environment variable first
    api_key = os.environ.get('OPENAI_API_KEY')
    
    # Fall back to .env file
    if not api_key:
        env_vars = load_env_file()
        api_key = env_vars.get('OPENAI_API_KEY')
    
    return api_key


def get_openai_model():
    """
    Get OpenAI model name from .env file or use default.
    
    Returns:
        Model name string (default: gpt-4o-mini)
    """
    env_vars = load_env_file()
    return env_vars.get('OPENAI_MODEL', 'gpt-4o-mini')

