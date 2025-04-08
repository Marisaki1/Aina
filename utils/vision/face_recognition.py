import os
import time
import cv2
import numpy as np
import json
import pickle
from typing import Dict, List, Any, Optional, Tuple, Union
import threading

# Try to import face recognition library
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False

class FaceRecognizer:
    """
    Face recognition system for identifying users.
    Maintains a database of known faces and provides matching.
    """
    
    def __init__(self, 
                db_path: str = "data/aina/face_recognition",
                min_confidence: float = 0.6):
        """
        Initialize face recognizer.
        
        Args:
            db_path: Path to face database directory
            min_confidence: Minimum confidence for recognition
        """
        self.db_path = db_path
        self.min_confidence = min_confidence
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_user_ids = []
        self.lock = threading.Lock()
        
        # Check if face recognition is available
        self.available = HAS_FACE_RECOGNITION
        
        if not self.available:
            print("⚠️ Face recognition not available: missing dependencies")
            return
        
        # Create database directory if it doesn't exist
        os.makedirs(self.db_path, exist_ok=True)
        
        # Load known faces
        self._load_known_faces()
    
    def _load_known_faces(self) -> None:
        """Load known faces from database."""
        if not self.available:
            return
        
        try:
            db_file = os.path.join(self.db_path, "face_db.pkl")
            
            if os.path.exists(db_file):
                with open(db_file, "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get("encodings", [])
                    self.known_face_names = data.get("names", [])
                    self.known_face_user_ids = data.get("user_ids", [])
                
                print(f"✅ Loaded {len(self.known_face_encodings)} faces from database")
            else:
                print("ℹ️ No face database found, starting with empty database")
        except Exception as e:
            print(f"❌ Error loading face database: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_user_ids = []
    
    def _save_known_faces(self) -> None:
        """Save known faces to database."""
        if not self.available:
            return
        
        try:
            db_file = os.path.join(self.db_path, "face_db.pkl")
            
            data = {
                "encodings": self.known_face_encodings,
                "names": self.known_face_names,
                "user_ids": self.known_face_user_ids,
                "updated": time.time()
            }
            
            with open(db_file, "wb") as f:
                pickle.dump(data, f)
                
            print(f"✅ Saved {len(self.known_face_encodings)} faces to database")
        except Exception as e:
            print(f"❌ Error saving face database: {e}")
    
    def add_face(self, 
                frame: np.ndarray, 
                name: str, 
                user_id: str) -> bool:
        """
        Add a face to the database.
        
        Args:
            frame: Frame containing the face
            name: Name of the person
            user_id: User ID to associate with the face
            
        Returns:
            Success status
        """
        if not self.available:
            print("❌ Face recognition not available")
            return False
        
        with self.lock:
            try:
                # Convert from BGR (OpenCV) to RGB (face_recognition)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Find face locations
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if not face_locations:
                    print("❌ No faces found in the image")
                    return False
                
                # Use the first face found
                face_location = face_locations[0]
                
                # Generate face encoding
                face_encoding = face_recognition.face_encodings(rgb_frame, [face_location])[0]
                
                # Check if this face is already in the database
                if self.known_face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    if True in matches:
                        match_index = matches.index(True)
                        if self.known_face_user_ids[match_index] == user_id:
                            print(f"ℹ️ Face for {name} ({user_id}) already exists, updating")
                            self.known_face_names[match_index] = name
                            self._save_known_faces()
                            return True
                
                # Add face to database
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                self.known_face_user_ids.append(user_id)
                
                # Save updated database
                self._save_known_faces()
                
                # Save face image for reference
                face_dir = os.path.join(self.db_path, "faces")
                os.makedirs(face_dir, exist_ok=True)
                
                # Extract face from frame
                top, right, bottom, left = face_location
                face_image = frame[top:bottom, left:right]
                
                # Save face image
                face_file = os.path.join(face_dir, f"{user_id}.jpg")
                cv2.imwrite(face_file, face_image)
                
                print(f"✅ Added face for {name} ({user_id})")
                return True
                
            except Exception as e:
                print(f"❌ Error adding face: {e}")
                return False
    
    def remove_face(self, user_id: str) -> bool:
        """
        Remove a face from the database.
        
        Args:
            user_id: User ID to remove
            
        Returns:
            Success status
        """
        if not self.available:
            print("❌ Face recognition not available")
            return False
        
        with self.lock:
            try:
                # Find all instances of the user_id
                indices = [i for i, uid in enumerate(self.known_face_user_ids) if uid == user_id]
                
                if not indices:
                    print(f"❌ No faces found for user {user_id}")
                    return False
                
                # Remove faces in reverse order
                for index in sorted(indices, reverse=True):
                    del self.known_face_encodings[index]
                    del self.known_face_names[index]
                    del self.known_face_user_ids[index]
                
                # Save updated database
                self._save_known_faces()
                
                # Remove face image if it exists
                face_file = os.path.join(self.db_path, "faces", f"{user_id}.jpg")
                if os.path.exists(face_file):
                    os.remove(face_file)
                
                print(f"✅ Removed {len(indices)} faces for user {user_id}")
                return True
                
            except Exception as e:
                print(f"❌ Error removing face: {e}")
                return False
    
    def recognize_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Recognize faces in a frame.
        
        Args:
            frame: Frame to analyze
            
        Returns:
            List of recognized faces with name, user_id, confidence, and location
        """
        if not self.available:
            print("❌ Face recognition not available")
            return []
        
        if not self.known_face_encodings:
            return []
        
        with self.lock:
            try:
                # Convert from BGR (OpenCV) to RGB (face_recognition)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Find face locations
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if not face_locations:
                    return []
                
                # Generate face encodings
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                results = []
                
                # Compare each face against known faces
                for i, face_encoding in enumerate(face_encodings):
                    name = "Unknown"
                    user_id = None
                    confidence = 0.0
                    
                    # Calculate face distance (lower is better)
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        best_match_distance = face_distances[best_match_index]
                        
                        # Convert distance to confidence (0-1)
                        confidence = 1.0 - min(1.0, best_match_distance)
                        
                        if confidence >= self.min_confidence:
                            name = self.known_face_names[best_match_index]
                            user_id = self.known_face_user_ids[best_match_index]
                    
                    top, right, bottom, left = face_locations[i]
                    
                    results.append({
                        "name": name,
                        "user_id": user_id,
                        "confidence": confidence,
                        "location": (top, right, bottom, left)
                    })
                
                return results
                
            except Exception as e:
                print(f"❌ Error recognizing faces: {e}")
                return []
    
    def draw_faces(self, frame: np.ndarray, faces: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draw face boxes and names on a frame.
        
        Args:
            frame: Frame to draw on
            faces: List of face data from recognize_faces
            
        Returns:
            Frame with faces drawn
        """
        if not self.available or not faces:
            return frame
        
        # Create a copy of the frame
        result = frame.copy()
        
        for face in faces:
            top, right, bottom, left = face["location"]
            name = face["name"]
            confidence = face["confidence"]
            
            # Draw a box around the face
            cv2.rectangle(result, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # Draw label below the face
            label = f"{name} ({confidence:.2f})"
            cv2.rectangle(result, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(result, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the face database.
        
        Returns:
            Face database statistics
        """
        if not self.available:
            return {"available": False}
        
        # Count unique users
        unique_users = len(set(self.known_face_user_ids))
        
        return {
            "available": True,
            "total_faces": len(self.known_face_encodings),
            "unique_users": unique_users,
            "min_confidence": self.min_confidence
        }