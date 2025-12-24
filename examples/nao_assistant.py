#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
NAO AI Assistant - Listen, Think, Speak

NAO listens to your question using its microphone, sends audio to 
OpenAI Whisper for transcription, gets a GPT response, and speaks it back.

Usage:
    python2 nao_assistant.py [robot_ip]
    
Touch NAO's head to start a conversation!

Setup:
    1. Add to your .env file:
       NAO_IP_ADDRESS=192.168.1.100
       OPENAI_API_KEY=sk-your-api-key-here
       NAO_PASSWORD=nao
    
    2. Install file transfer tool (needed to copy audio files from NAO):
       
       macOS:
         brew install hudochenkov/sshpass/sshpass
       
       Linux (Ubuntu/Debian):
         sudo apt-get install sshpass
       
       Windows:
         Option A - Use PuTTY's pscp:
           1. Download PuTTY from https://www.putty.org/
           2. Add PuTTY folder to PATH
           (Script will auto-detect and use pscp on Windows)
         
         Option B - Use WSL (Windows Subsystem for Linux):
           1. Install WSL: wsl --install
           2. In WSL terminal: sudo apt-get install sshpass
           3. Run this script from WSL
"""

from __future__ import print_function
import sys
import os
import json
import time
import tempfile
import subprocess
import platform
import traceback

# Python 2/3 compatibility for HTTP requests
try:
    from urllib2 import Request, urlopen, HTTPError, URLError
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip, get_openai_api_key, get_openai_model, load_env_file

try:
    from naoqi import ALProxy
except ImportError:
    print("Error: NAOqi not found. Please set up the environment first.")
    print("Run: source setup_env.sh")
    sys.exit(1)


# Configuration
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"
RECORD_DURATION = 5  # seconds to record
SAMPLE_RATE = 16000  # Audio sample rate

SYSTEM_PROMPT = """You are NAO, a friendly and helpful humanoid robot assistant.
You have a cheerful personality and love to help people.
Keep your responses concise (2-3 sentences max) since you'll be speaking them aloud.
Be friendly, warm, and occasionally add a bit of robot humor.
If asked about your capabilities, mention that you can move, dance, wave, and have conversations."""


def get_nao_password():
    """Get NAO SSH password from environment."""
    env_vars = load_env_file()
    return env_vars.get('NAO_PASSWORD', 'nao')  # Default NAO password is 'nao'


def is_windows():
    """Check if running on Windows."""
    return platform.system() == 'Windows'


class NaoAssistant:
    """NAO AI Assistant that listens, thinks, and speaks."""
    
    def __init__(self, robot_ip, port=9559):
        self.robot_ip = robot_ip
        self.port = port
        self.api_key = get_openai_api_key()
        self.model = get_openai_model()
        self.conversation_history = []
        self.nao_password = get_nao_password()
        
        # Connect to NAO services
        print("Connecting to NAO at %s..." % robot_ip)
        self.tts = ALProxy("ALTextToSpeech", robot_ip, port)
        self.memory = ALProxy("ALMemory", robot_ip, port)
        self.leds = ALProxy("ALLeds", robot_ip, port)
        self.audio_recorder = ALProxy("ALAudioRecorder", robot_ip, port)
        
        # Configure TTS
        self.tts.setParameter("speed", 85)
        
        print("Connected successfully!")
    
    def set_eye_color(self, color):
        """Set NAO's eye LED color."""
        colors = {
            'white': 0xFFFFFF,
            'blue': 0x0000FF,
            'green': 0x00FF00,
            'yellow': 0xFFFF00,
            'red': 0xFF0000,
            'cyan': 0x00FFFF,
            'magenta': 0xFF00FF,
            'off': 0x000000
        }
        hex_color = colors.get(color, 0xFFFFFF)
        self.leds.fadeRGB("FaceLeds", hex_color, 0.3)
    
    def say(self, text):
        """Make NAO speak."""
        if text is None:
            text = "I'm sorry, I couldn't process that."
        text = str(text).strip()
        if not text:
            text = "I'm sorry, I couldn't process that."
        print("NAO: %s" % text)
        self.tts.say(text)
    
    def record_audio_on_nao(self, duration=RECORD_DURATION):
        """
        Record audio from NAO's microphone.
        The file is saved ON THE ROBOT at /home/nao/recording.wav
        
        Returns the remote path on NAO.
        """
        remote_path = "/home/nao/recording.wav"
        
        # Stop any existing recording first
        try:
            self.audio_recorder.stopMicrophonesRecording()
        except:
            pass
        time.sleep(0.3)
        
        print("[DEBUG] Recording: Starting...")
        print("Recording for %d seconds..." % duration)
        
        # Start recording
        # Parameters: filename, format, sampleRate, channels
        # channels: [front, rear, left, right] microphones
        self.audio_recorder.startMicrophonesRecording(
            remote_path,
            "wav",
            SAMPLE_RATE,
            [1, 0, 0, 0]  # Front microphone only
        )
        
        # Wait for recording duration
        time.sleep(duration)
        
        # Stop recording
        self.audio_recorder.stopMicrophonesRecording()
        print("Recording complete. File saved on NAO: %s" % remote_path)
        
        # Wait a bit for file to be fully written
        time.sleep(0.5)
        
        return remote_path
    
    def copy_file_from_nao(self, remote_path):
        """
        Copy a file from NAO to local machine using SCP.
        Supports both Unix (scp/sshpass) and Windows (pscp).
        
        Returns local path to the copied file.
        """
        local_path = tempfile.mktemp(suffix='.wav')
        
        print("[DEBUG] Audio Transfer: Copying from NAO...")
        print("[DEBUG] Audio Transfer: Remote: %s" % remote_path)
        print("[DEBUG] Audio Transfer: Local: %s" % local_path)
        
        if is_windows():
            return self._copy_file_windows(remote_path, local_path)
        else:
            return self._copy_file_unix(remote_path, local_path)
    
    def _copy_file_unix(self, remote_path, local_path):
        """Copy file using scp/sshpass on Unix/macOS."""
        try:
            # First, try with sshpass (most reliable for automation)
            print("[DEBUG] Audio Transfer: Trying sshpass + scp...")
            cmd_with_pass = [
                'sshpass', '-p', self.nao_password,
                'scp',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                'nao@%s:%s' % (self.robot_ip, remote_path),
                local_path
            ]
            
            result = subprocess.call(
                cmd_with_pass, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            if result == 0 and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print("[DEBUG] Audio Transfer: Success! (%d bytes)" % file_size)
                return local_path
            
            # Fallback: try without sshpass (if SSH keys are set up)
            print("[DEBUG] Audio Transfer: Trying scp without password...")
            cmd_no_pass = [
                'scp',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'BatchMode=yes',
                'nao@%s:%s' % (self.robot_ip, remote_path),
                local_path
            ]
            
            result = subprocess.call(
                cmd_no_pass,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result == 0 and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print("[DEBUG] Audio Transfer: Success! (%d bytes)" % file_size)
                return local_path
            
            print("[DEBUG] Audio Transfer: FAILED")
            print("Make sure sshpass is installed:")
            print("  macOS: brew install hudochenkov/sshpass/sshpass")
            print("  Linux: sudo apt-get install sshpass")
            return None
            
        except Exception as e:
            print("[DEBUG] Audio Transfer: Error: %s" % str(e))
            return None
    
    def _copy_file_windows(self, remote_path, local_path):
        """Copy file using pscp (PuTTY) on Windows."""
        try:
            print("[DEBUG] Audio Transfer: Trying pscp (PuTTY)...")
            cmd = [
                'pscp',
                '-pw', self.nao_password,
                '-batch',
                'nao@%s:%s' % (self.robot_ip, remote_path),
                local_path
            ]
            
            result = subprocess.call(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result == 0 and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print("[DEBUG] Audio Transfer: Success! (%d bytes)" % file_size)
                return local_path
            
            print("[DEBUG] Audio Transfer: FAILED")
            print("Make sure PuTTY is installed and pscp is in PATH.")
            print("Download from: https://www.putty.org/")
            return None
            
        except Exception as e:
            print("[DEBUG] Audio Transfer: Error: %s" % str(e))
            return None
    
    def transcribe_with_whisper(self, audio_path):
        """
        Transcribe audio using OpenAI Whisper API.
        Uses curl for reliable multipart upload.
        """
        if not audio_path or not os.path.exists(audio_path):
            print("[DEBUG] Whisper: Audio file not found: %s" % audio_path)
            return None
        
        file_size = os.path.getsize(audio_path)
        print("[DEBUG] Whisper: Transcribing audio (%d bytes)..." % file_size)
        
        if file_size < 1000:
            print("[DEBUG] Whisper: WARNING - File seems too small!")
        
        try:
            # Use curl for multipart upload (works on all platforms)
            if is_windows():
                curl_cmd = 'curl.exe'
            else:
                curl_cmd = 'curl'
            
            cmd = [
                curl_cmd, '-s',
                '-X', 'POST',
                OPENAI_WHISPER_URL,
                '-H', 'Authorization: Bearer %s' % self.api_key,
                '-F', 'file=@%s' % audio_path,
                '-F', 'model=whisper-1'
            ]
            
            print("[DEBUG] Whisper: Sending to API...")
            result = subprocess.check_output(cmd)
            
            print("[DEBUG] Whisper: Response received (%d bytes)" % len(result))
            data = json.loads(result)
            
            if 'text' in data:
                transcription = data['text'].strip()
                print("[DEBUG] Whisper: Transcription: \"%s\"" % transcription)
                return transcription
            elif 'error' in data:
                print("[DEBUG] Whisper: API error: %s" % data['error'])
                return None
            else:
                print("[DEBUG] Whisper: Unexpected response: %s" % result[:200])
                return None
                
        except subprocess.CalledProcessError as e:
            print("[DEBUG] Whisper: Curl error: %s" % str(e))
            return None
        except ValueError as e:
            print("[DEBUG] Whisper: JSON parse error: %s" % str(e))
            return None
        except Exception as e:
            print("[DEBUG] Whisper: Error: %s" % str(e))
            print("[DEBUG] Whisper: Traceback: %s" % traceback.format_exc())
            return None
    
    def get_gpt_response(self, user_message):
        """Get response from ChatGPT."""
        print("[DEBUG] GPT: Processing message: \"%s\"" % user_message[:50])
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % self.api_key
        }
        
        try:
            print("[DEBUG] GPT: Sending request...")
            request = Request(
                OPENAI_CHAT_URL,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            response = urlopen(request, timeout=30)
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                if 'message' in choice:
                    content = choice['message'].get('content')
                    if content:
                        reply = str(content).strip()
                        print("[DEBUG] GPT: Response: \"%s\"" % reply[:50])
                        
                        # Update conversation history
                        self.conversation_history.append({"role": "user", "content": user_message})
                        self.conversation_history.append({"role": "assistant", "content": reply})
                        
                        # Keep history manageable
                        if len(self.conversation_history) > 20:
                            self.conversation_history = self.conversation_history[-20:]
                        
                        return reply
            
            print("[DEBUG] GPT: No valid response in API result")
            return "I didn't understand that. Could you try again?"
            
        except HTTPError as e:
            print("[DEBUG] GPT: HTTP Error %s" % e.code)
            return "I'm having trouble thinking right now. Please try again."
        except Exception as e:
            print("[DEBUG] GPT: Error: %s" % str(e))
            return "Something went wrong. Please try again."
    
    def is_head_touched(self):
        """Check if any head sensor is touched."""
        try:
            front = self.memory.getData("Device/SubDeviceList/Head/Touch/Front/Sensor/Value")
            middle = self.memory.getData("Device/SubDeviceList/Head/Touch/Middle/Sensor/Value")
            rear = self.memory.getData("Device/SubDeviceList/Head/Touch/Rear/Sensor/Value")
            return front > 0.5 or middle > 0.5 or rear > 0.5
        except:
            return False
    
    def listen_and_respond(self):
        """Full conversation flow: listen, transcribe, respond."""
        
        # Step 1: Visual feedback - listening
        self.set_eye_color('blue')
        self.say("I'm listening")
        
        try:
            # Step 2: Record audio on NAO
            remote_audio_path = self.record_audio_on_nao(duration=RECORD_DURATION)
            
            # Step 3: Copy file from NAO to local machine
            self.set_eye_color('cyan')
            local_audio_path = self.copy_file_from_nao(remote_audio_path)
            
            if not local_audio_path:
                self.set_eye_color('red')
                self.say("I couldn't access the recording. Please check the setup.")
                self.set_eye_color('white')
                return
            
            # Step 4: Transcribe with Whisper
            self.set_eye_color('yellow')
            transcription = self.transcribe_with_whisper(local_audio_path)
            
            # Clean up local file
            try:
                os.remove(local_audio_path)
            except:
                pass
            
            if not transcription:
                self.set_eye_color('red')
                self.say("I couldn't understand what you said. Please try again.")
                self.set_eye_color('white')
                return
            
            print("\nYou said: \"%s\"" % transcription)
            
            # Step 5: Get GPT response
            print("Getting GPT response...")
            response = self.get_gpt_response(transcription)
            
            # Step 6: Speak the response
            self.set_eye_color('green')
            self.say(response)
            
            # Reset
            self.set_eye_color('white')
            
        except Exception as e:
            print("Error in conversation: %s" % str(e))
            print("Traceback: %s" % traceback.format_exc())
            self.set_eye_color('red')
            self.say("I encountered an error. Please try again.")
            self.set_eye_color('white')
    
    def run(self):
        """Main loop - wait for head touch to start conversation."""
        print("\n" + "=" * 60)
        print("NAO AI Assistant Ready!")
        print("=" * 60)
        print("\nTouch NAO's head to start talking.")
        print("Press Ctrl+C to exit.")
        print("=" * 60 + "\n")
        
        self.set_eye_color('white')
        self.say("Hello! Touch my head when you want to talk to me.")
        
        try:
            while True:
                if self.is_head_touched():
                    self.listen_and_respond()
                    time.sleep(1)  # Debounce
                    print("\nTouch my head to talk again...")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.say("Goodbye!")
            self.set_eye_color('white')


def print_setup_instructions():
    """Print setup instructions for the current platform."""
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS")
    print("=" * 60)
    
    if is_windows():
        print("""
Windows Setup:

1. Install PuTTY (includes pscp for file transfer):
   - Download from: https://www.putty.org/
   - Run the installer
   - Make sure to add PuTTY to your PATH during installation
   
   OR use the standalone pscp.exe:
   - Download pscp.exe from the PuTTY website
   - Place it in C:\\Windows or add its folder to PATH

2. Add to your .env file:
   NAO_IP_ADDRESS=192.168.1.100
   OPENAI_API_KEY=sk-your-api-key-here
   NAO_PASSWORD=nao

3. Run:
   python examples\\nao_assistant.py
""")
    else:
        print("""
macOS Setup:

1. Install sshpass:
   brew install hudochenkov/sshpass/sshpass

2. Add to your .env file:
   NAO_IP_ADDRESS=192.168.1.100
   OPENAI_API_KEY=sk-your-api-key-here
   NAO_PASSWORD=nao

3. Run:
   python2 examples/nao_assistant.py

---

Linux Setup:

1. Install sshpass:
   sudo apt-get install sshpass

2. Add to your .env file:
   NAO_IP_ADDRESS=192.168.1.100
   OPENAI_API_KEY=sk-your-api-key-here
   NAO_PASSWORD=nao

3. Run:
   python2 examples/nao_assistant.py
""")
    print("=" * 60)


def main():
    robot_ip = get_robot_ip()
    
    if not robot_ip:
        print("Usage: python nao_assistant.py [robot_ip]")
        print("Or set NAO_IP_ADDRESS in .env file")
        print_setup_instructions()
        sys.exit(1)
    
    # Check API key
    api_key = get_openai_api_key()
    if not api_key:
        print("=" * 60)
        print("ERROR: OpenAI API key not found!")
        print("=" * 60)
        print("\nAdd to your .env file:")
        print("  OPENAI_API_KEY=sk-your-api-key-here")
        sys.exit(1)
    
    print("OpenAI API key: %s...%s" % (api_key[:8], api_key[-4:]))
    print("Model: %s" % get_openai_model())
    print("NAO IP: %s" % robot_ip)
    print("Platform: %s" % platform.system())
    
    # Start the assistant
    assistant = NaoAssistant(robot_ip)
    assistant.run()


if __name__ == "__main__":
    main()
