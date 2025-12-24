#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
NAO AI Assistant - Listen, Think, Speak

The laptop listens to your question using its microphone, sends audio to 
OpenAI Whisper for transcription, gets a GPT response, and NAO speaks it back.

Usage:
    python2 nao_assistant.py [robot_ip]
    
Touch NAO's head to start a conversation!

Setup:
    1. Add to your .env file:
       NAO_IP_ADDRESS=192.168.1.100
       OPENAI_API_KEY=sk-your-api-key-here
    
    2. Install pyaudio for audio recording:
       
       macOS:
         brew install portaudio
         pip install pyaudio
       
       Linux (Ubuntu/Debian):
         sudo apt-get install portaudio19-dev python-pyaudio
       
       Windows:
         pip install pyaudio
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
# Import wave module - clear cache if needed to avoid conflicts with old wave.py
if 'wave' in sys.modules:
    wave_mod = sys.modules['wave']
    wave_file = getattr(wave_mod, '__file__', '')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # If it's the local wave module (from examples directory), remove it
    if wave_file and script_dir in wave_file:
        print("[DEBUG] Removing cached local wave module: %s" % wave_file)
        del sys.modules['wave']
import wave
# Verify we got the right module
if not hasattr(wave, 'open'):
    raise ImportError("Failed to import standard library wave module. Got: %s" % getattr(wave, '__file__', 'unknown'))

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

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: pyaudio not found. Audio recording will not work.")
    print("Install with: pip install pyaudio")


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
        
        # Check pyaudio availability
        if not PYAUDIO_AVAILABLE:
            print("ERROR: pyaudio is required for audio recording.")
            print("Install with: pip install pyaudio")
            sys.exit(1)
        
        # Connect to NAO services
        print("Connecting to NAO at %s..." % robot_ip)
        self.tts = ALProxy("ALTextToSpeech", robot_ip, port)
        self.memory = ALProxy("ALMemory", robot_ip, port)
        self.leds = ALProxy("ALLeds", robot_ip, port)
        
        # Configure TTS
        self.tts.setParameter("speed", 85)
        
        # Initialize pyaudio
        self.audio = pyaudio.PyAudio()
        
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
    
    def list_audio_devices(self):
        """List available audio input devices for debugging."""
        print("\n[DEBUG] Available audio input devices:")
        print("-" * 60)
        try:
            default_input = self.audio.get_default_input_device_info()
            print("Default input device:")
            print("  Index: %d" % default_input['index'])
            # Handle encoding issues with device names
            try:
                device_name = default_input['name'].encode('ascii', 'replace').decode('ascii')
            except:
                device_name = str(default_input['name']).encode('ascii', 'replace').decode('ascii')
            print("  Name: %s" % device_name)
            print("  Channels: %d" % default_input['maxInputChannels'])
            print("  Sample Rate: %.0f" % default_input['defaultSampleRate'])
            print("-" * 60)
            
            print("\nAll input devices:")
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    try:
                        device_name = info['name'].encode('ascii', 'replace').decode('ascii')
                    except:
                        device_name = str(info['name']).encode('ascii', 'replace').decode('ascii')
                    print("  [%d] %s (Channels: %d)" % (i, device_name, info['maxInputChannels']))
        except Exception as e:
            print("[DEBUG] Error listing devices: %s" % str(e))
        print("-" * 60 + "\n")
    
    def record_audio_on_laptop(self, duration=RECORD_DURATION):
        """
        Record audio from laptop's microphone.
        Returns the local path to the recorded WAV file.
        """
        if not PYAUDIO_AVAILABLE:
            print("ERROR: pyaudio not available. Cannot record audio.")
            return None
        
        print("[DEBUG] Recording: Starting...")
        print("Recording for %d seconds..." % duration)
        
        # List available devices for debugging
        self.list_audio_devices()
        
        # Create temporary file for recording
        local_path = tempfile.mktemp(suffix='.wav')
        
        # Audio recording parameters
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1  # Mono
        sample_rate = SAMPLE_RATE
        
        stream = None
        try:
            # Get default input device
            try:
                default_device = self.audio.get_default_input_device_info()
                device_index = default_device['index']
                # Handle encoding issues with device names
                try:
                    device_name = default_device['name'].encode('ascii', 'replace').decode('ascii')
                except:
                    device_name = str(default_device['name']).encode('ascii', 'replace').decode('ascii')
                print("[DEBUG] Using default input device: %s (index %d)" % (device_name, device_index))
            except Exception as e:
                print("[DEBUG] Warning: Could not get default input device: %s" % str(e))
                print("[DEBUG] Trying to use device index 0...")
                device_index = None
            
            # Open audio stream
            print("[DEBUG] Opening audio stream...")
            stream_params = {
                'format': format,
                'channels': channels,
                'rate': sample_rate,
                'input': True,
                'frames_per_buffer': chunk
            }
            
            if device_index is not None:
                stream_params['input_device_index'] = device_index
            
            stream = self.audio.open(**stream_params)
            print("[DEBUG] Audio stream opened successfully!")
            
            print("\n" + "=" * 60)
            print("Recording... (speak now)")
            print("=" * 60)
            frames = []
            
            # Record for specified duration
            num_chunks = int(sample_rate / chunk * duration)
            for i in range(0, num_chunks):
                try:
                    data = stream.read(chunk, exception_on_overflow=False)
                    frames.append(data)
                    # Show progress
                    if (i + 1) % 10 == 0:
                        progress = int((i + 1) * 100.0 / num_chunks)
                        print("[%d%%] Recording..." % progress)
                except Exception as e:
                    print("[DEBUG] Error reading audio chunk: %s" % str(e))
                    break
            
            print("Recording complete.")
            
            # Stop and close stream
            if stream:
                stream.stop_stream()
                stream.close()
            
            if len(frames) == 0:
                print("[DEBUG] ERROR: No audio frames recorded!")
                return None
            
            # Save to WAV file
            print("[DEBUG] Saving audio file...")
            # Import wave module (standard library)
            # Clear any cached wave module to avoid conflicts with old .pyc files
            import sys
            if 'wave' in sys.modules:
                wave_mod = sys.modules['wave']
                wave_file = getattr(wave_mod, '__file__', '')
                # If it's not the standard library wave, remove it
                if wave_file and ('site-packages' not in wave_file and 'lib' not in wave_file and 'python' not in wave_file.lower()):
                    print("[DEBUG] Removing cached wave module (was: %s)" % wave_file)
                    del sys.modules['wave']
            
            import wave
            # Verify it's the correct module
            if not hasattr(wave, 'open'):
                raise AttributeError("wave module does not have 'open' - wrong module imported! File: %s" % getattr(wave, '__file__', 'N/A'))
            
            wf = wave.open(local_path, 'wb')
            
            wf.setnchannels(channels)
            wf.setsampwidth(self.audio.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            file_size = os.path.getsize(local_path)
            print("[DEBUG] Recording: File saved (%d bytes)" % file_size)
            
            if file_size < 1000:
                print("[DEBUG] WARNING: File seems very small. Recording may have failed.")
                return None
            
            return local_path
            
        except OSError as e:
            print("[DEBUG] Recording: OSError - %s" % str(e))
            if "Invalid sample rate" in str(e) or "Invalid number of channels" in str(e):
                print("[DEBUG] The microphone may not support the requested sample rate or channels.")
                print("[DEBUG] Try checking your microphone settings.")
            elif "Permission denied" in str(e) or "Access is denied" in str(e):
                print("[DEBUG] Microphone permission denied. Please check:")
                print("[DEBUG]   - Windows: Settings > Privacy > Microphone")
                print("[DEBUG]   - Make sure microphone access is enabled for Python")
            print("[DEBUG] Recording: Traceback: %s" % traceback.format_exc())
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            return None
        except Exception as e:
            print("[DEBUG] Recording: Error: %s" % str(e))
            print("[DEBUG] Recording: Traceback: %s" % traceback.format_exc())
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
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
        
        # Handle Python 2/3 compatibility for unicode strings
        try:
            # Python 2
            unicode_type = unicode
        except NameError:
            # Python 3
            unicode_type = str
        
        # Ensure user_message is unicode/str (not bytes)
        if not isinstance(user_message, unicode_type):
            try:
                user_message = user_message.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                user_message = unicode_type(user_message)
        
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
            # Use ensure_ascii=False to preserve unicode characters, then encode to UTF-8
            json_str = json.dumps(data, ensure_ascii=False)
            # If it's unicode (Python 2) or str (Python 3), encode to UTF-8 bytes
            if isinstance(json_str, unicode_type):
                json_bytes = json_str.encode('utf-8')
            else:
                # Already bytes (shouldn't happen with ensure_ascii=False, but handle it)
                json_bytes = json_str
            
            request = Request(
                OPENAI_CHAT_URL,
                data=json_bytes,
                headers=headers
            )
            
            response = urlopen(request, timeout=30)
            response_data = response.read()
            # Decode response
            if isinstance(response_data, bytes):
                response_data = response_data.decode('utf-8')
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
        # Try primary sensor paths
        try:
            front = self.memory.getData("Device/SubDeviceList/Head/Touch/Front/Sensor/Value")
            middle = self.memory.getData("Device/SubDeviceList/Head/Touch/Middle/Sensor/Value")
            rear = self.memory.getData("Device/SubDeviceList/Head/Touch/Rear/Sensor/Value")
            touched = front > 0.5 or middle > 0.5 or rear > 0.5
            if touched:
                print("[DEBUG] Head touched! Front: %.2f, Middle: %.2f, Rear: %.2f" % (front, middle, rear))
            return touched
        except Exception as e:
            # Try alternative sensor paths (some NAO models use different paths)
            try:
                print("[DEBUG] Primary head touch paths failed, trying alternatives...")
                # Alternative path format
                alt_paths = [
                    "Device/SubDeviceList/Head/Touch/Front/Sensor/Value",
                    "Device/SubDeviceList/Head/Touch/Middle/Sensor/Value", 
                    "Device/SubDeviceList/Head/Touch/Rear/Sensor/Value",
                    "ALMemory/HeadTouch/Front",
                    "ALMemory/HeadTouch/Middle",
                    "ALMemory/HeadTouch/Rear"
                ]
                for path in alt_paths:
                    try:
                        value = self.memory.getData(path)
                        if value > 0.5:
                            print("[DEBUG] Head touched via alternative path: %s = %.2f" % (path, value))
                            return True
                    except:
                        continue
                print("[DEBUG] Error checking head touch: %s" % str(e))
            except:
                pass
            return False
    
    def listen_and_respond(self):
        """
        Full conversation flow: listen, transcribe, respond.
        Returns True if user wants to quit, False to continue.
        """
        
        # Step 1: Visual feedback - listening
        self.set_eye_color('blue')
        self.say("I'm listening")
        # Give user a moment to start speaking
        time.sleep(0.5)
        
        try:
            # Step 2: Record audio on laptop
            local_audio_path = self.record_audio_on_laptop(duration=RECORD_DURATION)
            
            if not local_audio_path:
                self.set_eye_color('red')
                self.say("I couldn't record audio. Please check your microphone.")
                self.set_eye_color('white')
                return False  # Continue conversation
            
            # Step 3: Transcribe with Whisper
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
                return False  # Continue conversation
            
            print("\nYou said: \"%s\"" % transcription)
            
            # Check if user wants to quit
            transcription_lower = transcription.lower().strip()
            quit_keywords = ['quit', 'exit', 'stop', 'goodbye', 'bye', 'end conversation']
            if any(keyword in transcription_lower for keyword in quit_keywords):
                print("[DEBUG] User requested to quit conversation")
                self.set_eye_color('yellow')
                self.say("Goodbye! It was nice talking with you.")
                self.set_eye_color('white')
                return True  # Signal to stop the conversation loop
            
            # Step 4: Get GPT response
            print("Getting GPT response...")
            response = self.get_gpt_response(transcription)
            
            # Step 5: Speak the response
            self.set_eye_color('green')
            self.say(response)
            
            # Reset
            self.set_eye_color('white')
            return False  # Continue conversation
            
        except Exception as e:
            print("Error in conversation: %s" % str(e))
            print("Traceback: %s" % traceback.format_exc())
            self.set_eye_color('red')
            self.say("I encountered an error. Please try again.")
            self.set_eye_color('white')
            return False  # Continue conversation
    
    def run(self):
        """Main loop - wait for head touch to start, then continue conversation until user says quit."""
        print("\n" + "=" * 60)
        print("NAO AI Assistant Ready!")
        print("=" * 60)
        print("\nTouch NAO's head to start the conversation.")
        print("Say 'quit', 'exit', or 'stop' to end the conversation.")
        print("Press Ctrl+C to exit.")
        print("=" * 60 + "\n")
        
        self.set_eye_color('white')
        self.say("Hello! Touch my head to start our conversation.")
        
        # Test head touch sensors on startup
        print("[DEBUG] Testing head touch sensors...")
        try:
            front = self.memory.getData("Device/SubDeviceList/Head/Touch/Front/Sensor/Value")
            middle = self.memory.getData("Device/SubDeviceList/Head/Touch/Middle/Sensor/Value")
            rear = self.memory.getData("Device/SubDeviceList/Head/Touch/Rear/Sensor/Value")
            print("[DEBUG] Head sensors initialized - Front: %.2f, Middle: %.2f, Rear: %.2f" % (front, middle, rear))
        except Exception as e:
            print("[DEBUG] WARNING: Could not read head sensors: %s" % str(e))
            print("[DEBUG] Head touch detection may not work properly.")
        
        # Wait for initial head touch
        print("\nWaiting for head touch to start conversation...")
        head_touched = False
        last_touch_time = 0
        touch_debounce = 1.5  # seconds between touches
        
        try:
            # Phase 1: Wait for initial head touch
            while not head_touched:
                if self.is_head_touched():
                    current_time = time.time()
                    if current_time - last_touch_time > touch_debounce:
                        last_touch_time = current_time
                        print("\n" + "=" * 60)
                        print("HEAD TOUCH DETECTED - Starting conversation!")
                        print("=" * 60)
                        head_touched = True
                        # Immediate visual feedback
                        self.set_eye_color('cyan')
                        time.sleep(0.2)
                time.sleep(0.1)
            
            # Phase 2: Continuous conversation loop
            print("\n" + "=" * 60)
            print("Conversation started! I'm ready to chat.")
            print("Say 'quit', 'exit', or 'stop' when you want to end the conversation.")
            print("=" * 60 + "\n")
            
            self.set_eye_color('white')
            self.say("I'm ready! Let's chat.")
            time.sleep(0.5)
            
            # Continuous conversation loop
            while True:
                should_quit = self.listen_and_respond()
                if should_quit:
                    print("\n" + "=" * 60)
                    print("Conversation ended by user.")
                    print("=" * 60)
                    break
                
                # Small delay before next recording
                time.sleep(0.3)
                
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.say("Goodbye!")
            self.set_eye_color('white')
        except Exception as e:
            print("\n[ERROR] Fatal error in main loop: %s" % str(e))
            print("[ERROR] Traceback: %s" % traceback.format_exc())
            self.set_eye_color('red')
            try:
                self.say("A fatal error occurred. Shutting down.")
            except:
                pass
            self.set_eye_color('white')


def print_setup_instructions():
    """Print setup instructions for the current platform."""
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS")
    print("=" * 60)
    
    if is_windows():
        print("""
Windows Setup:

1. Install pyaudio for audio recording:
   pip install pyaudio
   
   Note: If installation fails, you may need to install Visual C++ Build Tools
   or download a pre-built wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

2. Add to your .env file:
   NAO_IP_ADDRESS=192.168.1.100
   OPENAI_API_KEY=sk-your-api-key-here

3. Run:
   python examples\\nao_assistant.py
""")
    else:
        print("""
macOS Setup:

1. Install pyaudio:
   brew install portaudio
   pip install pyaudio

2. Add to your .env file:
   NAO_IP_ADDRESS=192.168.1.100
   OPENAI_API_KEY=sk-your-api-key-here

3. Run:
   python2 examples/nao_assistant.py

---

Linux Setup:

1. Install pyaudio:
   sudo apt-get install portaudio19-dev python-pyaudio

2. Add to your .env file:
   NAO_IP_ADDRESS=192.168.1.100
   OPENAI_API_KEY=sk-your-api-key-here

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
    print("\n[DEBUG] Attempting to connect to NAO...")
    
    # Start the assistant
    try:
        assistant = NaoAssistant(robot_ip)
        print("[DEBUG] Connection successful! Starting main loop...")
        assistant.run()
    except Exception as e:
        print("\n[ERROR] Failed to connect or initialize NAO assistant:")
        print("[ERROR] %s" % str(e))
        print("[ERROR] Traceback: %s" % traceback.format_exc())
        print("\nTroubleshooting:")
        print("  1. Verify NAO is powered on and connected to the network")
        print("  2. Check that the IP address is correct: %s" % robot_ip)
        print("  3. Ensure your firewall allows connections on port 9559")
        print("  4. Try pinging the robot: ping %s" % robot_ip)
        sys.exit(1)
    finally:
        # Clean up pyaudio
        try:
            if 'assistant' in locals() and hasattr(assistant, 'audio'):
                assistant.audio.terminate()
        except:
            pass


if __name__ == "__main__":
    main()
