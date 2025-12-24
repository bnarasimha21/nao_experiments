#!/bin/bash
# Setup script for PyNAOqi environment
# Run with: source setup_env.sh

SDK_PATH="/Users/nbadrinath/Downloads/pynaoqi-python2.7-2.8.6.23-mac64-20191127_144231"

# Add SDK's Python to PATH (first, so it takes priority)
export PATH="${SDK_PATH}/bin:$PATH"

# Create convenient alias
alias nao-python="${SDK_PATH}/bin/python2"

echo "✅ PyNAOqi environment configured!"
echo ""
echo "Python 2.7 + NAOqi ready to use."
echo ""
echo "Test with:"
echo "  python2 test_setup.py"
echo ""
echo "Run examples:"
echo "  python2 examples/say_hello.py <robot_ip>"
echo "  python2 examples/wave.py <robot_ip>"
echo "  python2 examples/dance.py <robot_ip>"
