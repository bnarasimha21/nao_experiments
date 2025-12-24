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
    Add to your .env file:
    NAO_IP_ADDRESS=192.168.1.100
    OPENAI_API_KEY=sk-your-api-key-here
"""

from __future__ import print_function
import sys
import os
import json
import time
import tempfile
import struct

# Python 2/3 compatibility for HTTP requests
try:
    from urllib2 import Request, urlopen, HTTPError, URLError
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nao_utils import get_robot_ip, get_openai_api_key, get_openai_model

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


class NaoAssistant:
    """NAO AI Assistant that listens, thinks, and speaks."""
    
    def __init__(self, robot_ip, port=9559):
        self.robot_ip = robot_ip
        self.port = port
        self.api_key = get_openai_api_key()
        self.model = get_openai_model()
        self.conversation_history = []
        
        # Connect to NAO services
        print("Connecting to NAO at %s..." % robot_ip)
        self.tts = ALProxy("ALTextToSpeech", robot_ip, port)
        self.memory = ALProxy("ALMemory", robot_ip, port)
        self.leds = ALProxy("ALLeds", robot_ip, port)
        self.audio_recorder = ALProxy("ALAudioRecorder", robot_ip, port)
        self.audio_device = ALProxy("ALAudioDevice", robot_ip, port)
        
        # Configure TTS
        self.tts.setParameter("speed", 85)
        
        print("Connected successfully!")
    
    def set_eye_color(self, color):
        """Set NAO's eye LED color.
        
        Colors: 'white', 'blue', 'green', 'yellow', 'red', 'off'
        """
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
        print("NAO: %s" % text)
        self.tts.say(str(text))
    
    def record_audio(self, duration=RECORD_DURATION):
        """Record audio from NAO's microphone.
        
        Returns path to the recorded WAV file.
        """
        # Create temp file path on the robot
        filename = "/home/nao/recording.wav"
        
        # Configure audio recorder
        # Channels: [front, rear, left, right] - we use front mic
        self.audio_recorder.stopMicrophonesRecording()  # Stop any existing recording
        time.sleep(0.2)
        
        # Start recording (16kHz, mono, WAV format)
        self.audio_recorder.startMicrophonesRecording(
            filename,
            "wav",
            SAMPLE_RATE,
            [1, 0, 0, 0]  # Front microphone only
        )
        
        print("Recording for %d seconds..." % duration)
        time.sleep(duration)
        
        # Stop recording
        self.audio_recorder.stopMicrophonesRecording()
        print("Recording complete.")
        
        return filename
    
    def get_audio_from_robot(self, remote_path):
        """Download audio file from robot to local temp file."""
        try:
            # Use SSH/SCP to get file, or read via ALFileManager
            file_manager = ALProxy("ALFileManager", self.robot_ip, self.port)
            
            # Read the file data
            with open(remote_path, 'rb') as f:
                audio_data = f.read()
            
            # Save to local temp file
            local_path = tempfile.mktemp(suffix='.wav')
            with open(local_path, 'wb') as f:
                f.write(audio_data)
            
            return local_path
        except Exception as e:
            print("Error getting audio: %s" % str(e))
            return None
    
    def transcribe_audio_file(self, audio_path):
        """Send audio to OpenAI Whisper API for transcription.
        
        Uses multipart/form-data POST request.
        """
        if not os.path.exists(audio_path):
            print("Audio file not found: %s" % audio_path)
            return None
        
        # Read the audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Build multipart form data manually (Python 2 compatible)
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        
        body = []
        # Add file field
        body.append('--%s' % boundary)
        body.append('Content-Disposition: form-data; name="file"; filename="audio.wav"')
        body.append('Content-Type: audio/wav')
        body.append('')
        
        # Add model field
        body_str = '\r\n'.join(body).encode('utf-8')
        body_str += b'\r\n' + audio_data + b'\r\n'
        body_str += ('--%s\r\n' % boundary).encode('utf-8')
        body_str += b'Content-Disposition: form-data; name="model"\r\n\r\n'
        body_str += b'whisper-1\r\n'
        body_str += ('--%s--\r\n' % boundary).encode('utf-8')
        
        headers = {
            'Authorization': 'Bearer %s' % self.api_key,
            'Content-Type': 'multipart/form-data; boundary=%s' % boundary
        }
        
        try:
            request = Request(OPENAI_WHISPER_URL, data=body_str, headers=headers)
            response = urlopen(request, timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            return result.get('text', '').strip()
        except HTTPError as e:
            print("Whisper API Error: %s" % e.code)
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else ''
            print("Details: %s" % error_body)
            return None
        except Exception as e:
            print("Transcription error: %s" % str(e))
            return None
    
    def transcribe_with_whisper(self, audio_path):
        """Transcribe audio using OpenAI Whisper API via curl (more reliable)."""
        import subprocess
        
        try:
            # Use curl for multipart upload (more reliable than urllib2)
            cmd = [
                'curl', '-s',
                '-X', 'POST',
                OPENAI_WHISPER_URL,
                '-H', 'Authorization: Bearer %s' % self.api_key,
                '-F', 'file=@%s' % audio_path,
                '-F', 'model=whisper-1'
            ]
            
            result = subprocess.check_output(cmd)
            data = json.loads(result)
            return data.get('text', '').strip()
        except subprocess.CalledProcessError as e:
            print("Curl error: %s" % str(e))
            return None
        except Exception as e:
            print("Transcription error: %s" % str(e))
            return None
    
    def get_gpt_response(self, user_message):
        """Get response from ChatGPT."""
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
            request = Request(
                OPENAI_CHAT_URL,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            response = urlopen(request, timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in result and len(result['choices']) > 0:
                reply = result['choices'][0]['message']['content'].strip()
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": reply})
                
                # Keep history manageable
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return reply
            return "I didn't understand that. Could you try again?"
            
        except HTTPError as e:
            print("GPT API Error: %s" % e.code)
            return "I'm having trouble thinking right now. Please try again."
        except Exception as e:
            print("Error: %s" % str(e))
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
        """Main conversation loop: listen, transcribe, respond."""
        # Visual feedback - listening (blue eyes)
        self.set_eye_color('blue')
        self.say("I'm listening")
        
        # Record audio
        try:
            audio_file = self.record_audio(duration=RECORD_DURATION)
            
            # Eyes yellow while processing
            self.set_eye_color('yellow')
            print("Transcribing speech...")
            
            # Transcribe using Whisper
            # Note: The audio file is on the robot, we need to access it
            # For simplicity, we'll use a local recording approach
            transcription = self.transcribe_with_whisper(audio_file)
            
            if not transcription:
                self.set_eye_color('red')
                self.say("I couldn't understand that. Please try again.")
                self.set_eye_color('white')
                return
            
            print("You said: %s" % transcription)
            
            # Get GPT response
            print("Getting response...")
            response = self.get_gpt_response(transcription)
            
            # Eyes green while speaking
            self.set_eye_color('green')
            self.say(response)
            
            # Reset to white
            self.set_eye_color('white')
            
        except Exception as e:
            print("Error in conversation: %s" % str(e))
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
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.say("Goodbye!")
            self.set_eye_color('white')


def run_demo_mode(robot_ip, port=9559):
    """Run in demo mode - type what you'd say and NAO responds."""
    print("\n" + "=" * 60)
    print("DEMO MODE - Simulating voice conversation")
    print("=" * 60)
    print("Type what you would SAY to NAO.")
    print("NAO will respond using GPT and speak the answer.")
    print("Type 'quit' to exit.")
    print("=" * 60 + "\n")
    
    api_key = get_openai_api_key()
    model = get_openai_model()
    
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    leds = ALProxy("ALLeds", robot_ip, port)
    tts.setParameter("speed", 85)
    
    conversation_history = []
    
    # Greeting
    greeting = "Hello! I'm NAO, your AI assistant. What would you like to talk about?"
    print("NAO: %s" % greeting)
    tts.say(greeting)
    
    while True:
        try:
            user_input = raw_input("\nYou (speaking): ").strip()
        except NameError:
            user_input = input("\nYou (speaking): ").strip()
        
        if not user_input:
            continue
        if user_input.lower() in ['quit', 'exit', 'bye']:
            leds.fadeRGB("FaceLeds", 0x00FF00, 0.3)
            farewell = "Goodbye! It was nice talking to you!"
            print("NAO: %s" % farewell)
            tts.say(farewell)
            leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)
            break
        
        # Show thinking
        leds.fadeRGB("FaceLeds", 0xFFFF00, 0.3)
        print("(NAO is thinking...)")
        
        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        # Call GPT
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % api_key
        }
        
        try:
            request = Request(
                OPENAI_CHAT_URL,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            response = urlopen(request, timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            
            reply = result['choices'][0]['message']['content'].strip()
            
            # Update history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": reply})
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            # Speak response
            leds.fadeRGB("FaceLeds", 0x00FF00, 0.3)
            print("NAO: %s" % reply)
            tts.say(reply)
            leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)
            
        except Exception as e:
            print("Error: %s" % str(e))
            leds.fadeRGB("FaceLeds", 0xFF0000, 0.3)
            tts.say("I had trouble processing that.")
            leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)


def main():
    robot_ip = get_robot_ip()
    
    if not robot_ip:
        print("Usage: python nao_assistant.py [robot_ip] [mode]")
        print("Or set NAO_IP_ADDRESS in .env file")
        print("\nModes:")
        print("  listen - Touch head to talk (default)")
        print("  demo   - Type what you'd say")
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
    
    # Check for mode
    mode = "demo"  # Default to demo for now (more reliable)
    for arg in sys.argv[1:]:
        if arg.lower() == "listen":
            mode = "listen"
        elif arg.lower() == "demo":
            mode = "demo"
    
    print("Connecting to NAO at: %s" % robot_ip)
    
    if mode == "listen":
        assistant = NaoAssistant(robot_ip)
        assistant.run()
    else:
        run_demo_mode(robot_ip)


if __name__ == "__main__":
    main()

