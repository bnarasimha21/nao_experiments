# NAO Robot Python Experiments

## Prerequisites

1. **NAO Robot** on the same network as your computer
2. **Robot IP address** - Press the chest button on the robot to hear it
3. **PyNAOqi SDK** - Download from [Aldebaran/SoftBank Robotics](https://www.aldebaran.com/en/support)

---

## Quick Setup

### macOS Setup

#### Step 1: Configure Environment

```bash
cd /path/to/nao_experiments
source setup_env.sh
```

Or manually set environment variables:

```bash
export PYTHONPATH="/path/to/pynaoqi-python2.7-2.8.6.23-mac64/lib/python2.7/site-packages:$PYTHONPATH"
export DYLD_LIBRARY_PATH="/path/to/pynaoqi-python2.7-2.8.6.23-mac64/lib:$DYLD_LIBRARY_PATH"
```

#### Step 2: Verify Setup

```bash
python2 test_setup.py
```

#### Step 3: Run Your First Script

```bash
python2 examples/say_hello.py <robot_ip>
```

---

### Windows Setup

#### Step 1: Download the Windows SDK

Download `pynaoqi-python2.7-2.8.6.23-win32-vs2015` from the Aldebaran/SoftBank support site.

#### Step 2: Install Python 2.7

1. Download Python 2.7 from [python.org/downloads](https://www.python.org/downloads/release/python-2718/)
2. Install to `C:\Python27`
3. Add to PATH: `C:\Python27` and `C:\Python27\Scripts`

#### Step 3: Set Environment Variables

**Option A: Command Prompt (temporary)**

```cmd
set PYTHONPATH=C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib\site-packages
set PATH=%PATH%;C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib
```

**Option B: PowerShell (temporary)**

```powershell
$env:PYTHONPATH = "C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib\site-packages"
$env:PATH += ";C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib"
```

**Option C: Permanent (System Environment Variables)**

1. Right-click **This PC** → **Properties** → **Advanced system settings**
2. Click **Environment Variables**
3. Under **User variables**, click **New**:
   - Variable name: `PYTHONPATH`
   - Variable value: `C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib\site-packages`
4. Edit **PATH** and add: `C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib`

#### Step 4: Verify Setup

```cmd
python test_setup.py
```

You should see: `SUCCESS: NAOqi loaded correctly!`

#### Step 5: Run Your First Script

```cmd
python examples\say_hello.py 192.168.1.100
```

Replace `192.168.1.100` with your robot's actual IP.

---

### Linux Setup

#### Step 1: Download the Linux SDK

Download `pynaoqi-python2.7-2.8.6.23-linux64` from the Aldebaran/SoftBank support site.

#### Step 2: Set Environment Variables

```bash
export PYTHONPATH="/path/to/pynaoqi-python2.7-2.8.6.23-linux64/lib/python2.7/site-packages:$PYTHONPATH"
export LD_LIBRARY_PATH="/path/to/pynaoqi-python2.7-2.8.6.23-linux64/lib:$LD_LIBRARY_PATH"
```

Add these to `~/.bashrc` for permanent setup.

#### Step 3: Run Scripts

```bash
python2 examples/say_hello.py <robot_ip>
```

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

### Configuration

**Using .env file (Recommended):**

Create a `.env` file in the project root with your NAO robot's IP address:

```
NAO_IP_ADDRESS=192.168.68.108
```

All example scripts will automatically use this IP address. You can still override it by passing the IP as a command-line argument.

### Usage Examples

**macOS / Linux:**
```bash
# With .env file configured:
python2 examples/say_hello.py
python2 examples/stand_sit.py stand
python2 examples/wave.py
python2 examples/dance.py

# Or override with command-line argument:
python2 examples/say_hello.py 192.168.1.100
python2 examples/stand_sit.py 192.168.1.100 stand
```

**Windows:**
```cmd
# With .env file configured:
python examples\say_hello.py
python examples\stand_sit.py stand
python examples\wave.py
python examples\dance.py

# Or override with command-line argument:
python examples\say_hello.py 192.168.1.100
python examples\stand_sit.py 192.168.1.100 stand
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
        print("Usage: python script.py <robot_ip>")
        sys.exit(1)
    
    robot_ip = sys.argv[1]
    main(robot_ip)
```

---

## Troubleshooting

### "Cannot connect to robot"
- Ensure NAO is powered on and connected to the network
- Verify the IP address is correct (press chest button to hear it)
- Check if your firewall allows connections on port 9559
- Try pinging the robot: `ping <robot_ip>`
- Ensure your computer is on the same WiFi network as NAO

### "Module not found" errors
- Make sure environment variables are set correctly
- On macOS/Linux: run `source setup_env.sh` first
- On Windows: verify `PYTHONPATH` is set
- Use Python 2.7 (not Python 3)

### Windows-specific issues
- Use backslashes in paths: `examples\say_hello.py`
- Run Command Prompt as Administrator if permission errors occur
- Make sure Visual C++ Redistributable 2015 is installed

### macOS-specific issues
- If you have VPN or Docker running, try disabling them
- Toggle WiFi off/on to reset network routing
- On newer macOS, you may need to allow the app in Security settings

---

## Resources

- [NAO Documentation](http://doc.aldebaran.com/2-8/index.html)
- [Python NAOqi API Reference](http://doc.aldebaran.com/2-8/naoqi/index.html)
- [ALMotion API](http://doc.aldebaran.com/2-8/naoqi/motion/almotion.html)
- [ALTextToSpeech API](http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech.html)
- [SDK Downloads](https://www.aldebaran.com/en/support)
