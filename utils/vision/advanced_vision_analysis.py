import os
import time
import cv2
import numpy as np
import json
import sqlite3
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import threading
import pickle
from datetime import datetime

# Configure logging
logger = logging.getLogger("aina.vision.face")

# Try to import face recognition libraries
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False

try:
    from deepface import DeepFace # type: ignore
    HAS_DEEPFACE = True
except ImportError:
    HAS_DEEPFACE = False

# Try to import emotion recognition
try:
    from fer import FER # type: ignore
    HAS_FER = True
except ImportError:
    HAS_FER = False

class Person:
    """Class representing a person recognized by the system."""
    
    def __init__(self, 
                person_id: str, 
                name: str, 
                relation: str = "unknown",
                notes: str = ""):
        """
        Initialize person.
        
        Args:
            person_id: Unique ID for the person
            name: Person's name
            relation: Relationship to the system (e.g., "family", "friend")
            notes: Additional notes about the person
        """
        self.person_id = person_id
        self.name = name
        self.relation = relation
        self.notes = notes
        self.face_encodings = []
        self.face_images = []
        self.last_seen = 0
        self.first_seen = time.time()
        self.recognition_count = 0
        self.attributes = {}
    
    def add_face_encoding(self, encoding: np.ndarray, face_image: Optional[np.ndarray] = None) -> None:
        """
        Add a face encoding for this person.
        
        Args:
            encoding: Face encoding array
            face_image: Face image (optional)
        """
        self.face_encodings.append(encoding)
        
        if face_image is not None:
            self.face_images.append(face_image)
    
    def update_seen(self) -> None:
        """Update the last seen timestamp."""
        self.last_seen = time.time()
        self.recognition_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert person to dictionary for storage."""
        return {
            "person_id": self.person_id,
            "name": self.name,
            "relation": self.relation,
            "notes": self.notes,
            "last_seen": self.last_seen,
            "first_seen": self.first_seen,
            "recognition_count": self.recognition_count,
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Person':
        """Create person from dictionary."""
        person = cls(
            person_id=data["person_id"],
            name=data["name"],
            relation=data.get("relation", "unknown"),
            notes=data.get("notes", "")
        )
        
        person.last_seen = data.get("last_seen", 0)
        person.first_seen = data.get("first_seen", time.time())
        person.recognition_count = data.get("recognition_count", 0)
        person.attributes = data.get("attributes", {})
        
        return person

class AdvancedFaceRecognition:
    """
    Advanced face recognition system with identity management,
    emotion detection, and attribute recognition.
    """
    
    def __init__(self, 
                data_dir: str = "data/aina/face_recognition",
                face_db_file: str = "faces.db",
                encodings_file: str = "encodings.pkl",
                min_detection_confidence: float = 0.5,
                min_recognition_confidence: float = 0.6):
        """
        Initialize face recognition system.
        
        Args:
            data_dir: Directory for face recognition data
            face_db_file: SQLite database file for face data
            encodings_file: File for storing face encodings
            min_detection_confidence: Minimum confidence for face detection
            min_recognition_confidence: Minimum confidence for face recognition
        """
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, face_db_file)
        self.encodings_path = os.path.join(data_dir, encodings_file)
        self.min_detection_confidence = min_detection_confidence
        self.min_recognition_confidence = min_recognition_confidence
        
        # Thread lock for database access
        self.db_lock = threading.Lock()
        
        # Check capabilities
        self.has_face_recognition = HAS_FACE_RECOGNITION
        self.has_deepface = HAS_DEEPFACE
        self.has_emotion = HAS_FER
        
        # Initialize emotion detector if available
        self.emotion_detector = None
        if self.has_emotion:
            try:
                self.emotion_detector = FER()
                logger.info("Emotion detection enabled")
            except Exception as e:
                logger.error(f"Error initializing emotion detector: {e}")
                self.has_emotion = False
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "images"), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load known face encodings
        self.known_people = []
        self.known_encodings = []
        self.known_ids = []
        self._load_known_faces()
        
        # Recognition statistics
        self.recognition_stats = {
            "total_detections": 0,
            "total_recognitions": 0,
            "unknown_faces": 0
        }
        
        logger.info(f"Advanced face recognition initialized (detection={self.has_face_recognition}, " + 
                  f"deepface={self.has_deepface}, emotion={self.has_emotion})")
    
    def _init_database(self) -> None:
        """Initialize face database."""
        with self.db_lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Create people table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS people (
                    person_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    relation TEXT,
                    notes TEXT,
                    last_seen INTEGER,
                    first_seen INTEGER,
                    recognition_count INTEGER,
                    attributes TEXT
                )
                ''')
                
                # Create faces table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS faces (
                    face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    image_path TEXT,
                    captured_time INTEGER,
                    FOREIGN KEY (person_id) REFERENCES people (person_id)
                )
                ''')
                
                # Create recognition log table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS recognition_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT,
                    timestamp INTEGER,
                    confidence REAL,
                    emotions TEXT,
                    FOREIGN KEY (person_id) REFERENCES people (person_id)
                )
                ''')
                
                conn.commit()
                conn.close()
                
                logger.info("Face recognition database initialized")
            except Exception as e:
                logger.error(f"Error initializing database: {e}")
    
    def _load_known_faces(self) -> None:
        """Load known face encodings and people from database."""
        with self.db_lock:
            try:
                # Load people from database
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM people")
                people_rows = cursor.fetchall()
                
                self.known_people = []
                for row in people_rows:
                    person_dict = dict(row)
                    
                    # Convert attributes from JSON string
                    if "attributes" in person_dict and person_dict["attributes"]:
                        try:
                            person_dict["attributes"] = json.loads(person_dict["attributes"])
                        except:
                            person_dict["attributes"] = {}
                    
                    person = Person.from_dict(person_dict)
                    self.known_people.append(person)
                
                conn.close()
                
                # Load face encodings from file
                if os.path.exists(self.encodings_path):
                    try:
                        with open(self.encodings_path, "rb") as f:
                            encodings_data = pickle.load(f)
                            
                            self.known_encodings = encodings_data.get("encodings", [])
                            self.known_ids = encodings_data.get("ids", [])
                            
                            # Attach encodings to people
                            for i, person_id in enumerate(self.known_ids):
                                if i < len(self.known_encodings):
                                    for person in self.known_people:
                                        if person.person_id == person_id:
                                            person.add_face_encoding(self.known_encodings[i])
                                            break
                    except Exception as e:
                        logger.error(f"Error loading encodings: {e}")
                        self.known_encodings = []
                        self.known_ids = []
                
                logger.info(f"Loaded {len(self.known_people)} people with {len(self.known_encodings)} face encodings")
                
            except Exception as e:
                logger.error(f"Error loading known faces: {e}")
                self.known_people = []
                self.known_encodings = []
                self.known_ids = []
    
    def _save_encodings(self) -> bool:
        """Save face encodings to file."""
        with self.db_lock:
            try:
                # Prepare data for saving
                encodings_data = {
                    "encodings": self.known_encodings,
                    "ids": self.known_ids,
                    "updated": time.time()
                }
                
                # Save to file
                with open(self.encodings_path, "wb") as f:
                    pickle.dump(encodings_data, f)
                
                return True
            except Exception as e:
                logger.error(f"Error saving encodings: {e}")
                return False
    
    def _save_person(self, person: Person) -> bool:
        """Save person to database."""
        with self.db_lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Convert person to dict
                person_dict = person.to_dict()
                
                # Convert attributes to JSON string
                attributes_json = json.dumps(person_dict.get("attributes", {}))
                
                # Check if person already exists
                cursor.execute(
                    "SELECT * FROM people WHERE person_id = ?",
                    (person.person_id,)
                )
                
                if cursor.fetchone():
                    # Update existing person
                    cursor.execute(
                        """
                        UPDATE people 
                        SET name = ?, relation = ?, notes = ?, last_seen = ?, 
                            first_seen = ?, recognition_count = ?, attributes = ?
                        WHERE person_id = ?
                        """,
                        (
                            person.name, person.relation, person.notes, person.last_seen,
                            person.first_seen, person.recognition_count, attributes_json,
                            person.person_id
                        )
                    )
                else:
                    # Insert new person
                    cursor.execute(
                        """
                        INSERT INTO people 
                        (person_id, name, relation, notes, last_seen, first_seen, recognition_count, attributes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            person.person_id, person.name, person.relation, person.notes,
                            person.last_seen, person.first_seen, person.recognition_count,
                            attributes_json
                        )
                    )
                
                conn.commit()
                conn.close()
                
                return True
            
            except Exception as e:
                logger.error(f"Error saving person: {e}")
                return False
    
    def _add_recognition_log(self, 
                           person_id: Optional[str], 
                           confidence: float,
                           emotions: Optional[Dict[str, float]] = None) -> None:
        """Add entry to recognition log."""
        with self.db_lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Convert emotions to JSON string
                emotions_json = json.dumps(emotions) if emotions else None
                
                # Add log entry
                cursor.execute(
                    """
                    INSERT INTO recognition_log 
                    (person_id, timestamp, confidence, emotions)
                    VALUES (?, ?, ?, ?)
                    """,
                    (person_id, int(time.time()), confidence, emotions_json)
                )
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"Error adding recognition log: {e}")
    
    def add_person(self, 
                 name: str, 
                 face_image: np.ndarray,
                 relation: str = "unknown",
                 notes: str = "",
                 person_id: Optional[str] = None) -> Optional[str]:
        """
        Add a new person to the recognition system.
        
        Args:
            name: Person's name
            face_image: Image containing the person's face
            relation: Relationship to the system
            notes: Additional notes
            person_id: Explicit ID (if None, generates one)
            
        Returns:
            Person ID if successful, None otherwise
        """
        if not self.has_face_recognition:
            logger.error("Face recognition not available")
            return None
        
        try:
            # Detect faces in the image
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                logger.error("No face detected in the image")
                return None
            
            # Use the first face found
            face_location = face_locations[0]
            
            # Generate face encoding
            face_encodings = face_recognition.face_encodings(rgb_image, [face_location])
            
            if not face_encodings:
                logger.error("Could not generate face encoding")
                return None
            
            face_encoding = face_encodings[0]
            
            # Extract face image
            top, right, bottom, left = face_location
            face_image_crop = face_image[top:bottom, left:right]
            
            # Generate ID if not provided
            if person_id is None:
                person_id = f"person_{int(time.time())}_{hash(str(face_encoding))}"
            
            # Check if this face already exists
            matches = []
            if self.known_encodings:
                matches = face_recognition.compare_faces(
                    self.known_encodings, 
                    face_encoding,
                    tolerance=1.0 - self.min_recognition_confidence
                )
            
            if True in matches:
                # This face already exists
                match_index = matches.index(True)
                existing_id = self.known_ids[match_index]
                
                logger.warning(f"Face already exists with ID {existing_id}")
                
                # Find the existing person
                existing_person = None
                for person in self.known_people:
                    if person.person_id == existing_id:
                        existing_person = person
                        break
                
                if existing_person:
                    # Update existing person
                    existing_person.name = name
                    existing_person.relation = relation
                    existing_person.notes = notes
                    
                    # Save updated person
                    self._save_person(existing_person)
                    
                    return existing_id
                
                return None
            
            # Create new person
            person = Person(
                person_id=person_id,
                name=name,
                relation=relation,
                notes=notes
            )
            
            # Add face encoding
            person.add_face_encoding(face_encoding, face_image_crop)
            
            # Save face image
            image_filename = f"{person_id}_{int(time.time())}.jpg"
            image_path = os.path.join(self.data_dir, "images", image_filename)
            cv2.imwrite(image_path, face_image_crop)
            
            # Add to database
            self.known_people.append(person)
            self.known_encodings.append(face_encoding)
            self.known_ids.append(person_id)
            
            # Save to database
            self._save_person(person)
            self._save_encodings()
            
            # Add face to faces table
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO faces 
                    (person_id, image_path, captured_time)
                    VALUES (?, ?, ?)
                    """,
                    (person_id, image_path, int(time.time()))
                )
                
                conn.commit()
                conn.close()
            
            logger.info(f"Added new person: {name} (ID: {person_id})")
            
            return person_id
        
        except Exception as e:
            logger.error(f"Error adding person: {e}")
            return None
    
    def update_person(self, 
                    person_id: str, 
                    name: Optional[str] = None,
                    relation: Optional[str] = None,
                    notes: Optional[str] = None) -> bool:
        """
        Update person information.
        
        Args:
            person_id: Person ID to update
            name: New name (if None, keeps current)
            relation: New relation (if None, keeps current)
            notes: New notes (if None, keeps current)
            
        Returns:
            Success status
        """
        try:
            # Find person
            person = None
            for p in self.known_people:
                if p.person_id == person_id:
                    person = p
                    break
            
            if not person:
                logger.error(f"Person not found: {person_id}")
                return False
            
            # Update fields
            if name is not None:
                person.name = name
            
            if relation is not None:
                person.relation = relation
            
            if notes is not None:
                person.notes = notes
            
            # Save to database
            return self._save_person(person)
            
        except Exception as e:
            logger.error(f"Error updating person: {e}")
            return False
    
    def add_face_to_person(self, 
                         person_id: str, 
                         face_image: np.ndarray) -> bool:
        """
        Add another face image to an existing person.
        
        Args:
            person_id: Person ID to update
            face_image: Image containing the person's face
            
        Returns:
            Success status
        """
        if not self.has_face_recognition:
            logger.error("Face recognition not available")
            return False
        
        try:
            # Find person
            person = None
            for p in self.known_people:
                if p.person_id == person_id:
                    person = p
                    break
            
            if not person:
                logger.error(f"Person not found: {person_id}")
                return False
            
            # Detect faces in the image
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                logger.error("No face detected in the image")
                return False
            
            # Use the first face found
            face_location = face_locations[0]
            
            # Generate face encoding
            face_encodings = face_recognition.face_encodings(rgb_image, [face_location])
            
            if not face_encodings:
                logger.error("Could not generate face encoding")
                return False
            
            face_encoding = face_encodings[0]
            
            # Extract face image
            top, right, bottom, left = face_location
            face_image_crop = face_image[top:bottom, left:right]
            
            # Add face encoding to person
            person.add_face_encoding(face_encoding, face_image_crop)
            
            # Update known encodings and IDs
            self.known_encodings.append(face_encoding)
            self.known_ids.append(person_id)
            
            # Save face image
            image_filename = f"{person_id}_{int(time.time())}.jpg"
            image_path = os.path.join(self.data_dir, "images", image_filename)
            cv2.imwrite(image_path, face_image_crop)
            
            # Save encodings
            self._save_encodings()
            
            # Add face to faces table
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    INSERT INTO faces 
                    (person_id, image_path, captured_time)
                    VALUES (?, ?, ?)
                    """,
                    (person_id, image_path, int(time.time()))
                )
                
                conn.commit()
                conn.close()
            
            logger.info(f"Added new face to person {person.name} (ID: {person_id})")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding face to person: {e}")
            return False
    
    def recognize_faces(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Recognize faces in an image.
        
        Args:
            image: Image to analyze
            
        Returns:
            List of recognized faces with details
        """
        if not self.has_face_recognition:
            return []
        
        try:
            # Convert to RGB for face_recognition
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                return []
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            results = []
            
            # Process each face
            for i, (face_encoding, face_location) in enumerate(zip(face_encodings, face_locations)):
                # Extract face image
                top, right, bottom, left = face_location
                face_image = image[top:bottom, left:right]
                
                # Increment detection counter
                self.recognition_stats["total_detections"] += 1
                
                # Initialize result
                result = {
                    "location": face_location,
                    "confidence": 0.0,
                    "recognized": False,
                    "name": "Unknown",
                    "person_id": None
                }
                
                # Detect emotions if available
                if self.has_emotion and self.emotion_detector:
                    try:
                        emotions = self.emotion_detector.detect_emotions(face_image)
                        if emotions and len(emotions) > 0:
                            dominant_emotion = emotions[0]
                            result["emotions"] = dominant_emotion["emotions"]
                            result["dominant_emotion"] = max(
                                dominant_emotion["emotions"].items(),
                                key=lambda x: x[1]
                            )[0]
                    except Exception as e:
                        logger.error(f"Error detecting emotions: {e}")
                
                # Match against known faces
                if self.known_encodings:
                    face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        best_match_distance = face_distances[best_match_index]
                        
                        # Convert distance to confidence (0-1)
                        confidence = 1.0 - min(1.0, best_match_distance)
                        
                        if confidence >= self.min_recognition_confidence:
                            # We have a match
                            person_id = self.known_ids[best_match_index]
                            
                            # Find person info
                            for person in self.known_people:
                                if person.person_id == person_id:
                                    # Update last seen
                                    person.update_seen()
                                    self._save_person(person)
                                    
                                    # Add to result
                                    result["recognized"] = True
                                    result["name"] = person.name
                                    result["person_id"] = person_id
                                    result["confidence"] = confidence
                                    result["relation"] = person.relation
                                    result["recognition_count"] = person.recognition_count
                                    
                                    # Add attributes if available
                                    if person.attributes:
                                        result["attributes"] = person.attributes
                                    
                                    # Increment recognition counter
                                    self.recognition_stats["total_recognitions"] += 1
                                    
                                    break
                        else:
                            # Unknown face
                            self.recognition_stats["unknown_faces"] += 1
                
                # Add to results
                results.append(result)
                
                # Log recognition
                self._add_recognition_log(
                    person_id=result.get("person_id"),
                    confidence=result.get("confidence", 0.0),
                    emotions=result.get("emotions")
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error recognizing faces: {e}")
            return []
    
    def draw_faces(self, image: np.ndarray, faces: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draw face boxes and information on an image.
        
        Args:
            image: Image to draw on
            faces: Face data from recognize_faces
            
        Returns:
            Image with faces drawn
        """
        # Make a copy of the image
        output = image.copy()
        
        # Draw each face
        for face in faces:
            top, right, bottom, left = face["location"]
            
            # Determine color based on recognition status
            if face["recognized"]:
                # Green for recognized faces
                color = (0, 255, 0)
            else:
                # Red for unknown faces
                color = (0, 0, 255)
            
            # Draw face rectangle
            cv2.rectangle(output, (left, top), (right, bottom), color, 2)
            
            # Prepare label text
            if face["recognized"]:
                confidence = face["confidence"] * 100
                label = f"{face['name']} ({confidence:.1f}%)"
            else:
                label = "Unknown"
            
            # Add emotion if available
            if "dominant_emotion" in face:
                label += f" - {face['dominant_emotion']}"
            
            # Draw label background
            cv2.rectangle(output, (left, top - 35), (right, top), color, cv2.FILLED)
            cv2.putText(output, label, (left + 6, top - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return output
    
    def get_person(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a person.
        
        Args:
            person_id: Person ID to get
            
        Returns:
            Person information or None if not found
        """
        try:
            # Find person
            for person in self.known_people:
                if person.person_id == person_id:
                    # Get face images paths
                    face_images = []
                    
                    with self.db_lock:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            "SELECT image_path FROM faces WHERE person_id = ?",
                            (person_id,)
                        )
                        
                        for row in cursor.fetchall():
                            if row[0] and os.path.exists(row[0]):
                                face_images.append(row[0])
                        
                        conn.close()
                    
                    # Get recent recognitions
                    recent_recognitions = []
                    
                    with self.db_lock:
                        conn = sqlite3.connect(self.db_path)
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            """
                            SELECT * FROM recognition_log 
                            WHERE person_id = ? 
                            ORDER BY timestamp DESC 
                            LIMIT 10
                            """,
                            (person_id,)
                        )
                        
                        for row in cursor.fetchall():
                            log_entry = dict(row)
                            
                            # Parse emotions JSON
                            if log_entry.get("emotions"):
                                try:
                                    log_entry["emotions"] = json.loads(log_entry["emotions"])
                                except:
                                    log_entry["emotions"] = None
                            
                            # Add formatted timestamp
                            timestamp = log_entry.get("timestamp", 0)
                            log_entry["timestamp_str"] = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                            
                            recent_recognitions.append(log_entry)
                        
                        conn.close()
                    
                    # Create full person info
                    result = person.to_dict()
                    result["face_images"] = face_images
                    result["recent_recognitions"] = recent_recognitions
                    result["last_seen_str"] = datetime.fromtimestamp(person.last_seen).strftime("%Y-%m-%d %H:%M:%S") if person.last_seen > 0 else "Never"
                    result["first_seen_str"] = datetime.fromtimestamp(person.first_seen).strftime("%Y-%m-%d %H:%M:%S")
                    
                    return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting person: {e}")
            return None
    
    def list_people(self) -> List[Dict[str, Any]]:
        """
        List all known people.
        
        Returns:
            List of people information
        """
        try:
            results = []
            
            for person in self.known_people:
                # Create basic person info
                person_info = {
                    "person_id": person.person_id,
                    "name": person.name,
                    "relation": person.relation,
                    "last_seen": person.last_seen,
                    "last_seen_str": datetime.fromtimestamp(person.last_seen).strftime("%Y-%m-%d %H:%M:%S") if person.last_seen > 0 else "Never",
                    "first_seen": person.first_seen,
                    "first_seen_str": datetime.fromtimestamp(person.first_seen).strftime("%Y-%m-%d %H:%M:%S"),
                    "recognition_count": person.recognition_count
                }
                
                # Get face count
                face_count = 0
                with self.db_lock:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        "SELECT COUNT(*) FROM faces WHERE person_id = ?",
                        (person.person_id,)
                    )
                    
                    face_count = cursor.fetchone()[0]
                    conn.close()
                
                person_info["face_count"] = face_count
                results.append(person_info)
            
            # Sort by name
            results.sort(key=lambda x: x["name"])
            
            return results
            
        except Exception as e:
            logger.error(f"Error listing people: {e}")
            return []
    
    def remove_person(self, person_id: str) -> bool:
        """
        Remove a person from the system.
        
        Args:
            person_id: Person ID to remove
            
        Returns:
            Success status
        """
        try:
            # Find person and remove from memory
            person_index = None
            for i, person in enumerate(self.known_people):
                if person.person_id == person_id:
                    person_index = i
                    break
            
            if person_index is not None:
                # Remove from memory
                self.known_people.pop(person_index)
                
                # Remove associated encodings
                to_remove = []
                for i, pid in enumerate(self.known_ids):
                    if pid == person_id:
                        to_remove.append(i)
                
                # Remove in reverse order
                for i in sorted(to_remove, reverse=True):
                    self.known_encodings.pop(i)
                    self.known_ids.pop(i)
                
                # Save encodings
                self._save_encodings()
                
                # Remove from database
                with self.db_lock:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    # Get face images to delete
                    cursor.execute(
                        "SELECT image_path FROM faces WHERE person_id = ?",
                        (person_id,)
                    )
                    
                    image_paths = [row[0] for row in cursor.fetchall()]
                    
                    # Delete from faces table
                    cursor.execute(
                        "DELETE FROM faces WHERE person_id = ?",
                        (person_id,)
                    )
                    
                    # Delete from recognition log
                    cursor.execute(
                        "DELETE FROM recognition_log WHERE person_id = ?",
                        (person_id,)
                    )
                    
                    # Delete from people table
                    cursor.execute(
                        "DELETE FROM people WHERE person_id = ?",
                        (person_id,)
                    )
                    
                    conn.commit()
                    conn.close()
                
                # Delete face images
                for path in image_paths:
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                        except:
                            pass
                
                logger.info(f"Removed person with ID {person_id}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing person: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get face recognition statistics.
        
        Returns:
            Statistics information
        """
        try:
            # Update stats with current counts
            stats = self.recognition_stats.copy()
            
            # Add people stats
            stats["total_people"] = len(self.known_people)
            stats["total_encodings"] = len(self.known_encodings)
            
            # Get stats from database
            with self.db_lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Count faces
                cursor.execute("SELECT COUNT(*) FROM faces")
                stats["total_face_images"] = cursor.fetchone()[0]
                
                # Count recognition logs
                cursor.execute("SELECT COUNT(*) FROM recognition_log")
                stats["total_recognitions_logged"] = cursor.fetchone()[0]
                
                # Count unknown recognitions
                cursor.execute("SELECT COUNT(*) FROM recognition_log WHERE person_id IS NULL")
                stats["total_unknown_logged"] = cursor.fetchone()[0]
                
                conn.close()
            
            # Add capabilities
            stats["capabilities"] = {
                "face_recognition": self.has_face_recognition,
                "deepface": self.has_deepface,
                "emotion_detection": self.has_emotion
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}