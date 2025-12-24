# NAO Robot Python Experiments

## Prerequisites

1. **NAO Robot** on the same network as your computer
2. **Robot IP address** - Press the chest button on the robot to hear it

The PyNAOqi SDK includes its own Python 2.7, so no separate installation is needed!

---

## Quick Setup

### Step 1: Configure Environment

```bash
cd /Users/nbadrinath/Documents/MyGitHub/nao_experiments
source setup_env.sh
```

### Step 2: Verify Setup

```bash
python2 test_setup.py
```

You should see: `SUCCESS: NAOqi loaded correctly!`

### Step 3: Get Your Robot's IP

Press the **chest button** on NAO once — it will announce its IP address.

### Step 4: Run Your First Script!

```bash
python2 examples/say_hello.py 192.168.1.100
```

Replace `192.168.1.100` with your robot's actual IP.

---

## 📁 Example Scripts

| Script | What it does |
|--------|--------------|
| `examples/say_hello.py` | Make NAO speak |
| `examples/move_head.py` | Look around (left, right, up, down) |
| `examples/stand_sit.py` | Stand up, sit down, or crouch |
| `examples/walk.py` | Walk forward and turn |
| `examples/wave.py` | Wave hello |
| `examples/dance.py` | Dance routine with LED effects |
| `examples/leds.py` | Change eye LED colors |
| `examples/sensors.py` | Read battery, touch sensors, sonar |

### Usage Examples

```bash
# Make NAO speak
python2 examples/say_hello.py 192.168.1.100

# Make NAO stand up
python2 examples/stand_sit.py 192.168.1.100 stand

# Make NAO sit down
python2 examples/stand_sit.py 192.168.1.100 sit

# Make NAO wave
python2 examples/wave.py 192.168.1.100

# Make NAO dance
python2 examples/dance.py 192.168.1.100

# Check sensors
python2 examples/sensors.py 192.168.1.100
```

---

## Main NAOqi Services (Proxies)

| Service | Description |
|---------|-------------|
| `ALTextToSpeech` | Text-to-speech |
| `ALMotion` | Body movement control |
| `ALRobotPosture` | Predefined postures (Stand, Sit, etc.) |
| `ALLeds` | LED control |
| `ALAudioPlayer` | Play audio files |
| `ALMemory` | Access sensor data and events |
| `ALVideoDevice` | Camera access |
| `ALFaceDetection` | Face detection |
| `ALSpeechRecognition` | Speech recognition |
| `ALBehaviorManager` | Manage installed behaviors |

---

## Writing Your Own Script

Basic template:

```python
#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
from naoqi import ALProxy

def main(robot_ip, port=9559):
    # Create proxy to a service
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    motion = ALProxy("ALMotion", robot_ip, port)
    
    # Wake up the robot (enable motors)
    motion.wakeUp()
    
    # Do something!
    tts.say("Hello world!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python2 script.py <robot_ip>")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)
```

---

## Troubleshooting

### "Cannot connect to robot"
- Ensure NAO is powered on and connected to the network
- Verify the IP address is correct
- Check if your firewall allows connections on port 9559
- Try pinging the robot: `ping 192.168.1.100`

### "Module not found" errors
- Make sure you ran `source setup_env.sh` first
- Use `python2` (the SDK's Python), not your system Python

---

## Resources

- [NAO Documentation](http://doc.aldebaran.com/2-8/index.html)
- [Python NAOqi API Reference](http://doc.aldebaran.com/2-8/naoqi/index.html)
- [ALMotion API](http://doc.aldebaran.com/2-8/naoqi/motion/almotion.html)
- [ALTextToSpeech API](http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech.html)
