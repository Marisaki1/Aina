import os
import time
import threading
import queue
import tempfile
from typing import Dict, List, Any, Optional, Callable, Union

# Try to import speech recognition libraries
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

class SpeechRecognizer:
    """
    Speech recognition system for transcribing audio to text.
    Supports continuous listening with callbacks.
    """
    
    def __init__(self, 
                energy_threshold: int = 4000,
                pause_threshold: float = 0.8,
                dynamic_energy: bool = True):
        """
        Initialize speech recognizer.
        
        Args:
            energy_threshold: Energy level for speech detection
            pause_threshold: Seconds of non-speaking audio to consider the end of a phrase
            dynamic_energy: Whether to dynamically adjust energy threshold
        """
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        self.dynamic_energy = dynamic_energy
        
        self.recognizer = None
        self.microphone = None
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.stop_listening = False
        self.listener_thread = None
        self.processor_thread = None
        
        # Callback function
        self.callback = None
        
        # Check if speech recognition is available
        self.available = HAS_SPEECH_RECOGNITION
        
        if not self.available:
            print("⚠️ Speech recognition not available: missing dependencies")
            return
        
        # Initialize speech recognition
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = self.energy_threshold
            self.recognizer.pause_threshold = self.pause_threshold
            self.recognizer.dynamic_energy_threshold = self.dynamic_energy
            
            # Test if microphone is available
            try:
                with sr.Microphone() as mic:
                    print("✅ Speech recognition initialized, microphone available")
            except Exception as e:
                print(f"⚠️ Microphone not available: {e}")
                self.available = False
                
        except Exception as e:
            print(f"❌ Error initializing speech recognition: {e}")
            self.available = False
    
    def start(self, callback: Callable[[str], None]) -> bool:
        """
        Start continuous speech recognition.
        
        Args:
            callback: Function to call with recognized text
            
        Returns:
            Success status
        """
        if not self.available:
            print("❌ Speech recognition not available")
            return False
        
        if self.listener_thread and self.listener_thread.is_alive():
            print("⚠️ Speech recognition already running")
            return False
        
        try:
            self.callback = callback
            self.stop_listening = False
            
            # Start listener thread
            self.listener_thread = threading.Thread(target=self._listener_loop)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            # Start processor thread
            self.processor_thread = threading.Thread(target=self._processor_loop)
            self.processor_thread.daemon = True
            self.processor_thread.start()
            
            return True
        except Exception as e:
            print(f"❌ Error starting speech recognition: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop continuous speech recognition.
        
        Returns:
            Success status
        """
        if not self.listener_thread or not self.processor_thread:
            return False
        
        try:
            self.stop_listening = True
            
            # Wait for threads to terminate
            if self.listener_thread.is_alive():
                self.listener_thread.join(timeout=2.0)
            
            if self.processor_thread.is_alive():
                self.processor_thread.join(timeout=2.0)
            
            # Clear queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            return True
        except Exception as e:
            print(f"❌ Error stopping speech recognition: {e}")
            return False
    
    def _listener_loop(self) -> None:
        """Background thread for continuous listening."""
        print("🎤 Starting speech recognition listener...")
        
        with sr.Microphone() as source:
            # Adjust for ambient noise
            print("Adjusting for ambient noise... (please be quiet)")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold set to {self.recognizer.energy_threshold}")
            
            print("🎤 Listening for speech...")
            
            while not self.stop_listening:
                try:
                    # Listen for audio
                    audio = self.recognizer.listen(source, timeout=10.0, phrase_time_limit=10.0)
                    
                    # Put audio in queue for processing
                    self.audio_queue.put(audio)
                    
                except sr.WaitTimeoutError:
                    # No speech detected, continue listening
                    continue
                except Exception as e:
                    if not self.stop_listening:
                        print(f"❌ Error in speech listener: {e}")
                    break
    
    def _processor_loop(self) -> None:
        """Background thread for processing audio."""
        print("🔄 Starting speech recognition processor...")
        
        while not self.stop_listening:
            try:
                # Get audio from queue with timeout
                try:
                    audio = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process audio
                try:
                    print("🔄 Processing speech...")
                    
                    # Try to recognize with Google first (more accurate, requires internet)
                    text = None
                    try:
                        text = self.recognizer.recognize_google(audio)
                    except Exception:
                        # Fall back to Sphinx (offline, less accurate)
                        try:
                            text = self.recognizer.recognize_sphinx(audio)
                        except Exception:
                            # No recognition possible
                            pass
                    
                    # Call callback with recognized text
                    if text and self.callback:
                        self.callback(text)
                    
                except Exception as e:
                    print(f"❌ Error processing speech: {e}")
                
                # Mark task as done
                self.audio_queue.task_done()
                
            except Exception as e:
                if not self.stop_listening:
                    print(f"❌ Error in speech processor: {e}")
                break
    
    def recognize_file(self, audio_file: str) -> Optional[str]:
        """
        Recognize speech from an audio file.
        
        Args:
            audio_file: Path to audio file
            
        Returns:
            Recognized text or None if failed
        """
        if not self.available:
            print("❌ Speech recognition not available")
            return None
        
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                
                # Try to recognize with Google first
                try:
                    text = self.recognizer.recognize_google(audio_data)
                    return text
                except Exception:
                    # Fall back to Sphinx
                    try:
                        text = self.recognizer.recognize_sphinx(audio_data)
                        return text
                    except Exception as e:
                        print(f"❌ Could not recognize speech: {e}")
                        return None
        except Exception as e:
            print(f"❌ Error processing audio file: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of speech recognition system.
        
        Returns:
            Status information
        """
        status = {
            "available": self.available,
            "running": self.listener_thread is not None and self.listener_thread.is_alive()
        }
        
        if self.available and self.recognizer:
            status.update({
                "energy_threshold": self.recognizer.energy_threshold,
                "pause_threshold": self.recognizer.pause_threshold,
                "dynamic_energy": self.recognizer.dynamic_energy_threshold
            })
        
        return status