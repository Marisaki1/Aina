import os
import time
import numpy as np
import cv2
from typing import Dict, List, Any, Optional, Tuple, Union
import tempfile
from PIL import Image, ImageGrab
import json

# Try to import OCR and vision libraries
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import torch
    from transformers import AutoProcessor, AutoModelForVision2Seq
    HAS_VISION_MODELS = True
except ImportError:
    HAS_VISION_MODELS = False

class ScreenAnalyzer:
    """
    Analyzes desktop screen content for understanding and interaction.
    Provides OCR, element detection, and semantic analysis.
    """
    
    def __init__(self, 
                vision_model_name: str = "microsoft/git-base",
                tesseract_cmd: Optional[str] = None,
                temp_dir: Optional[str] = None):
        """
        Initialize screen analyzer.
        
        Args:
            vision_model_name: Vision model name for image captioning
            tesseract_cmd: Path to Tesseract OCR executable
            temp_dir: Directory for temporary files
        """
        self.vision_model_name = vision_model_name
        self.processor = None
        self.model = None
        
        # Set Tesseract path if provided
        if tesseract_cmd and HAS_TESSERACT:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Check capabilities
        self._has_screen_capture = self._check_screen_capture()
        self._has_ocr = HAS_TESSERACT
        self._has_vision_models = HAS_VISION_MODELS
        
        # Create temporary directory
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = tempfile.mkdtemp()
        
        os.makedirs(os.path.join(self.temp_dir, "screenshots"), exist_ok=True)
        
        # Initialize vision models if available
        if self._has_vision_models:
            self._init_vision_models()
        
        print(f"✅ Screen analyzer initialized (OCR: {'available' if self._has_ocr else 'unavailable'}, " +
              f"Vision: {'available' if self._has_vision_models else 'unavailable'})")
    
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
            print(f"🔄 Loading vision model: {self.vision_model_name}")
            self.processor = AutoProcessor.from_pretrained(self.vision_model_name)
            self.model = AutoModelForVision2Seq.from_pretrained(self.vision_model_name)
            
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
    
    def capture_screen(self, 
                      region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Capture the desktop screen.
        
        Args:
            region: Screen region to capture (left, top, right, bottom) or None for full screen
            
        Returns:
            Screenshot as numpy array or None if failed
        """
        if not self._has_screen_capture:
            print("❌ Screen capture not available")
            return None
        
        try:
            # Capture screen
            screenshot = ImageGrab.grab(bbox=region)
            
            # Convert to numpy array
            screenshot_np = np.array(screenshot)
            
            # Convert from RGB to BGR (OpenCV format)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            return screenshot_bgr
        except Exception as e:
            print(f"❌ Error capturing screen: {e}")
            return None
    
    def save_screenshot(self, 
                       screenshot: np.ndarray, 
                       filename: Optional[str] = None) -> Optional[str]:
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
    
    def extract_text(self, screenshot: np.ndarray) -> str:
        """
        Extract text from screenshot using OCR.
        
        Args:
            screenshot: Screenshot as numpy array
            
        Returns:
            Extracted text
        """
        if not self._has_ocr:
            return "OCR not available"
        
        if screenshot is None:
            return ""
        
        try:
            # Convert from BGR to RGB
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(screenshot_rgb)
            
            return text.strip()
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return f"Error: {str(e)}"
    
    def extract_text_with_layout(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """
        Extract text with positional information.
        
        Args:
            screenshot: Screenshot as numpy array
            
        Returns:
            Dictionary with text and layout information
        """
        if not self._has_ocr:
            return {"error": "OCR not available"}
        
        if screenshot is None:
            return {"error": "No screenshot provided"}
        
        try:
            # Convert from BGR to RGB
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Get data including bounding boxes
            data = pytesseract.image_to_data(screenshot_rgb, output_type=pytesseract.Output.DICT)
            
            # Process the results
            result = {
                "text": "",
                "blocks": []
            }
            
            # Group by block
            current_block = ""
            current_block_id = -1
            blocks = []
            
            for i in range(len(data["text"])):
                # Skip empty text
                if not data["text"][i].strip():
                    continue
                
                # Check if new block
                if data["block_num"][i] != current_block_id:
                    if current_block:
                        blocks.append(current_block)
                    current_block = data["text"][i]
                    current_block_id = data["block_num"][i]
                else:
                    current_block += " " + data["text"][i]
            
            # Add last block
            if current_block:
                blocks.append(current_block)
            
            # Add to result
            result["text"] = " ".join(blocks)
            result["blocks"] = blocks
            
            # Add bounding boxes for regions with text
            regions = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    regions.append({
                        "text": data["text"][i],
                        "confidence": data["conf"][i],
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i]
                    })
            
            result["regions"] = regions
            
            return result
        except Exception as e:
            print(f"❌ Error extracting text with layout: {e}")
            return {"error": str(e)}
    
    def describe_screenshot(self, screenshot: np.ndarray) -> str:
        """
        Generate a text description of a screenshot.
        
        Args:
            screenshot: Screenshot as numpy array
            
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
                max_length=100,
                num_beams=4,
                early_stopping=True
            )
            
            # Decode output tokens
            description = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            return f"I see a desktop screen showing: {description}"
        except Exception as e:
            print(f"❌ Error analyzing screenshot: {e}")
            return f"Error analyzing screenshot: {str(e)}"
    
    def analyze_screen_elements(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """
        Analyze screen elements (windows, buttons, etc.).
        
        Args:
            screenshot: Screenshot as numpy array
            
        Returns:
            Analysis results with element types and positions
        """
        if screenshot is None:
            return {"error": "No screenshot provided"}
        
        # Get text with layout
        text_info = self.extract_text_with_layout(screenshot)
        
        # Generate visual description
        visual_description = self.describe_screenshot(screenshot)
        
        # Simple element detection based on OCR
        elements = []
        if "regions" in text_info:
            for region in text_info["regions"]:
                # Try to classify UI element type
                element_type = "text"
                text = region["text"].lower()
                
                # Button detection
                if (text in ["ok", "cancel", "submit", "save", "close", "yes", "no"] or
                    region["width"] < 150 and region["height"] < 50):
                    element_type = "button"
                
                # Input field detection
                elif ":" in text or text.endswith("?"):
                    element_type = "label"
                
                # Menu item detection
                elif text in ["file", "edit", "view", "help", "tools", "settings", "options"]:
                    element_type = "menu"
                
                elements.append({
                    "type": element_type,
                    "text": region["text"],
                    "position": {
                        "x": region["x"],
                        "y": region["y"],
                        "width": region["width"],
                        "height": region["height"]
                    }
                })
        
        return {
            "text": text_info.get("text", ""),
            "elements": elements,
            "visual_description": visual_description
        }
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        Get information about the screen.
        
        Returns:
            Screen information
        """
        info = {
            "screen_capture_available": self._has_screen_capture,
            "ocr_available": self._has_ocr,
            "vision_models_available": self._has_vision_models
        }
        
        if self._has_screen_capture:
            try:
                # Get screen size
                screenshot = ImageGrab.grab()
                info["width"] = screenshot.width
                info["height"] = screenshot.height
            except Exception:
                pass
        
        return info
    
    def has_screen_capture(self) -> bool:
        """Check if screen capture is available."""
        return self._has_screen_capture