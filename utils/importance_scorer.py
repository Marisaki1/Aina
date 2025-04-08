import re
import string
import time
from typing import Dict, List, Any, Optional, Tuple, Union
import math

# Try to import NLP libraries
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

class ImportanceScorer:
    """
    Evaluates the importance of memories for efficient storage and retrieval.
    Uses linguistic features, emotional content, and heuristics.
    """
    
    def __init__(self, use_nltk: bool = True):
        """
        Initialize importance scorer.
        
        Args:
            use_nltk: Whether to use NLTK for advanced scoring
        """
        self.use_nltk = use_nltk and HAS_NLTK
        self.emotional_words = self._load_emotional_words()
        self.important_phrases = [
            "remember this", "important", "critical", "essential", "remember",
            "don't forget", "never forget", "always", "never", "must", "need to",
            "favorite", "hate", "love", "preference", "always", "every time"
        ]
        
        # Download NLTK resources if needed
        if self.use_nltk:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                self.stop_words = set(stopwords.words('english'))
            except Exception as e:
                print(f"⚠️ Error downloading NLTK resources: {e}")
                self.use_nltk = False
        
        print(f"✅ Importance scorer initialized (NLTK: {'enabled' if self.use_nltk else 'disabled'})")
    
    def _load_emotional_words(self) -> Dict[str, float]:
        """Load emotional words with valence scores."""
        # Basic emotional dictionary (positive values for positive emotions)
        emotional_dict = {
            # Positive emotions (higher values = stronger)
            "joy": 0.8, "happy": 0.7, "wonderful": 0.8, "excellent": 0.9, "amazing": 0.9,
            "great": 0.7, "good": 0.6, "nice": 0.5, "love": 0.9, "like": 0.6,
            "beautiful": 0.7, "fantastic": 0.8, "awesome": 0.9, "best": 0.8,
            
            # Negative emotions (lower values = stronger negative)
            "sad": -0.7, "angry": -0.8, "upset": -0.6, "terrible": -0.9, "horrible": -0.9,
            "worst": -0.8, "bad": -0.6, "awful": -0.8, "hate": -0.9, "dislike": -0.6,
            "annoying": -0.7, "depressing": -0.8, "miserable": -0.9, "disappointed": -0.7
        }
        
        return emotional_dict
    
    def score_text(self, text: str) -> float:
        """
        Calculate importance score for a piece of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Importance score between 0.0 and 1.0
        """
        if not text:
            return 0.0
        
        # Initialize component scores
        length_score = self._score_length(text)
        emotional_score = self._score_emotional_content(text)
        phrase_score = self._score_important_phrases(text)
        content_score = self._score_content_features(text)
        
        # Weighted sum of components (total = 1.0)
        final_score = (
            0.15 * length_score +
            0.30 * emotional_score +
            0.25 * phrase_score +
            0.30 * content_score
        )
        
        # Ensure score is in range [0.0, 1.0]
        return max(0.0, min(1.0, final_score))
    
    def _score_length(self, text: str) -> float:
        """Score based on text length."""
        # Very short or very long texts may be less important
        # Optimal length around 50-200 words
        if self.use_nltk:
            tokens = word_tokenize(text)
            word_count = len([t for t in tokens if t not in string.punctuation])
        else:
            # Simple word count
            word_count = len(text.split())
        
        # Sigmoid function centered around 100 words
        if word_count < 5:
            return 0.3  # Very short texts get low score
        elif word_count < 20:
            return 0.5 + (word_count - 5) * 0.02  # Linear growth to 0.8
        elif word_count < 200:
            return 0.8  # Optimal range
        else:
            return 0.8 - min(0.3, (word_count - 200) * 0.001)  # Very long texts decrease slightly
    
    def _score_emotional_content(self, text: str) -> float:
        """Score based on emotional content."""
        text_lower = text.lower()
        
        # Count emotional words
        emotion_count = 0
        emotion_sum = 0.0
        
        for word, value in self.emotional_words.items():
            if word in text_lower:
                # Count occurrences
                occurrences = len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
                if occurrences > 0:
                    emotion_count += occurrences
                    emotion_sum += abs(value) * occurrences  # Use absolute value for intensity
        
        # Check for exclamation marks and question marks
        exclamations = text.count('!')
        questions = text.count('?')
        
        # Calculate emotion intensity
        if emotion_count == 0:
            emotion_intensity = 0.0
        else:
            emotion_intensity = emotion_sum / emotion_count
        
        # Adjust for punctuation
        punctuation_factor = min(1.0, (exclamations + questions) * 0.1)
        
        # Emotion presence score
        emotion_presence = min(1.0, emotion_count * 0.15)
        
        # Combine factors
        return 0.6 * emotion_presence + 0.3 * emotion_intensity + 0.1 * punctuation_factor
    
    def _score_important_phrases(self, text: str) -> float:
        """Score based on presence of important phrases."""
        text_lower = text.lower()
        
        # Count important phrases
        phrase_count = 0
        for phrase in self.important_phrases:
            if phrase in text_lower:
                occurrences = len(re.findall(r'\b' + re.escape(phrase) + r'\b', text_lower))
                phrase_count += occurrences
        
        # Scale phrase count to score
        return min(1.0, phrase_count * 0.25)
    
    def _score_content_features(self, text: str) -> float:
        """Score based on content features."""
        text_lower = text.lower()
        
        # Check for specific features that indicate importance
        has_numbers = bool(re.search(r'\d', text))
        has_url = bool(re.search(r'https?://\S+', text))
        has_email = bool(re.search(r'\S+@\S+\.\S+', text))
        has_proper_nouns = self._has_proper_nouns(text)
        has_dates = bool(re.search(r'\b(today|tomorrow|yesterday|\d{1,2}/\d{1,2}(/\d{2,4})?|\d{1,2}-\d{1,2}(-\d{2,4})?)\b', text_lower))
        has_times = bool(re.search(r'\b(\d{1,2}:\d{2}|\d{1,2}( )?(am|pm|AM|PM))\b', text))
        
        # Combine features
        feature_score = (
            0.2 * int(has_numbers) +
            0.2 * int(has_url) +
            0.1 * int(has_email) +
            0.2 * int(has_proper_nouns) +
            0.15 * int(has_dates) +
            0.15 * int(has_times)
        )
        
        return feature_score
    
    def _has_proper_nouns(self, text: str) -> bool:
        """Check if text has proper nouns."""
        if not self.use_nltk:
            # Simple heuristic: check for capitalized words not at start of sentence
            words = text.split()
            for i, word in enumerate(words):
                if i > 0 and word and word[0].isupper() and len(word) > 1:
                    prev_word = words[i-1]
                    if not prev_word.endswith(('.', '!', '?', ':')):
                        return True
            return False
        
        try:
            # Use NLTK for proper noun detection
            tokens = word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            for _, tag in pos_tags:
                if tag.startswith('NNP'):  # Proper noun
                    return True
            return False
        except Exception:
            # Fall back to simple heuristic
            return self._has_proper_nouns_simple(text)
    
    def _has_proper_nouns_simple(self, text: str) -> bool:
        """Simple check for proper nouns without NLTK."""
        words = text.split()
        for i, word in enumerate(words):
            if i > 0 and word and word[0].isupper() and len(word) > 1:
                prev_word = words[i-1]
                if not prev_word.endswith(('.', '!', '?', ':')):
                    return True
        return False
    
    def score_with_explanation(self, text: str) -> Dict[str, Any]:
        """
        Calculate importance score with detailed explanation.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with score and explanation
        """
        length_score = self._score_length(text)
        emotional_score = self._score_emotional_content(text)
        phrase_score = self._score_important_phrases(text)
        content_score = self._score_content_features(text)
        
        # Calculate final score
        final_score = (
            0.15 * length_score +
            0.30 * emotional_score +
            0.25 * phrase_score +
            0.30 * content_score
        )
        
        # Ensure score is in range [0.0, 1.0]
        final_score = max(0.0, min(1.0, final_score))
        
        # Generate explanation
        explanation = {
            "length_score": {
                "score": length_score,
                "weight": 0.15,
                "explanation": f"Based on text length of approximately {len(text.split())} words"
            },
            "emotional_score": {
                "score": emotional_score,
                "weight": 0.30,
                "explanation": "Based on emotional intensity and presence of emotional words"
            },
            "phrase_score": {
                "score": phrase_score,
                "weight": 0.25,
                "explanation": "Based on presence of importance indicators like 'remember this', 'important', etc."
            },
            "content_score": {
                "score": content_score,
                "weight": 0.30,
                "explanation": "Based on presence of numbers, URLs, dates, times, and proper nouns"
            }
        }
        
        return {
            "score": final_score,
            "components": explanation
        }
    
    def adjust_for_recency(self, base_score: float, timestamp: float, half_life_days: float = 7.0) -> float:
        """
        Adjust importance score based on recency.
        
        Args:
            base_score: Base importance score
            timestamp: Unix timestamp of the memory
            half_life_days: Half-life in days for decay
            
        Returns:
            Adjusted importance score
        """
        # Convert half-life to seconds
        half_life_seconds = half_life_days * 24 * 3600
        
        # Calculate time difference
        time_diff = time.time() - timestamp
        
        if time_diff <= 0:
            return base_score  # No decay for current or future events
        
        # Calculate decay factor using exponential decay
        decay_factor = math.exp(-math.log(2) * time_diff / half_life_seconds)
        
        # Combine original score with decay
        # This formula ensures recent memories are weighted higher
        # but important memories still remain important even if older
        adjusted_score = 0.4 * base_score + 0.6 * base_score * decay_factor
        
        return max(0.1, min(1.0, adjusted_score))  # Ensure minimum score of 0.1