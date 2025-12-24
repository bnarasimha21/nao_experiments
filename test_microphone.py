#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script to verify microphone access and recording.
"""

import sys
import os
import time

try:
    import pyaudio
    import wave
except ImportError as e:
    print("ERROR: Required library not found: %s" % str(e))
    print("Install with: pip install pyaudio")
    sys.exit(1)

def test_microphone():
    """Test if we can access and record from the microphone."""
    print("=" * 60)
    print("Microphone Access Test")
    print("=" * 60)
    
    # Initialize pyaudio
    try:
        audio = pyaudio.PyAudio()
        print("[OK] PyAudio initialized")
    except Exception as e:
        print("[ERROR] Failed to initialize PyAudio: %s" % str(e))
        return False
    
    # List devices
    print("\nAvailable input devices:")
    print("-" * 60)
    try:
        default_input = audio.get_default_input_device_info()
        print("Default input device:")
        print("  Index: %d" % default_input['index'])
        try:
            device_name = default_input['name'].encode('ascii', 'replace').decode('ascii')
        except:
            device_name = str(default_input['name'])
        print("  Name: %s" % device_name)
        print("  Channels: %d" % default_input['maxInputChannels'])
        print("  Sample Rate: %.0f" % default_input['defaultSampleRate'])
    except Exception as e:
        print("[ERROR] Could not get default input device: %s" % str(e))
        audio.terminate()
        return False
    
    # Try to open a stream
    print("\nTesting microphone access...")
    print("-" * 60)
    
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    sample_rate = 16000
    duration = 2  # 2 seconds test
    
    try:
        stream = audio.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk
        )
        print("[OK] Audio stream opened successfully!")
        
        # Try to read some data
        print("Recording 2 seconds of audio (speak now)...")
        frames = []
        num_chunks = int(sample_rate / chunk * duration)
        
        for i in range(num_chunks):
            try:
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                print("[ERROR] Failed to read audio data: %s" % str(e))
                stream.stop_stream()
                stream.close()
                audio.terminate()
                return False
        
        stream.stop_stream()
        stream.close()
        print("[OK] Successfully recorded %d frames" % len(frames))
        
        # Try to save to file
        test_file = "test_recording.wav"
        try:
            wf = wave.open(test_file, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(audio.get_sample_size(format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            file_size = os.path.getsize(test_file)
            print("[OK] Saved test recording: %s (%d bytes)" % (test_file, file_size))
            
            # Clean up
            try:
                os.remove(test_file)
                print("[OK] Test file cleaned up")
            except:
                pass
                
        except Exception as e:
            print("[ERROR] Failed to save audio file: %s" % str(e))
            audio.terminate()
            return False
        
        audio.terminate()
        print("\n" + "=" * 60)
        print("SUCCESS: Microphone access is working!")
        print("=" * 60)
        return True
        
    except OSError as e:
        print("[ERROR] Failed to open audio stream: %s" % str(e))
        if "Permission denied" in str(e) or "Access is denied" in str(e):
            print("\nMICROPHONE PERMISSION ISSUE:")
            print("  Windows: Settings > Privacy > Microphone")
            print("  Make sure Python/your terminal has microphone access")
        elif "Invalid sample rate" in str(e):
            print("\nSAMPLE RATE ISSUE:")
            print("  Your microphone may not support 16000 Hz")
            print("  Try a different sample rate")
        audio.terminate()
        return False
    except Exception as e:
        print("[ERROR] Unexpected error: %s" % str(e))
        import traceback
        print(traceback.format_exc())
        audio.terminate()
        return False

if __name__ == "__main__":
    success = test_microphone()
    sys.exit(0 if success else 1)

