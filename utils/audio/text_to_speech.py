import os
import time
import threading
import queue
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union

# Try to import TTS libraries
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

class TextToSpeech:
    """
    Text-to-speech system for converting text to spoken audio.
    Supports multiple TTS engines with fallback mechanisms.
    """
    
    def __init__(self, 
                voice_id: Optional[str] = None,
                rate: int = 180,
                volume: float = 0.9,
                prefer_online: bool = False):
        """
        Initialize text-to-speech system.
        
        Args:
            voice_id: Voice ID to use (if None, use default)
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            prefer_online: Whether to prefer online TTS (gTTS) over offline (pyttsx3)
        """
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        self.prefer_online = prefer_online
        
        # TTS engines
        self.engine_pyttsx3 = None
        
        # Speech queue
        self.speech_queue = queue.Queue()
        self.stop_speaking = False
        self.speaker_thread = None
        
        # Available TTS engines
        self.has_pyttsx3 = HAS_PYTTSX3
        self.has_gtts = HAS_GTTS
        
        # Create temp directory for audio files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize TTS engines
        if self.has_pyttsx3:
            self._init_pyttsx3()
        
        # Check if any TTS engine is available
        self.available = self.has_pyttsx3 or self.has_gtts
        
        if not self.available:
            print("⚠️ Text-to-speech not available: missing dependencies")
            return
        
        print("✅ Text-to-speech initialized")
        
        # Start speaker thread
        self.speaker_thread = threading.Thread(target=self._speaker_loop)
        self.speaker_thread.daemon = True
        self.speaker_thread.start()
    
    def _init_pyttsx3(self) -> None:
        """Initialize pyttsx3 engine."""
        try:
            self.engine_pyttsx3 = pyttsx3.init()
            
            # Set properties
            self.engine_pyttsx3.setProperty('rate', self.rate)
            self.engine_pyttsx3.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice_id:
                self.engine_pyttsx3.setProperty('voice', self.voice_id)
            else:
                # Try to find a female voice
                voices = self.engine_pyttsx3.getProperty('voices')
                for voice in voices:
                    if "female" in voice.name.lower():
                        self.engine_pyttsx3.setProperty('voice', voice.id)
                        self.voice_id = voice.id
                        break
            
            print("✅ pyttsx3 engine initialized")
        except Exception as e:
            print(f"❌ Error initializing pyttsx3: {e}")
            self.engine_pyttsx3 = None
            self.has_pyttsx3 = False
    
    def speak(self, text: str, priority: bool = False) -> bool:
        """
        Convert text to speech.
        
        Args:
            text: Text to speak
            priority: Whether to speak immediately (skip queue)
            
        Returns:
            Success status
        """
        if not self.available:
            print("❌ Text-to-speech not available")
            return False
        
        if not text:
            return False
        
        try:
            # Add to queue or speak immediately
            if priority:
                return self._speak_text(text)
            else:
                self.speech_queue.put(text)
                return True
        except Exception as e:
            print(f"❌ Error queuing speech: {e}")
            return False
    
    def _speaker_loop(self) -> None:
        """Background thread for processing speech queue."""
        print("🔄 Starting text-to-speech processor...")
        
        while not self.stop_speaking:
            try:
                # Get text from queue with timeout
                try:
                    text = self.speech_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Speak text
                self._speak_text(text)
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except Exception as e:
                if not self.stop_speaking:
                    print(f"❌ Error in speech processor: {e}")
                time.sleep(1.0)
    
    def _speak_text(self, text: str) -> bool:
        """
        Speak text using available TTS engine.
        
        Args:
            text: Text to speak
            
        Returns:
            Success status
        """
        # Choose TTS engine based on preference and availability
        if self.prefer_online and self.has_gtts:
            # Try gTTS first, fall back to pyttsx3
            success = self._speak_gtts(text)
            if not success and self.has_pyttsx3:
                success = self._speak_pyttsx3(text)
            return success
        elif self.has_pyttsx3:
            # Try pyttsx3 first, fall back to gTTS
            success = self._speak_pyttsx3(text)
            if not success and self.has_gtts:
                success = self._speak_gtts(text)
            return success
        elif self.has_gtts:
            # Only gTTS is available
            return self._speak_gtts(text)
        else:
            return False
    
    def _speak_pyttsx3(self, text: str) -> bool:
        """
        Speak text using pyttsx3 engine.
        
        Args:
            text: Text to speak
            
        Returns:
            Success status
        """
        if not self.has_pyttsx3 or not self.engine_pyttsx3:
            return False
        
        try:
            self.engine_pyttsx3.say(text)
            self.engine_pyttsx3.runAndWait()
            return True
        except Exception as e:
            print(f"❌ Error with pyttsx3: {e}")
            return False
    
    def _speak_gtts(self, text: str) -> bool:
        """
        Speak text using Google Text-to-Speech (gTTS).
        
        Args:
            text: Text to speak
            
        Returns:
            Success status
        """
        if not self.has_gtts:
            return False
        
        try:
            # Create temporary file
            temp_file = os.path.join(self.temp_dir, f"tts_{int(time.time())}.mp3")
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file)
            
            # Play audio
            self._play_audio_file(temp_file)
            
            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass
                
            return True
        except Exception as e:
            print(f"❌ Error with gTTS: {e}")
            return False
    
    def _play_audio_file(self, file_path: str) -> bool:
        """
        Play an audio file.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Success status
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            # Try to use playsound (cross-platform)
            try:
                from playsound import playsound
                playsound(file_path)
                return True
            except ImportError:
                pass
            
            # Try platform-specific methods
            if os.name == 'posix':  # Linux/Mac
                os.system(f"mpg123 -q {file_path}")
                return True
            elif os.name == 'nt':  # Windows
                os.system(f"start /min {file_path}")
                return True
            
            return False
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop text-to-speech and clean up.
        
        Returns:
            Success status
        """
        try:
            # Stop speaker thread
            self.stop_speaking = True
            
            if self.speaker_thread and self.speaker_thread.is_alive():
                self.speaker_thread.join(timeout=2.0)
            
            # Clear queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Stop pyttsx3 engine
            if self.has_pyttsx3 and self.engine_pyttsx3:
                try:
                    self.engine_pyttsx3.stop()
                except:
                    pass
            
            return True
        except Exception as e:
            print(f"❌ Error stopping text-to-speech: {e}")
            return False
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get list of available voices.
        
        Returns:
            List of voice information dictionaries
        """
        voices = []
        
        if self.has_pyttsx3 and self.engine_pyttsx3:
            try:
                for voice in self.engine_pyttsx3.getProperty('voices'):
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'languages': voice.languages,
                        'gender': 'female' if 'female' in voice.name.lower() else 'male',
                        'engine': 'pyttsx3'
                    })
            except Exception as e:
                print(f"❌ Error getting pyttsx3 voices: {e}")
        
        return voices
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set voice by ID.
        
        Args:
            voice_id: Voice ID to use
            
        Returns:
            Success status
        """
        if not self.has_pyttsx3 or not self.engine_pyttsx3:
            return False
        
        try:
            self.engine_pyttsx3.setProperty('voice', voice_id)
            self.voice_id = voice_id
            return True
        except Exception as e:
            print(f"❌ Error setting voice: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of text-to-speech system.
        
        Returns:
            Status information
        """
        return {
            'available': self.available,
            'engines': {
                'pyttsx3': self.has_pyttsx3,
                'gtts': self.has_gtts
            },
            'voice_id': self.voice_id,
            'rate': self.rate,
            'volume': self.volume,
            'queue_size': self.speech_queue.qsize() if hasattr(self, 'speech_queue') else 0
        }