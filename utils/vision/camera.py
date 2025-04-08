import os
import time
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
import base64
import json
import tempfile
from PIL import Image, ImageGrab
import threading

# Try to import vision-related libraries
try:
    import torch
    from transformers import AutoProcessor, AutoModelForVision2Seq
    HAS_VISION_MODELS = True
except ImportError:
    HAS_VISION_MODELS = False

class CameraManager:
    """
    Manages camera and vision functionality.
    Provides interfaces for webcam capture, screen capture, and image analysis.
    """
    
    def __init__(self, 
                camera_id: int = 0, 
                model_name: str = "microsoft/git-base"):
        """
        Initialize the camera manager.
        
        Args:
            camera_id: Camera device ID
            model_name: Vision model name for image captioning
        """
        self.camera_id = camera_id
        self.camera = None
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.lock = threading.Lock()
        
        # Flags for available features
        self._has_screen_capture = self._check_screen_capture()
        self._has_vision_models = HAS_VISION_MODELS
        
        # Create temporary directory for saving images
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "frames"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "screenshots"), exist_ok=True)
        
        # Initialize vision models if available
        if self._has_vision_models:
            self._init_vision_models()
    
    def _check_screen_capture(self) -> bool:
        """Check if screen capture is available."""
        try:
            # Try to import and use ImageGrab
            test_grab = ImageGrab.grab(bbox=(0, 0, 10, 10))
            return True
        except Exception:
            return False
    
    def _init_vision_models(self) -> bool:
        """Initialize vision models."""
        if not HAS_VISION_MODELS:
            print("⚠️ Vision models not available: missing dependencies")
            return False
        
        try:
            print(f"🔄 Loading vision model: {self.model_name}")
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForVision2Seq.from_pretrained(self.model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
                print(f"✅ Vision model loaded on GPU: {torch.cuda.get_device_name(0)}")
            else:
                print("✅ Vision model loaded on CPU")
            
            return True
        except Exception as e:
            print(f"❌ Error loading vision model: {e}")
            self.processor = None
            self.model = None
            return False
    
    def initialize(self) -> bool:
        """Initialize the camera."""
        with self.lock:
            if self.camera is not None:
                # Camera is already initialized
                return True
            
            try:
                self.camera = cv2.VideoCapture(self.camera_id)
                
                # Check if camera opened successfully
                if not self.camera.isOpened():
                    raise RuntimeError(f"Failed to open camera with ID {self.camera_id}")
                
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                return True
            except Exception as e:
                print(f"❌ Error initializing camera: {e}")
                self.camera = None
                return False
    
    def release(self) -> None:
        """Release camera resources."""
        with self.lock:
            if self.camera is not None:
                self.camera.release()
                self.camera = None
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a frame from the webcam.
        
        Returns:
            Captured frame as numpy array or None if failed
        """
        with self.lock:
            if self.camera is None:
                if not self.initialize():
                    return None
            
            # Capture frame
            ret, frame = self.camera.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                return None
            
            return frame
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Capture a screenshot of the desktop.
        
        Returns:
            Screenshot as numpy array or None if failed
        """
        if not self._has_screen_capture:
            print("❌ Screen capture not available")
            return None
        
        try:
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Convert to numpy array
            screenshot_np = np.array(screenshot)
            
            # Convert from RGB to BGR (OpenCV format)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            return screenshot_bgr
        except Exception as e:
            print(f"❌ Error capturing screen: {e}")
            return None
    
    def save_frame(self, frame: np.ndarray, filename: Optional[str] = None) -> Optional[str]:
        """
        Save a frame to disk.
        
        Args:
            frame: Frame to save
            filename: Filename to use (if None, generate one)
            
        Returns:
            Path to saved file or None if failed
        """
        if frame is None:
            return None
        
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"frame_{timestamp}.jpg"
            
            file_path = os.path.join(self.temp_dir, "frames", filename)
            cv2.imwrite(file_path, frame)
            
            return file_path
        except Exception as e:
            print(f"❌ Error saving frame: {e}")
            return None
    
    def save_screenshot(self, screenshot: np.ndarray, filename: Optional[str] = None) -> Optional[str]:
        """
        Save a screenshot to disk.
        
        Args:
            screenshot: Screenshot to save
            filename: Filename to use (if None, generate one)
            
        Returns:
            Path to saved file or None if failed
        """
        if screenshot is None:
            return None
        
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.jpg"
            
            file_path = os.path.join(self.temp_dir, "screenshots", filename)
            cv2.imwrite(file_path, screenshot)
            
            return file_path
        except Exception as e:
            print(f"❌ Error saving screenshot: {e}")
            return None
    
    def describe_frame(self, frame: np.ndarray) -> str:
        """
        Generate a text description of a webcam frame.
        
        Args:
            frame: Frame to describe
            
        Returns:
            Text description
        """
        if frame is None:
            return "No frame available"
        
        if not self._has_vision_models or self.processor is None or self.model is None:
            return "Frame analysis not available: vision models missing"
        
        try:
            # Convert from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create PIL image
            image = Image.fromarray(frame_rgb)
            
            # Process image with vision model
            inputs = self.processor(images=image, return_tensors="pt")
            
            # Move inputs to GPU if available
            if torch.cuda.is_available():
                inputs = {key: value.to("cuda") for key, value in inputs.items()}
            
            # Generate outputs
            outputs = self.model.generate(
                **inputs,
                max_length=50,
                num_beams=4,
                early_stopping=True
            )
            
            # Decode output tokens
            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            return description
        except Exception as e:
            print(f"❌ Error analyzing frame: {e}")
            return f"Error analyzing image: {str(e)}"
    
    def describe_screen(self, screenshot: np.ndarray) -> str:
        """
        Generate a text description of a screenshot.
        
        Args:
            screenshot: Screenshot to describe
            
        Returns:
            Text description
        """
        if screenshot is None:
            return "No screenshot available"
        
        if not self._has_vision_models or self.processor is None or self.model is None:
            return "Screenshot analysis not available: vision models missing"
        
        try:
            # Convert from BGR to RGB
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Create PIL image
            image = Image.fromarray(screenshot_rgb)
            
            # Process image with vision model
            inputs = self.processor(images=image, return_tensors="pt")
            
            # Move inputs to GPU if available
            if torch.cuda.is_available():
                inputs = {key: value.to("cuda") for key, value in inputs.items()}
            
            # Generate outputs
            outputs = self.model.generate(
                **inputs,
                max_length=50,
                num_beams=4,
                early_stopping=True
            )
            
            # Decode output tokens
            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            return f"I see a desktop screen showing: {description}"
        except Exception as e:
            print(f"❌ Error analyzing screenshot: {e}")
            return f"Error analyzing screenshot: {str(e)}"
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        Get information about the camera.
        
        Returns:
            Camera information
        """
        info = {
            "camera_id": self.camera_id,
            "initialized": self.camera is not None
        }
        
        if self.camera is not None:
            info["width"] = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            info["height"] = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            info["fps"] = int(self.camera.get(cv2.CAP_PROP_FPS))
        
        return info
    
    def has_screen_capture(self) -> bool:
        """Check if screen capture is available."""
        return self._has_screen_capture