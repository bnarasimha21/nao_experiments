# Windows Setup Guide for NAO Experiments

This guide will help you set up your Windows development environment to test NAO robot examples.

## Prerequisites Checklist

- [ ] Python 2.7 installed (✅ Found at `C:\Python27`)
- [ ] PyNAOqi SDK downloaded
- [ ] Environment variables configured
- [ ] Setup verified

## Step-by-Step Setup

### Step 1: Install Python 2.7 (if not already installed)

Python 2.7.18 is already installed at `C:\Python27`. ✅

If you need to install it:
1. Download from: https://www.python.org/downloads/release/python-2718/
2. Install to: `C:\Python27`
3. During installation, check "Add python.exe to Path" (optional, we'll handle it in setup scripts)

### Step 2: Download PyNAOqi SDK

1. Go to: https://www.aldebaran.com/en/support
2. Download: `pynaoqi-python2.7-2.8.6.23-win32-vs2015`
3. Extract the SDK to a location like:
   - `C:\pynaoqi-python2.7-2.8.6.23-win32-vs2015`
   - Or `C:\NAO\pynaoqi-python2.7-2.8.6.23-win32-vs2015`
   - Or any folder you prefer

**Note:** Remember the full path where you extract it - you'll need it in the next step!

### Step 3: Configure Environment Variables

You have two options:

#### Option A: Use Setup Scripts (Recommended for Testing)

**PowerShell:**
```powershell
# 1. Edit setup_env.ps1 and update the SDK_PATH variable with your actual SDK path
# 2. Run the setup script:
.\setup_env.ps1
```

**Command Prompt:**
```cmd
# 1. Edit setup_env.bat and update the SDK_PATH variable with your actual SDK path
# 2. Run the setup script:
setup_env.bat
```

**Note:** These scripts set environment variables for the current session only. You'll need to run them each time you open a new terminal.

#### Option B: Set Permanent Environment Variables

1. Right-click **This PC** → **Properties** → **Advanced system settings**
2. Click **Environment Variables**
3. Under **User variables**, click **New**:
   - Variable name: `PYTHONPATH`
   - Variable value: `C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib\site-packages`
     (Replace with your actual SDK path)
4. Edit **PATH** variable and add:
   - `C:\path\to\pynaoqi-python2.7-2.8.6.23-win32-vs2015\lib`
   - `C:\Python27`
   - `C:\Python27\Scripts`

### Step 4: Verify Setup

After configuring environment variables, test your setup:

```cmd
python test_setup.py
```

You should see:
```
🎉 SUCCESS: NAOqi loaded correctly!
```

If you see errors, check the troubleshooting section below.

### Step 5: Run Your First NAO Example

Once setup is verified, you can test with a NAO robot:

```cmd
python examples\say_hello.py <robot_ip>
```

Replace `<robot_ip>` with your robot's IP address (press the chest button on NAO to hear it).

## Troubleshooting

### "Cannot import NAOqi module"
- Make sure you've downloaded and extracted the PyNAOqi SDK
- Verify the `PYTHONPATH` environment variable points to: `C:\path\to\pynaoqi\lib\site-packages`
- Make sure you updated the `SDK_PATH` in `setup_env.ps1` or `setup_env.bat`
- Run the setup script again: `.\setup_env.ps1` or `setup_env.bat`

### "Python 2.7 is required"
- Make sure Python 2.7 is installed at `C:\Python27`
- If installed elsewhere, update the setup scripts with the correct path
- Verify with: `C:\Python27\python.exe --version`

### "Cannot connect to robot"
- Ensure NAO is powered on and connected to the network
- Verify the IP address is correct (press chest button to hear it)
- Check if your firewall allows connections on port 9559
- Try pinging the robot: `ping <robot_ip>`
- Ensure your computer is on the same WiFi network as NAO

### Visual C++ Redistributable Error
If you see DLL errors, install:
- Visual C++ Redistributable for Visual Studio 2015
- Download from Microsoft's website

## Quick Reference

**Setup scripts:**
- `setup_env.ps1` - PowerShell setup script
- `setup_env.bat` - Command Prompt setup script

**Test script:**
- `test_setup.py` - Verifies your setup

**Example scripts:**
- `examples\say_hello.py` - Make NAO speak
- `examples\wave.py` - Wave hello
- `examples\dance.py` - Dance routine
- `examples\move_head.py` - Look around
- `examples\stand_sit.py` - Stand/sit/crouch
- `examples\walk.py` - Walk forward and turn
- `examples\leds.py` - Change LED colors
- `examples\sensors.py` - Read sensors

## Next Steps

1. Download the PyNAOqi SDK
2. Update `SDK_PATH` in `setup_env.ps1` or `setup_env.bat`
3. Run the setup script
4. Run `python test_setup.py` to verify
5. Connect to your NAO robot and test examples!

