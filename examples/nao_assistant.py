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
        if text is None:
            text = "I'm sorry, I couldn't process that."
        text = str(text).strip()
        if not text:
            text = "I'm sorry, I couldn't process that."
        print("NAO: %s" % text)
        self.tts.say(text)
    
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
        
        # Wait a bit for file to be fully written
        print("[DEBUG] Recording: Waiting for file to be written...")
        time.sleep(0.5)
        
        # Verify file exists using ALFileManager
        try:
            file_manager = ALProxy("ALFileManager", self.robot_ip, self.port)
            if file_manager.fileExists(filename):
                try:
                    if hasattr(file_manager, 'getFileSize'):
                        file_size = file_manager.getFileSize(filename)
                        print("[DEBUG] Recording: File exists on robot: %s (size: %d bytes)" % (filename, file_size))
                    else:
                        print("[DEBUG] Recording: File exists on robot: %s" % filename)
                except Exception as e:
                    print("[DEBUG] Recording: File exists but could not get size: %s" % str(e))
            else:
                print("[DEBUG] Recording: WARNING - File does not exist yet, may need more time")
                # Wait a bit more
                time.sleep(1.0)
                if file_manager.fileExists(filename):
                    try:
                        if hasattr(file_manager, 'getFileSize'):
                            file_size = file_manager.getFileSize(filename)
                            print("[DEBUG] Recording: File now exists (size: %d bytes)" % file_size)
                        else:
                            print("[DEBUG] Recording: File now exists")
                    except:
                        print("[DEBUG] Recording: File now exists")
                else:
                    print("[DEBUG] Recording: ERROR - File still does not exist after waiting")
                    # Try to list directory to see what's there
                    try:
                        parent_dir = os.path.dirname(filename)
                        if hasattr(file_manager, 'listFiles'):
                            files = file_manager.listFiles(parent_dir)
                            print("[DEBUG] Recording: Files in %s: %s" % (parent_dir, str(files)))
                    except Exception as e2:
                        print("[DEBUG] Recording: Could not list directory: %s" % str(e2))
        except Exception as e:
            print("[DEBUG] Recording: Could not verify file existence: %s" % str(e))
            import traceback
            print("[DEBUG] Recording: Traceback: %s" % traceback.format_exc())
        
        return filename
    
    def get_audio_from_robot(self, remote_path):
        """Download audio file from robot to local temp file using multiple methods."""
        try:
            print("[DEBUG] Audio Transfer: Downloading file from robot...")
            print("[DEBUG] Audio Transfer: Remote path: %s" % remote_path)
            
            # Use ALFileManager to check if file exists
            file_manager = ALProxy("ALFileManager", self.robot_ip, self.port)
            
            print("[DEBUG] Audio Transfer: Checking if file exists on robot...")
            if not file_manager.fileExists(remote_path):
                print("[DEBUG] Audio Transfer: ERROR - File does not exist on robot!")
                print("[DEBUG] Audio Transfer: This might mean:")
                print("[DEBUG] Audio Transfer:   1. Recording didn't complete properly")
                print("[DEBUG] Audio Transfer:   2. File path is incorrect")
                print("[DEBUG] Audio Transfer:   3. File hasn't been written yet (try waiting)")
                
                # Try listing the directory to see what files exist
                try:
                    parent_dir = os.path.dirname(remote_path)
                    print("[DEBUG] Audio Transfer: Checking parent directory: %s" % parent_dir)
                    # Note: ALFileManager might have listFiles method
                    if hasattr(file_manager, 'listFiles'):
                        files = file_manager.listFiles(parent_dir)
                        print("[DEBUG] Audio Transfer: Files in directory: %s" % str(files))
                except Exception as e:
                    print("[DEBUG] Audio Transfer: Could not list directory: %s" % str(e))
                
                return None
            
            # Try to get file size if method exists
            try:
                if hasattr(file_manager, 'getFileSize'):
                    file_size = file_manager.getFileSize(remote_path)
                    print("[DEBUG] Audio Transfer: File exists on robot (size: %d bytes)" % file_size)
                else:
                    print("[DEBUG] Audio Transfer: File exists on robot")
            except Exception as e:
                print("[DEBUG] Audio Transfer: Could not get file size: %s" % str(e))
            
            print("[DEBUG] Audio Transfer: Attempting download...")
            
            # Create local temp file
            local_path = tempfile.mktemp(suffix='.wav')
            print("[DEBUG] Audio Transfer: Local path: %s" % local_path)
            
            import subprocess
            import shutil
            
            # Method 1: Try SCP (if available)
            scp_available = shutil.which('scp') is not None
            if scp_available:
                print("[DEBUG] Audio Transfer: Method 1 - Trying SCP...")
                scp_cmd = ['scp', '-o', 'StrictHostKeyChecking=no', 
                          'nao@%s:%s' % (self.robot_ip, remote_path), local_path]
                try:
                    result = subprocess.check_output(scp_cmd, stderr=subprocess.STDOUT, timeout=10)
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        print("[DEBUG] Audio Transfer: SCP download successful!")
                        print("[DEBUG] Audio Transfer: File size: %d bytes" % os.path.getsize(local_path))
                        return local_path
                except subprocess.CalledProcessError as e:
                    print("[DEBUG] Audio Transfer: SCP failed: %s" % str(e.output if hasattr(e, 'output') else str(e)))
                except subprocess.TimeoutExpired:
                    print("[DEBUG] Audio Transfer: SCP timed out")
                except Exception as e:
                    print("[DEBUG] Audio Transfer: SCP error: %s" % str(e))
            
            # Method 2: Try SFTP with paramiko (if available)
            try:
                import paramiko
                print("[DEBUG] Audio Transfer: Method 2 - Trying SFTP with paramiko...")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.robot_ip, username='nao', password='nao', timeout=10)
                sftp = ssh.open_sftp()
                sftp.get(remote_path, local_path)
                sftp.close()
                ssh.close()
                if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                    print("[DEBUG] Audio Transfer: SFTP download successful!")
                    print("[DEBUG] Audio Transfer: File size: %d bytes" % os.path.getsize(local_path))
                    return local_path
            except ImportError:
                print("[DEBUG] Audio Transfer: paramiko not available (install with: pip install paramiko)")
            except Exception as e:
                print("[DEBUG] Audio Transfer: SFTP failed: %s" % str(e))
            
            # Method 3: Try using ALFileManager file operations
            # Some NAOqi versions might support file reading
            try:
                print("[DEBUG] Audio Transfer: Method 3 - Trying ALFileManager...")
                # Try to use file manager to read file (if method exists)
                if hasattr(file_manager, 'fileGetContents'):
                    file_data = file_manager.fileGetContents(remote_path)
                    with open(local_path, 'wb') as f:
                        f.write(file_data)
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        print("[DEBUG] Audio Transfer: ALFileManager download successful!")
                        return local_path
            except Exception as e:
                print("[DEBUG] Audio Transfer: ALFileManager method failed: %s" % str(e))
            
            # All methods failed
            print("[DEBUG] Audio Transfer: ERROR - All download methods failed!")
            print("[DEBUG] Audio Transfer: Solutions:")
            print("[DEBUG] Audio Transfer:   1. Install SCP (part of OpenSSH on Windows 10+)")
            print("[DEBUG] Audio Transfer:   2. Install paramiko: pip install paramiko")
            print("[DEBUG] Audio Transfer:   3. Configure SSH access to robot (user: nao)")
            print("[DEBUG] Audio Transfer:   4. Set up network share to access /home/nao/ on robot")
            
            return None
            
        except Exception as e:
            print("[DEBUG] Audio Transfer: ERROR - Exception: %s" % str(e))
            import traceback
            print("[DEBUG] Audio Transfer: Traceback: %s" % traceback.format_exc())
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
        
        print("[DEBUG] Whisper API: Starting transcription...")
        print("[DEBUG] Whisper API: Audio file path: %s" % audio_path)
        
        # Check if file exists
        if not os.path.exists(audio_path):
            print("[DEBUG] Whisper API: ERROR - Audio file does not exist!")
            return None
        
        file_size = os.path.getsize(audio_path)
        print("[DEBUG] Whisper API: Audio file size: %d bytes" % file_size)
        
        try:
            # Use curl for multipart upload (more reliable than urllib2)
            print("[DEBUG] Whisper API: Sending request to: %s" % OPENAI_WHISPER_URL)
            print("[DEBUG] Whisper API: Using model: whisper-1")
            
            cmd = [
                'curl', '-s',
                '-X', 'POST',
                OPENAI_WHISPER_URL,
                '-H', 'Authorization: Bearer %s' % self.api_key,
                '-F', 'file=@%s' % audio_path,
                '-F', 'model=whisper-1'
            ]
            
            print("[DEBUG] Whisper API: Executing curl command...")
            result = subprocess.check_output(cmd)
            
            print("[DEBUG] Whisper API: Raw response received (length: %d bytes)" % len(result))
            print("[DEBUG] Whisper API: Raw response: %s" % result[:200])  # First 200 chars
            
            data = json.loads(result)
            print("[DEBUG] Whisper API: Parsed JSON response: %s" % json.dumps(data))
            
            transcription = data.get('text', '').strip()
            print("[DEBUG] Whisper API: Transcription result: '%s'" % transcription)
            print("[DEBUG] Whisper API: Transcription length: %d characters" % len(transcription))
            
            return transcription
        except subprocess.CalledProcessError as e:
            print("[DEBUG] Whisper API: ERROR - Curl process error: %s" % str(e))
            print("[DEBUG] Whisper API: Return code: %s" % getattr(e, 'returncode', 'unknown'))
            return None
        except ValueError as e:
            print("[DEBUG] Whisper API: ERROR - JSON parsing error: %s" % str(e))
            print("[DEBUG] Whisper API: Response that failed to parse: %s" % result[:500])
            return None
        except Exception as e:
            print("[DEBUG] Whisper API: ERROR - Unexpected error: %s" % str(e))
            import traceback
            print("[DEBUG] Whisper API: Traceback: %s" % traceback.format_exc())
            return None
    
    def get_gpt_response(self, user_message):
        """Get response from ChatGPT."""
        print("[DEBUG] LLM API: Preparing request...")
        print("[DEBUG] LLM API: User message: '%s'" % user_message)
        print("[DEBUG] LLM API: User message length: %d characters" % len(user_message))
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        print("[DEBUG] LLM API: Total messages in conversation: %d" % len(messages))
        print("[DEBUG] LLM API: Conversation history length: %d" % len(self.conversation_history))
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        print("[DEBUG] LLM API: Request payload:")
        print("[DEBUG] LLM API:   Model: %s" % self.model)
        print("[DEBUG] LLM API:   Max tokens: %d" % data['max_tokens'])
        print("[DEBUG] LLM API:   Temperature: %.2f" % data['temperature'])
        print("[DEBUG] LLM API:   Messages count: %d" % len(messages))
        
        # Print message summary (first 100 chars of each)
        for i, msg in enumerate(messages):
            content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            print("[DEBUG] LLM API:   Message %d [%s]: %s" % (i, msg['role'], content_preview))
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % self.api_key
        }
        
        try:
            print("[DEBUG] LLM API: Sending request to: %s" % OPENAI_CHAT_URL)
            request_data = json.dumps(data).encode('utf-8')
            print("[DEBUG] LLM API: Request payload size: %d bytes" % len(request_data))
            
            request = Request(
                OPENAI_CHAT_URL,
                data=request_data,
                headers=headers
            )
            
            print("[DEBUG] LLM API: Waiting for response (timeout: 30s)...")
            response = urlopen(request, timeout=30)
            
            response_data = response.read().decode('utf-8')
            print("[DEBUG] LLM API: Response received (size: %d bytes)" % len(response_data))
            print("[DEBUG] LLM API: Raw response (first 500 chars): %s" % response_data[:500])
            
            result = json.loads(response_data)
            print("[DEBUG] LLM API: Parsed JSON response structure: %s" % list(result.keys()))
            
            if 'choices' in result:
                print("[DEBUG] LLM API: Number of choices: %d" % len(result['choices']))
            else:
                print("[DEBUG] LLM API: WARNING - No 'choices' key in response!")
                print("[DEBUG] LLM API: Full response: %s" % json.dumps(result, indent=2))
            
            if 'choices' in result and len(result['choices']) > 0:
                choice = result['choices'][0]
                print("[DEBUG] LLM API: First choice structure: %s" % list(choice.keys()))
                
                if 'message' in choice:
                    message = choice['message']
                    print("[DEBUG] LLM API: Message structure: %s" % list(message.keys()))
                    content = message.get('content')
                    
                    if content is None:
                        print("[DEBUG] LLM API: ERROR - Content is None!")
                        return "I didn't understand that. Could you try again?"
                    
                    reply = str(content).strip()
                    print("[DEBUG] LLM API: Response content: '%s'" % reply)
                    print("[DEBUG] LLM API: Response length: %d characters" % len(reply))
                    
                    # Ensure reply is not empty
                    if not reply:
                        print("[DEBUG] LLM API: WARNING - Empty reply, using fallback")
                        reply = "I didn't understand that. Could you try again?"
                    
                    # Update conversation history
                    self.conversation_history.append({"role": "user", "content": user_message})
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    
                    # Keep history manageable
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]
                    
                    print("[DEBUG] LLM API: Successfully processed response")
                    return reply
            else:
                print("[DEBUG] LLM API: ERROR - No valid choices in response")
                print("[DEBUG] LLM API: Full response: %s" % json.dumps(result, indent=2))
            
            return "I didn't understand that. Could you try again?"
            
        except HTTPError as e:
            print("[DEBUG] LLM API: ERROR - HTTP Error %s" % e.code)
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else ''
            print("[DEBUG] LLM API: Error response body: %s" % error_body)
            print("GPT API Error: %s" % e.code)
            return "I'm having trouble thinking right now. Please try again."
        except Exception as e:
            print("[DEBUG] LLM API: ERROR - Exception: %s" % str(e))
            import traceback
            print("[DEBUG] LLM API: Traceback: %s" % traceback.format_exc())
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
            # Note: The audio file is on the robot, we need to download it first
            print("[DEBUG] Audio Transfer: Audio recorded on robot at: %s" % audio_file)
            print("[DEBUG] Audio Transfer: Downloading audio file from robot...")
            local_audio_file = self.get_audio_from_robot(audio_file)
            
            if not local_audio_file:
                print("[DEBUG] Audio Transfer: Failed to download audio file")
                print("[DEBUG] Audio Transfer: Attempting to use remote path directly (may not work)...")
                # Try using remote path directly (won't work but will show better error)
                local_audio_file = audio_file
            
            print("[DEBUG] Starting Whisper transcription...")
            print("[DEBUG] Whisper API: Using audio file: %s" % local_audio_file)
            transcription = self.transcribe_with_whisper(local_audio_file)
            
            if not transcription:
                print("[DEBUG] Whisper transcription failed or returned empty result")
                self.set_eye_color('red')
                self.say("I couldn't understand that. Please try again.")
                self.set_eye_color('white')
                return
            
            print("[DEBUG] Whisper transcription successful")
            print("You said: %s" % transcription)
            
            # Get GPT response
            print("[DEBUG] Starting LLM API call...")
            print("Getting response...")
            response = self.get_gpt_response(transcription)
            print("[DEBUG] LLM API call completed")
            
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
    """Run in demo mode - type what you'd say OR use voice input."""
    print("\n" + "=" * 60)
    print("DEMO MODE - Voice or Text Conversation")
    print("=" * 60)
    print("Options:")
    print("  - Type your message and press Enter (text input)")
    print("  - Press Enter without typing to record audio from NAO's microphone")
    print("  - Type 'voice' or 'v' and press Enter to record audio")
    print("  - Type 'quit' to exit")
    print("=" * 60 + "\n")
    print("NOTE: Voice recording requires transferring audio from the robot.")
    print("      Setup options:")
    print("      1. Windows 10+: OpenSSH client is built-in (enable in Settings)")
    print("      2. Install paramiko: pip install paramiko")
    print("      3. Configure SSH: Default user 'nao' with password 'nao'")
    print("      Text input will always work.\n")
    
    api_key = get_openai_api_key()
    model = get_openai_model()
    
    tts = ALProxy("ALTextToSpeech", robot_ip, port)
    leds = ALProxy("ALLeds", robot_ip, port)
    audio_recorder = ALProxy("ALAudioRecorder", robot_ip, port)
    tts.setParameter("speed", 85)
    
    conversation_history = []
    
    # Create a minimal assistant instance for voice recording
    class MinimalAssistant:
        def __init__(self, robot_ip, port):
            self.robot_ip = robot_ip
            self.port = port
            self.audio_recorder = ALProxy("ALAudioRecorder", robot_ip, port)
            self.api_key = api_key
        def record_audio(self, duration=RECORD_DURATION):
            filename = "/home/nao/recording.wav"
            print("[DEBUG] Recording: Starting audio recording...")
            print("[DEBUG] Recording: Target file: %s" % filename)
            
            self.audio_recorder.stopMicrophonesRecording()
            time.sleep(0.2)
            
            print("[DEBUG] Recording: Starting microphone recording...")
            self.audio_recorder.startMicrophonesRecording(
                filename, "wav", SAMPLE_RATE, [1, 0, 0, 0]
            )
            print("Recording for %d seconds..." % duration)
            time.sleep(duration)
            
            print("[DEBUG] Recording: Stopping recording...")
            self.audio_recorder.stopMicrophonesRecording()
            print("Recording complete.")
            
            # Wait for file to be written
            print("[DEBUG] Recording: Waiting for file to be written...")
            time.sleep(0.5)
            
            # Verify file exists
            try:
                file_manager = ALProxy("ALFileManager", self.robot_ip, self.port)
                if file_manager.fileExists(filename):
                    try:
                        if hasattr(file_manager, 'getFileSize'):
                            file_size = file_manager.getFileSize(filename)
                            print("[DEBUG] Recording: File exists on robot: %s (size: %d bytes)" % (filename, file_size))
                        else:
                            print("[DEBUG] Recording: File exists on robot: %s" % filename)
                    except Exception as e:
                        print("[DEBUG] Recording: File exists but could not get size: %s" % str(e))
                else:
                    print("[DEBUG] Recording: WARNING - File does not exist yet")
                    time.sleep(1.0)
                    if file_manager.fileExists(filename):
                        try:
                            if hasattr(file_manager, 'getFileSize'):
                                file_size = file_manager.getFileSize(filename)
                                print("[DEBUG] Recording: File now exists (size: %d bytes)" % file_size)
                            else:
                                print("[DEBUG] Recording: File now exists")
                        except:
                            print("[DEBUG] Recording: File now exists")
                    else:
                        print("[DEBUG] Recording: ERROR - File still does not exist")
                        # Try to list directory
                        try:
                            parent_dir = os.path.dirname(filename)
                            if hasattr(file_manager, 'listFiles'):
                                files = file_manager.listFiles(parent_dir)
                                print("[DEBUG] Recording: Files in %s: %s" % (parent_dir, str(files)))
                        except Exception as e2:
                            print("[DEBUG] Recording: Could not list directory: %s" % str(e2))
            except Exception as e:
                print("[DEBUG] Recording: Could not verify file: %s" % str(e))
                import traceback
                print("[DEBUG] Recording: Traceback: %s" % traceback.format_exc())
            
            return filename
        def get_audio_from_robot(self, remote_path):
            # Use the same method as NaoAssistant
            try:
                print("[DEBUG] Audio Transfer: Downloading file from robot...")
                print("[DEBUG] Audio Transfer: Remote path: %s" % remote_path)
                
                # Check if file exists
                file_manager = ALProxy("ALFileManager", self.robot_ip, self.port)
                if not file_manager.fileExists(remote_path):
                    print("[DEBUG] Audio Transfer: ERROR - File does not exist on robot!")
                    return None
                
                local_path = tempfile.mktemp(suffix='.wav')
                print("[DEBUG] Audio Transfer: Local path: %s" % local_path)
                
                import subprocess
                import shutil
                
                # Try SCP
                scp_available = shutil.which('scp') is not None
                if scp_available:
                    print("[DEBUG] Audio Transfer: Trying SCP...")
                    scp_cmd = ['scp', '-o', 'StrictHostKeyChecking=no',
                              'nao@%s:%s' % (self.robot_ip, remote_path), local_path]
                    try:
                        subprocess.check_output(scp_cmd, stderr=subprocess.STDOUT, timeout=10)
                        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                            print("[DEBUG] Audio Transfer: SCP successful!")
                            return local_path
                    except Exception as e:
                        print("[DEBUG] Audio Transfer: SCP failed: %s" % str(e))
                
                # Try paramiko SFTP
                try:
                    import paramiko
                    print("[DEBUG] Audio Transfer: Trying SFTP...")
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(self.robot_ip, username='nao', password='nao', timeout=10)
                    sftp = ssh.open_sftp()
                    sftp.get(remote_path, local_path)
                    sftp.close()
                    ssh.close()
                    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                        print("[DEBUG] Audio Transfer: SFTP successful!")
                        return local_path
                except ImportError:
                    print("[DEBUG] Audio Transfer: paramiko not available")
                except Exception as e:
                    print("[DEBUG] Audio Transfer: SFTP failed: %s" % str(e))
                
                print("[DEBUG] Audio Transfer: All methods failed")
                return None
            except Exception as e:
                print("[DEBUG] Audio Transfer: Exception: %s" % str(e))
                return None
        def transcribe_with_whisper(self, audio_path):
            # Import the method logic
            import subprocess
            import json
            if not os.path.exists(audio_path):
                print("[DEBUG] Whisper API: ERROR - Audio file does not exist!")
                return None
            try:
                cmd = [
                    'curl', '-s', '-X', 'POST', OPENAI_WHISPER_URL,
                    '-H', 'Authorization: Bearer %s' % self.api_key,
                    '-F', 'file=@%s' % audio_path,
                    '-F', 'model=whisper-1'
                ]
                result = subprocess.check_output(cmd)
                data = json.loads(result)
                return data.get('text', '').strip()
            except:
                return None
    
    minimal_assistant = MinimalAssistant(robot_ip, port)
    
    # Greeting
    greeting = "Hello! I'm NAO, your AI assistant. What would you like to talk about?"
    print("NAO: %s" % greeting)
    tts.say(greeting)
    
    while True:
        try:
            user_input = raw_input("\nYou (type message, 'voice'/'v' to record, 'quit' to exit): ").strip()
        except NameError:
            user_input = input("\nYou (type message, 'voice'/'v' to record, 'quit' to exit): ").strip()
        
        print("[DEBUG] User Input: Received: '%s'" % user_input)
        print("[DEBUG] User Input: Length: %d characters" % len(user_input))
        
        # Handle empty input - trigger voice recording
        if not user_input:
            print("[DEBUG] User Input: Empty input - starting voice recording...")
            user_input = 'voice'  # Treat empty as voice command
        
        # Handle voice recording
        if user_input.lower() in ['voice', 'v', 'record', 'r']:
            print("[DEBUG] User Input: Voice recording requested")
            leds.fadeRGB("FaceLeds", 0x0000FF, 0.3)  # Blue for listening
            tts.say("I'm listening")
            
            try:
                # Record audio
                audio_file = minimal_assistant.record_audio(duration=RECORD_DURATION)
                
                # Download from robot
                leds.fadeRGB("FaceLeds", 0xFFFF00, 0.3)  # Yellow for processing
                print("[DEBUG] Downloading audio from robot...")
                local_audio_file = minimal_assistant.get_audio_from_robot(audio_file)
                
                if not local_audio_file:
                    print("[DEBUG] Audio Transfer: Could not download, trying remote path...")
                    local_audio_file = audio_file
                
                # Transcribe
                print("[DEBUG] Transcribing audio with Whisper...")
                transcription = minimal_assistant.transcribe_with_whisper(local_audio_file)
                
                if not transcription:
                    print("[DEBUG] Whisper transcription failed")
                    leds.fadeRGB("FaceLeds", 0xFF0000, 0.3)  # Red for error
                    tts.say("I couldn't understand that. Please try again.")
                    leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)
                    continue
                
                print("[DEBUG] Whisper transcription successful: '%s'" % transcription)
                user_input = transcription  # Use transcription as user input
                print("You said: %s" % transcription)
                
            except Exception as e:
                print("[DEBUG] Voice recording error: %s" % str(e))
                import traceback
                print("[DEBUG] Traceback: %s" % traceback.format_exc())
                leds.fadeRGB("FaceLeds", 0xFF0000, 0.3)
                tts.say("I had trouble recording. Please try typing instead.")
                leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)
                continue
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("[DEBUG] User Input: Quit command received")
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
        print("[DEBUG] LLM API: Preparing request for demo mode...")
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        print("[DEBUG] LLM API: Total messages: %d" % len(messages))
        print("[DEBUG] LLM API: Conversation history: %d messages" % len(conversation_history))
        
        # Call GPT
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        print("[DEBUG] LLM API: Request configuration:")
        print("[DEBUG] LLM API:   Model: %s" % model)
        print("[DEBUG] LLM API:   Max tokens: %d" % data['max_tokens'])
        print("[DEBUG] LLM API:   Temperature: %.2f" % data['temperature'])
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % api_key
        }
        
        try:
            print("[DEBUG] LLM API: Sending request to: %s" % OPENAI_CHAT_URL)
            request_data = json.dumps(data).encode('utf-8')
            print("[DEBUG] LLM API: Request payload size: %d bytes" % len(request_data))
            
            request = Request(
                OPENAI_CHAT_URL,
                data=request_data,
                headers=headers
            )
            
            print("[DEBUG] LLM API: Waiting for response (timeout: 30s)...")
            response = urlopen(request, timeout=30)
            
            response_data = response.read().decode('utf-8')
            print("[DEBUG] LLM API: Response received (size: %d bytes)" % len(response_data))
            print("[DEBUG] LLM API: Raw response (first 500 chars): %s" % response_data[:500])
            
            result = json.loads(response_data)
            print("[DEBUG] LLM API: Parsed JSON response structure: %s" % list(result.keys()))
            
            # Validate response structure
            if 'choices' not in result or len(result['choices']) == 0:
                print("[DEBUG] LLM API: ERROR - No choices in response!")
                print("[DEBUG] LLM API: Full response: %s" % json.dumps(result, indent=2))
                raise ValueError("No choices in API response")
            
            print("[DEBUG] LLM API: Number of choices: %d" % len(result['choices']))
            choice = result['choices'][0]
            print("[DEBUG] LLM API: First choice structure: %s" % list(choice.keys()))
            
            if 'message' not in choice:
                print("[DEBUG] LLM API: ERROR - No 'message' in choice!")
                raise ValueError("No message in choice")
            
            message = choice['message']
            print("[DEBUG] LLM API: Message structure: %s" % list(message.keys()))
            
            content = message.get('content')
            if content is None:
                print("[DEBUG] LLM API: ERROR - Content is None!")
                print("[DEBUG] LLM API: Full message: %s" % json.dumps(message, indent=2))
                raise ValueError("Content is None in API response")
            
            reply = str(content).strip()
            print("[DEBUG] LLM API: Response content: '%s'" % reply)
            print("[DEBUG] LLM API: Response length: %d characters" % len(reply))
            
            # Ensure reply is not empty
            if not reply:
                print("[DEBUG] LLM API: WARNING - Empty reply, using fallback")
                reply = "I didn't understand that. Could you try again?"
            
            # Update history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": reply})
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            print("[DEBUG] LLM API: Successfully processed response")
            print("[DEBUG] LLM Response: Final reply to speak: '%s'" % reply)
            
            # Speak response
            leds.fadeRGB("FaceLeds", 0x00FF00, 0.3)
            print("NAO: %s" % reply)
            tts.say(reply)
            leds.fadeRGB("FaceLeds", 0xFFFFFF, 0.5)
            
        except Exception as e:
            print("[DEBUG] LLM API: ERROR - Exception occurred: %s" % str(e))
            import traceback
            print("[DEBUG] LLM API: Traceback: %s" % traceback.format_exc())
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

