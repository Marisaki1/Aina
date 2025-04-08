import os
import time
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import json
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import tempfile

# Try to import required libraries for UI detection
try:
    import torch
    from transformers import AutoImageProcessor, AutoModelForObjectDetection
    HAS_OBJECT_DETECTION = True
except ImportError:
    HAS_OBJECT_DETECTION = False

# Try to import OCR libraries
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# Setup logger
logger = logging.getLogger("aina.vision.screen")

class AdvancedScreenAnalyzer:
    """
    Advanced screen analysis for understanding desktop UI elements,
    application states, and providing guidance for interaction.
    """
    
    def __init__(self, 
                object_model: str = "microsoft/table-transformer-detection",
                ocr_threshold: float = 0.6,
                temp_dir: Optional[str] = None):
        """
        Initialize advanced screen analyzer.
        
        Args:
            object_model: Model for object detection
            ocr_threshold: Confidence threshold for OCR
            temp_dir: Directory for temporary files
        """
        self.object_model_name = object_model
        self.ocr_threshold = ocr_threshold
        
        # Create temporary directory
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = tempfile.mkdtemp()
        
        os.makedirs(os.path.join(self.temp_dir, "screenshots"), exist_ok=True)
        
        # Check capabilities
        self._has_screen_capture = self._check_screen_capture()
        self._has_ocr = HAS_TESSERACT
        self._has_object_detection = HAS_OBJECT_DETECTION
        
        # Initialize models if available
        self.object_processor = None
        self.object_model = None
        
        if self._has_object_detection:
            self._init_object_detection()
        
        # Keep track of previous screenshot for change detection
        self.previous_screenshot = None
        
        # Store application detection history
        self.application_history = {}
        
        # UI element definitions for recognition
        self.ui_elements = {
            "button": {
                "patterns": ["button", "btn", "submit", "cancel", "ok", "yes", "no", "save", "close", "open"],
                "shape": "rectangle",
                "aspect_ratio": (2, 5)  # width typically 2-5 times the height
            },
            "textbox": {
                "patterns": ["input", "text", "field", "enter"],
                "shape": "rectangle",
                "aspect_ratio": (3, 8)  # width typically 3-8 times the height
            },
            "checkbox": {
                "patterns": ["check", "checkbox", "toggle"],
                "shape": "square",
                "aspect_ratio": (0.8, 1.2)  # approximately square
            },
            "dropdown": {
                "patterns": ["select", "dropdown", "menu", "options"],
                "shape": "rectangle",
                "aspect_ratio": (3, 10)  # width typically 3-10 times the height
            },
            "menu": {
                "patterns": ["menu", "file", "edit", "view", "tools", "help", "options", "settings"],
                "shape": "rectangle",
                "aspect_ratio": (3, 15)  # can be quite wide
            }
        }
        
        logger.info("Advanced screen analyzer initialized")
    
    def _check_screen_capture(self) -> bool:
        """Check if screen capture is available."""
        try:
            test_grab = ImageGrab.grab(bbox=(0, 0, 10, 10))
            return True
        except Exception as e:
            logger.error(f"Screen capture not available: {e}")
            return False
    
    def _init_object_detection(self) -> bool:
        """Initialize object detection model."""
        try:
            logger.info(f"Loading object detection model: {self.object_model_name}")
            
            # Load model and processor
            self.object_processor = AutoImageProcessor.from_pretrained(self.object_model_name)
            self.object_model = AutoModelForObjectDetection.from_pretrained(self.object_model_name)
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.object_model = self.object_model.to("cuda")
                logger.info(f"Object detection model loaded on GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Object detection model loaded on CPU")
            
            return True
        except Exception as e:
            logger.error(f"Error loading object detection model: {e}")
            return False
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Capture the screen or a region of it.
        
        Args:
            region: Screen region to capture (left, top, right, bottom) or None for full screen
            
        Returns:
            Screenshot as numpy array or None if failed
        """
        if not self._has_screen_capture:
            logger.error("Screen capture not available")
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
            logger.error(f"Error capturing screen: {e}")
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
                filename = f"screenshot_{timestamp}.png"
            
            file_path = os.path.join(self.temp_dir, "screenshots", filename)
            cv2.imwrite(file_path, screenshot)
            
            return file_path
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return None
    
    def analyze_screen(self, screenshot: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of screen content.
        
        Args:
            screenshot: Screenshot to analyze (if None, will capture)
            
        Returns:
            Analysis results
        """
        if screenshot is None:
            screenshot = self.capture_screen()
        
        if screenshot is None:
            return {"error": "Failed to capture screen"}
        
        # Save current screenshot for change detection
        if self.previous_screenshot is None:
            self.previous_screenshot = screenshot.copy()
        
        # Analyze UI elements
        ui_elements = self.detect_ui_elements(screenshot)
        
        # Perform OCR
        text_data = self.extract_text_with_positions(screenshot)
        
        # Detect application
        app_info = self.detect_application(screenshot)
        
        # Detect screen changes
        changes = self.detect_screen_changes(screenshot)
        
        # Generate overall description
        description = self.generate_screen_description(
            screenshot, ui_elements, text_data, app_info
        )
        
        # Update previous screenshot for next comparison
        self.previous_screenshot = screenshot.copy()
        
        # Create analysis result
        result = {
            "ui_elements": ui_elements,
            "text": text_data,
            "application": app_info,
            "changes": changes,
            "description": description,
            "timestamp": time.time()
        }
        
        return result
    
    def detect_ui_elements(self, screenshot: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect UI elements in the screenshot.
        
        Args:
            screenshot: Screenshot to analyze
            
        Returns:
            List of detected UI elements
        """
        elements = []
        
        # Use object detection if available
        if self._has_object_detection and self.object_model:
            elements.extend(self._detect_elements_with_model(screenshot))
        
        # Use traditional CV techniques for additional detection
        additional_elements = self._detect_elements_with_cv(screenshot)
        
        # Merge elements, avoiding duplicates
        existing_bboxes = [(e["x"], e["y"], e["width"], e["height"]) for e in elements]
        
        for element in additional_elements:
            bbox = (element["x"], element["y"], element["width"], element["height"])
            
            # Check if this element overlaps with existing ones
            duplicate = False
            for ex_bbox in existing_bboxes:
                if self._boxes_overlap(bbox, ex_bbox, threshold=0.7):
                    duplicate = True
                    break
            
            if not duplicate:
                elements.append(element)
                existing_bboxes.append(bbox)
        
        # Refine element types using OCR data if available
        if self._has_ocr:
            elements = self._refine_elements_with_ocr(screenshot, elements)
        
        return elements
    
    def _detect_elements_with_model(self, screenshot: np.ndarray) -> List[Dict[str, Any]]:
        """Detect UI elements using object detection model."""
        elements = []
        
        try:
            # Convert from BGR to RGB
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Create PIL image
            image = Image.fromarray(screenshot_rgb)
            
            # Process image with object detection model
            inputs = self.object_processor(images=image, return_tensors="pt")
            
            # Move inputs to GPU if available
            if torch.cuda.is_available():
                inputs = {key: value.to("cuda") for key, value in inputs.items()}
            
            # Generate outputs
            with torch.no_grad():
                outputs = self.object_model(**inputs)
            
            # Convert outputs to detections
            target_sizes = torch.tensor([image.size[::-1]])
            if torch.cuda.is_available():
                target_sizes = target_sizes.to("cuda")
            
            results = self.object_processor.post_process_object_detection(
                outputs, 
                threshold=0.5, 
                target_sizes=target_sizes
            )[0]
            
            # Process results
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                # Convert box to integers
                box = [int(i) for i in box.tolist()]
                x, y, x2, y2 = box
                
                # Get class name
                class_name = self.object_model.config.id2label[label.item()]
                
                # Map model classes to UI element types
                ui_type = "unknown"
                if "button" in class_name.lower():
                    ui_type = "button"
                elif "input" in class_name.lower() or "field" in class_name.lower():
                    ui_type = "textbox"
                elif "checkbox" in class_name.lower():
                    ui_type = "checkbox"
                elif "dropdown" in class_name.lower() or "select" in class_name.lower():
                    ui_type = "dropdown"
                elif "menu" in class_name.lower():
                    ui_type = "menu"
                else:
                    ui_type = "ui_element"
                
                # Add element
                element = {
                    "type": ui_type,
                    "class": class_name,
                    "confidence": float(score),
                    "x": x,
                    "y": y,
                    "width": x2 - x,
                    "height": y2 - y,
                    "detection_method": "model"
                }
                
                elements.append(element)
                
        except Exception as e:
            logger.error(f"Error in model-based UI detection: {e}")
        
        return elements
    
    def _detect_elements_with_cv(self, screenshot: np.ndarray) -> List[Dict[str, Any]]:
        """Detect UI elements using traditional computer vision techniques."""
        elements = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size
            min_area = 100  # Minimum area to consider
            max_area = screenshot.shape[0] * screenshot.shape[1] * 0.25  # Maximum 25% of screen
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if min_area <= area <= max_area:
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Skip if too small
                    if w < 10 or h < 10:
                        continue
                    
                    # Try to determine type based on shape
                    ui_type = self._guess_element_type(gray[y:y+h, x:x+w], w, h)
                    
                    # Add element
                    element = {
                        "type": ui_type,
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "confidence": 0.5,  # Lower confidence for CV-based detection
                        "detection_method": "cv"
                    }
                    
                    elements.append(element)
        
        except Exception as e:
            logger.error(f"Error in CV-based UI detection: {e}")
        
        return elements
    
    def _guess_element_type(self, roi: np.ndarray, width: int, height: int) -> str:
        """Guess UI element type based on shape and properties."""
        # Calculate aspect ratio
        aspect_ratio = width / max(height, 1)
        
        # Check if it's approximately square (checkbox, radio button)
        if 0.8 <= aspect_ratio <= 1.2 and width < 50:
            return "checkbox"
        
        # Check if it's a button (rectangle with moderate aspect ratio)
        if 1.5 <= aspect_ratio <= 5 and width < 200:
            return "button"
        
        # Check if it's a textbox (rectangle with larger aspect ratio)
        if 3 <= aspect_ratio <= 10:
            return "textbox"
        
        # Default to generic UI element
        return "ui_element"
    
    def _refine_elements_with_ocr(self, 
                                 screenshot: np.ndarray, 
                                 elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Refine UI element types using OCR data."""
        if not self._has_ocr:
            return elements
        
        try:
            # Convert to RGB for OCR
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Process each element
            for i, element in enumerate(elements):
                # Extract ROI
                x, y, w, h = element["x"], element["y"], element["width"], element["height"]
                roi = screenshot_rgb[y:y+h, x:x+w]
                
                # Expand ROI slightly for better OCR
                expanded_y = max(0, y - 5)
                expanded_h = min(screenshot.shape[0] - expanded_y, h + 10)
                expanded_x = max(0, x - 5)
                expanded_w = min(screenshot.shape[1] - expanded_x, w + 10)
                
                expanded_roi = screenshot_rgb[expanded_y:expanded_y+expanded_h, expanded_x:expanded_x+expanded_w]
                
                # Perform OCR
                text = pytesseract.image_to_string(expanded_roi).strip().lower()
                
                if text:
                    # Update element with text
                    elements[i]["text"] = text
                    
                    # Check for UI element indicators in text
                    for element_type, type_info in self.ui_elements.items():
                        for pattern in type_info["patterns"]:
                            if pattern in text:
                                elements[i]["type"] = element_type
                                elements[i]["confidence"] = max(elements[i].get("confidence", 0), 0.7)
                                break
        
        except Exception as e:
            logger.error(f"Error refining elements with OCR: {e}")
        
        return elements
    
    def extract_text_with_positions(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """
        Extract text from screenshot with positions.
        
        Args:
            screenshot: Screenshot to analyze
            
        Returns:
            Dictionary with text and position information
        """
        if not self._has_ocr:
            return {"error": "OCR not available"}
        
        try:
            # Convert to RGB for OCR
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            
            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(
                screenshot_rgb, 
                output_type=pytesseract.Output.DICT
            )
            
            # Process OCR data
            text_blocks = []
            current_block = ""
            current_block_coords = (0, 0, 0, 0)
            current_block_confidence = 0
            current_word_count = 0
            
            for i in range(len(ocr_data["text"])):
                text = ocr_data["text"][i]
                conf = int(ocr_data["conf"][i])
                
                # Skip empty text or low confidence
                if not text.strip() or conf < self.ocr_threshold * 100:
                    # Save current block if not empty
                    if current_block:
                        text_blocks.append({
                            "text": current_block,
                            "x": current_block_coords[0],
                            "y": current_block_coords[1],
                            "width": current_block_coords[2],
                            "height": current_block_coords[3],
                            "confidence": current_block_confidence / max(1, current_word_count)
                        })
                        
                        current_block = ""
                        current_word_count = 0
                    
                    continue
                
                # Get word coordinates
                x = ocr_data["left"][i]
                y = ocr_data["top"][i]
                w = ocr_data["width"][i]
                h = ocr_data["height"][i]
                
                if not current_block:
                    # Start new block
                    current_block = text
                    current_block_coords = (x, y, w, h)
                    current_block_confidence = conf
                    current_word_count = 1
                else:
                    # Check if this word belongs to current block (based on position)
                    block_x, block_y, block_w, block_h = current_block_coords
                    
                    # If the word is close to the current block horizontally and vertically
                    if (abs(y - block_y) < block_h * 0.7 and 
                        (x - (block_x + block_w) < block_h * 3)):
                        # Extend current block
                        current_block += " " + text
                        current_block_coords = (
                            block_x,
                            min(block_y, y),
                            max(block_x + block_w, x + w) - block_x,
                            max(block_y + block_h, y + h) - min(block_y, y)
                        )
                        current_block_confidence += conf
                        current_word_count += 1
                    else:
                        # Save current block and start new one
                        if current_block:
                            text_blocks.append({
                                "text": current_block,
                                "x": current_block_coords[0],
                                "y": current_block_coords[1],
                                "width": current_block_coords[2],
                                "height": current_block_coords[3],
                                "confidence": current_block_confidence / current_word_count
                            })
                        
                        current_block = text
                        current_block_coords = (x, y, w, h)
                        current_block_confidence = conf
                        current_word_count = 1
            
            # Add the last block if not empty
            if current_block:
                text_blocks.append({
                    "text": current_block,
                    "x": current_block_coords[0],
                    "y": current_block_coords[1],
                    "width": current_block_coords[2],
                    "height": current_block_coords[3],
                    "confidence": current_block_confidence / current_word_count
                })
            
            # Combine all text
            full_text = " ".join([block["text"] for block in text_blocks])
            
            return {
                "full_text": full_text,
                "blocks": text_blocks
            }
            
        except Exception as e:
            logger.error(f"Error extracting text with positions: {e}")
            return {"error": f"OCR failed: {str(e)}"}
    
    def detect_application(self, screenshot: np.ndarray) -> Dict[str, Any]:
        """
        Detect the application shown in the screenshot.
        
        Args:
            screenshot: Screenshot to analyze
            
        Returns:
            Application information
        """
        # Extract text from top region (likely contains title bar)
        if not self._has_ocr:
            return {"name": "Unknown", "confidence": 0.0}
        
        try:
            # Take the top 40 pixels as the potential title bar
            title_bar = screenshot[:40, :]
            
            # Convert to RGB for OCR
            title_bar_rgb = cv2.cvtColor(title_bar, cv2.COLOR_BGR2RGB)
            
            # Perform OCR
            title_text = pytesseract.image_to_string(title_bar_rgb).strip()
            
            # Common applications to detect
            common_apps = {
                "chrome": ["chrome", "google chrome", "chromium"],
                "firefox": ["firefox", "mozilla firefox"],
                "edge": ["edge", "microsoft edge"],
                "word": ["word", "microsoft word", "doc", "document"],
                "excel": ["excel", "microsoft excel", "spreadsheet"],
                "powerpoint": ["powerpoint", "microsoft powerpoint", "presentation"],
                "notepad": ["notepad", "text editor"],
                "file explorer": ["file explorer", "this pc", "documents", "file manager"],
                "settings": ["settings", "control panel", "system settings"],
                "terminal": ["terminal", "command prompt", "cmd", "powershell", "bash", "shell"]
            }
            
            # Check if title matches any common app
            app_name = "Unknown"
            confidence = 0.0
            
            if title_text:
                title_lower = title_text.lower()
                
                for app, keywords in common_apps.items():
                    for keyword in keywords:
                        if keyword in title_lower:
                            app_name = app
                            confidence = 0.8
                            break
                
                # If no match found, use the title as the app name
                if app_name == "Unknown" and len(title_text) > 3:
                    # Extract the first part of the title (often the app name)
                    app_name = title_text.split(" - ")[0].split(" | ")[0]
                    confidence = 0.5
            
            # Store in history for tracking
            if app_name != "Unknown" and confidence > 0.5:
                self.application_history[app_name] = {
                    "last_seen": time.time(),
                    "count": self.application_history.get(app_name, {}).get("count", 0) + 1
                }
            
            return {
                "name": app_name,
                "title": title_text,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error detecting application: {e}")
            return {"name": "Unknown", "confidence": 0.0}
    
    def detect_screen_changes(self, current_screenshot: np.ndarray) -> Dict[str, Any]:
        """
        Detect changes between current and previous screenshots.
        
        Args:
            current_screenshot: Current screenshot
            
        Returns:
            Dictionary with change information
        """
        if self.previous_screenshot is None:
            return {"changed": False, "change_percentage": 0.0}
        
        try:
            # Ensure same size
            if (self.previous_screenshot.shape[0] != current_screenshot.shape[0] or
                self.previous_screenshot.shape[1] != current_screenshot.shape[1]):
                # Resize previous to match current
                self.previous_screenshot = cv2.resize(
                    self.previous_screenshot,
                    (current_screenshot.shape[1], current_screenshot.shape[0])
                )
            
            # Convert to grayscale
            prev_gray = cv2.cvtColor(self.previous_screenshot, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(current_screenshot, cv2.COLOR_BGR2GRAY)
            
            # Calculate absolute difference
            diff = cv2.absdiff(prev_gray, curr_gray)
            
            # Apply threshold to get significant changes
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            
            # Calculate change percentage
            change_pixels = np.sum(thresh > 0)
            total_pixels = thresh.size
            change_percentage = (change_pixels / total_pixels) * 100
            
            # Find contours of changed regions
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Get major change regions
            change_regions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Ignore small changes
                if area < 100:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                change_regions.append({
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "area": area
                })
            
            # Sort regions by area (largest first)
            change_regions.sort(key=lambda r: r["area"], reverse=True)
            
            # Limit to top 5 regions
            change_regions = change_regions[:5]
            
            # Determine if significant change occurred
            significant_change = change_percentage > 1.0  # More than 1% changed
            
            return {
                "changed": significant_change,
                "change_percentage": change_percentage,
                "regions": change_regions
            }
            
        except Exception as e:
            logger.error(f"Error detecting screen changes: {e}")
            return {"changed": False, "change_percentage": 0.0}
    
    def generate_screen_description(self, 
                                  screenshot: np.ndarray,
                                  ui_elements: List[Dict[str, Any]],
                                  text_data: Dict[str, Any],
                                  app_info: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of the screen.
        
        Args:
            screenshot: Screenshot
            ui_elements: Detected UI elements
            text_data: Extracted text data
            app_info: Application information
            
        Returns:
            Description text
        """
        # Start with application information
        app_name = app_info.get("name", "Unknown")
        app_title = app_info.get("title", "")
        
        description = f"I see a {app_name} window"
        if app_title and app_title != app_name:
            description += f" with title \"{app_title}\""
        description += ". "
        
        # Count UI elements by type
        element_counts = {}
        for element in ui_elements:
            element_type = element.get("type", "ui_element")
            element_counts[element_type] = element_counts.get(element_type, 0) + 1
        
        # Add UI element summary
        if element_counts:
            description += "The screen contains "
            element_descriptions = []
            
            for element_type, count in element_counts.items():
                element_descriptions.append(f"{count} {element_type}{'s' if count > 1 else ''}")
            
            description += ", ".join(element_descriptions) + ". "
        
        # Add text summary
        if text_data.get("blocks"):
            text_block_count = len(text_data["blocks"])
            if text_block_count > 0:
                description += f"There are {text_block_count} text blocks on the screen. "
                
                # Add a few examples of the text
                if text_block_count > 0:
                    description += "Some text I can see: "
                    example_texts = []
                    
                    # Take up to 3 largest text blocks
                    sorted_blocks = sorted(
                        text_data["blocks"], 
                        key=lambda b: b.get("width", 0) * b.get("height", 0),
                        reverse=True
                    )
                    
                    for block in sorted_blocks[:3]:
                        text = block.get("text", "").strip()
                        if text and len(text) > 3:
                            # Truncate long text
                            if len(text) > 40:
                                text = text[:37] + "..."
                            
                            example_texts.append(f"\"{text}\"")
                    
                    description += ", ".join(example_texts) + ". "
        
        # Add screen dimensions
        height, width = screenshot.shape[:2]
        description += f"The screen resolution is {width}x{height} pixels."
        
        return description
    
    def highlight_ui_elements(self, 
                            screenshot: np.ndarray,
                            ui_elements: List[Dict[str, Any]]) -> np.ndarray:
        """
        Highlight detected UI elements on the screenshot.
        
        Args:
            screenshot: Original screenshot
            ui_elements: Detected UI elements
            
        Returns:
            Screenshot with highlighted elements
        """
        # Create a copy of the screenshot
        highlighted = screenshot.copy()
        
        # Color mapping for different element types
        colors = {
            "button": (0, 255, 0),      # Green
            "textbox": (255, 0, 0),     # Red
            "checkbox": (0, 0, 255),    # Blue
            "dropdown": (255, 255, 0),  # Yellow
            "menu": (255, 0, 255),      # Magenta
            "ui_element": (0, 255, 255) # Cyan
        }
        
        # Draw rectangles around UI elements
        for element in ui_elements:
            x = element.get("x", 0)
            y = element.get("y", 0)
            width = element.get("width", 0)
            height = element.get("height", 0)
            element_type = element.get("type", "ui_element")
            
            # Get color for this element type
            color = colors.get(element_type, (0, 255, 255))
            
            # Draw rectangle
            cv2.rectangle(highlighted, (x, y), (x + width, y + height), color, 2)
            
            # Add label
            label = element_type
            if "text" in element:
                label_text = element["text"]
                if len(label_text) > 20:
                    label_text = label_text[:17] + "..."
                label = f"{element_type}: {label_text}"
            
            cv2.putText(
                highlighted, 
                label, 
                (x, y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                color, 
                1
            )
        
        return highlighted
    
    def _boxes_overlap(self, 
                      box1: Tuple[int, int, int, int], 
                      box2: Tuple[int, int, int, int],
                      threshold: float = 0.5) -> bool:
        """
        Check if two bounding boxes overlap.
        
        Args:
            box1: First box (x, y, width, height)
            box2: Second box (x, y, width, height)
            threshold: Overlap threshold (0-1)
            
        Returns:
            True if boxes overlap significantly
        """
        # Convert to x1, y1, x2, y2 format
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        x1_2, y1_2 = x1 + w1, y1 + h1
        x2_2, y2_2 = x2 + w2, y2 + h2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1_2, x2_2)
        y_bottom = min(y1_2, y2_2)
        
        if x_right < x_left or y_bottom < y_top:
            return False  # No intersection
        
        # Calculate areas
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        box1_area = w1 * h1
        box2_area = w2 * h2
        
        # Calculate IoU (Intersection over Union)
        iou = intersection_area / (box1_area + box2_area - intersection_area)
        
        return iou >= threshold