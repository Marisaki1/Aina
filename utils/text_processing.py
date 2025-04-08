import re
import string
import unicodedata
from typing import Dict, List, Any, Optional, Tuple, Union, Set

# Try to import NLP libraries
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import WordNetLemmatizer
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

class TextProcessor:
    """
    Text processing utilities for cleaning, normalization, and analysis.
    Supports memory system with enhanced text processing capabilities.
    """
    
    def __init__(self, use_nltk: bool = True):
        """
        Initialize text processor.
        
        Args:
            use_nltk: Whether to use NLTK for advanced processing
        """
        self.use_nltk = use_nltk and HAS_NLTK
        
        # Download NLTK resources if needed
        if self.use_nltk:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
                self.stop_words = set(stopwords.words('english'))
                self.lemmatizer = WordNetLemmatizer()
            except Exception as e:
                print(f"⚠️ Error downloading NLTK resources: {e}")
                self.use_nltk = False
        
        print(f"✅ Text processor initialized (NLTK: {'enabled' if self.use_nltk else 'disabled'})")
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace, normalizing, etc.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def normalize_text(self, text: str, remove_stopwords: bool = False) -> str:
        """
        Normalize text for search and comparison.
        
        Args:
            text: Input text
            remove_stopwords: Whether to remove stop words
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        if self.use_nltk:
            # Tokenize
            tokens = word_tokenize(text)
            
            # Remove punctuation
            tokens = [token for token in tokens if token not in string.punctuation]
            
            # Remove stop words if requested
            if remove_stopwords:
                tokens = [token for token in tokens if token not in self.stop_words]
            
            # Lemmatize
            tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
            
            # Rejoin tokens
            return ' '.join(tokens)
        else:
            # Simple normalization for non-NLTK case
            # Remove punctuation
            translator = str.maketrans('', '', string.punctuation)
            text = text.translate(translator)
            
            return text
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        if not text:
            return []
        
        if self.use_nltk:
            # Tokenize and remove punctuation
            tokens = word_tokenize(text.lower())
            tokens = [token for token in tokens if token not in string.punctuation]
            
            # Remove stop words
            tokens = [token for token in tokens if token not in self.stop_words]
            
            # Count token frequency
            freq_dist = nltk.FreqDist(tokens)
            
            # Get most common tokens
            keywords = [word for word, freq in freq_dist.most_common(max_keywords)]
            
            return keywords
        else:
            # Simple keyword extraction for non-NLTK case
            # Remove punctuation
            translator = str.maketrans('', '', string.punctuation)
            text = text.lower().translate(translator)
            
            # Split into words
            words = text.split()
            
            # Simple stop words list
            simple_stops = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'of', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'can', 'could', 'may', 'might', 'must', 'that', 'this', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'}
            
            # Remove stop words
            words = [word for word in words if word not in simple_stops]
            
            # Count word frequency
            word_freq = {}
            for word in words:
                if word in word_freq:
                    word_freq[word] += 1
                else:
                    word_freq[word] = 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Get top words
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of entity types and values
        """
        if not text or not self.use_nltk:
            return {}
        
        try:
            # Download NER resources if needed
            try:
                nltk.download('maxent_ne_chunker', quiet=True)
                nltk.download('words', quiet=True)
            except Exception:
                return {}
            
            # Tokenize and tag parts of speech
            tokens = word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            
            # Extract named entities
            ne_tree = nltk.ne_chunk(pos_tags)
            
            # Process named entities
            entities = {
                'PERSON': [],
                'ORGANIZATION': [],
                'LOCATION': [],
                'DATE': [],
                'TIME': [],
                'MONEY': [],
                'OTHER': []
            }
            
            for subtree in ne_tree:
                if isinstance(subtree, nltk.Tree):
                    entity_type = subtree.label()
                    entity_text = ' '.join([word for word, tag in subtree.leaves()])
                    
                    if entity_type in entities:
                        entities[entity_type].append(entity_text)
                    else:
                        entities['OTHER'].append(entity_text)
            
            # Remove empty entity types
            return {k: v for k, v in entities.items() if v}
        except Exception as e:
            print(f"⚠️ Error extracting entities: {e}")
            return {}
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        if self.use_nltk:
            return sent_tokenize(text)
        else:
            # Simple sentence splitting for non-NLTK case
            # Split on sentence-ending punctuation followed by space or end of string
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using Jaccard similarity.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize text
        norm_text1 = self.normalize_text(text1, remove_stopwords=True)
        norm_text2 = self.normalize_text(text2, remove_stopwords=True)
        
        # Split into words
        words1 = set(norm_text1.split())
        words2 = set(norm_text2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """
        Generate a simple extractive summary of text.
        
        Args:
            text: Input text
            max_sentences: Maximum number of sentences in summary
            
        Returns:
            Summarized text
        """
        if not text:
            return ""
        
        # Split into sentences
        sentences = self.split_into_sentences(text)
        
        if len(sentences) <= max_sentences:
            return text
        
        if self.use_nltk:
            # Score sentences based on keyword frequency
            keywords = self.extract_keywords(text, max_keywords=20)
            keyword_set = set(keywords)
            
            # Score each sentence
            sentence_scores = []
            for sentence in sentences:
                # Normalize sentence
                norm_sentence = self.normalize_text(sentence, remove_stopwords=True)
                words = set(norm_sentence.split())
                
                # Score based on keyword presence
                keyword_count = len(words.intersection(keyword_set))
                score = keyword_count / max(1, len(words))
                
                # Adjust score for sentence position (first and last sentences are important)
                position_factor = 1.0
                if sentences.index(sentence) == 0:
                    position_factor = 1.5
                elif sentences.index(sentence) == len(sentences) - 1:
                    position_factor = 1.2
                
                sentence_scores.append((sentence, score * position_factor))
            
            # Sort by score
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Get top sentences
            top_sentences = [s[0] for s in sentence_scores[:max_sentences]]
            
            # Sort back to original order
            ordered_sentences = [s for s in sentences if s in top_sentences]
            
            return ' '.join(ordered_sentences)
        else:
            # Simple summary for non-NLTK case: first sentence + middle + last
            if len(sentences) <= 3:
                return text
            
            # Always include first and last sentences
            summary_sentences = [sentences[0]]
            
            # Add one from the middle
            middle_idx = len(sentences) // 2
            summary_sentences.append(sentences[middle_idx])
            
            # Add last sentence
            summary_sentences.append(sentences[-1])
            
            return ' '.join(summary_sentences)
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of a text.
        
        Args:
            text: Input text
            
        Returns:
            ISO 639-1 language code or 'unknown'
        """
        if not text:
            return 'unknown'
        
        try:
            # Try to use langdetect if available
            try:
                from langdetect import detect
                return detect(text)
            except ImportError:
                pass
            
            # Fallback to simple heuristics
            # Check for common English words
            english_common = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it'}
            words = set(text.lower().split())
            english_count = len(words.intersection(english_common))
            
            if english_count >= 2:
                return 'en'
            
            # Check for Spanish
            spanish_common = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se'}
            spanish_count = len(words.intersection(spanish_common))
            
            if spanish_count >= 2:
                return 'es'
            
            # Check for French
            french_common = {'le', 'la', 'de', 'et', 'est', 'en', 'un', 'une', 'du', 'que'}
            french_count = len(words.intersection(french_common))
            
            if french_count >= 2:
                return 'fr'
            
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def extract_dates_and_times(self, text: str) -> List[str]:
        """
        Extract dates and times from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted date/time strings
        """
        if not text:
            return []
        
        # Regular expressions for dates and times
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',                   # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',                   # MM-DD-YYYY or DD-MM-YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',                     # YYYY-MM-DD
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}(st|nd|rd|th)?, \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}(st|nd|rd|th)? of (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*, \d{4}\b',  # DDth of Month, YYYY
            r'\b(yesterday|today|tomorrow)\b',                # Relative dates
            r'\b(next|last) (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',  # Relative weekdays
            r'\b(next|last) week\b',                          # Relative weeks
            r'\b(next|last) month\b',                         # Relative months
            r'\b(next|last) year\b'                           # Relative years
        ]
        
        time_patterns = [
            r'\b\d{1,2}:\d{2}\b',                            # HH:MM
            r'\b\d{1,2}:\d{2}:\d{2}\b',                      # HH:MM:SS
            r'\b\d{1,2}(am|pm|AM|PM)\b',                     # HHam/pm
            r'\b\d{1,2} (am|pm|AM|PM)\b',                    # HH am/pm
            r'\b(noon|midnight)\b',                          # Noon/midnight
            r'\b\d{1,2} o\'clock\b'                          # HH o'clock
        ]
        
        # Combine all patterns
        all_patterns = date_patterns + time_patterns
        
        # Extract matches
        results = []
        for pattern in all_patterns:
            matches = re.findall(pattern, text)
            if isinstance(matches, list):
                for match in matches:
                    if isinstance(match, tuple):
                        # Some regex groups return tuples, convert to string
                        match_str = ' '.join([m for m in match if m])
                    else:
                        match_str = match
                    
                    if match_str and match_str not in results:
                        results.append(match_str)
        
        return results