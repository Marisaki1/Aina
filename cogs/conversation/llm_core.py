import os
import json
from llama_cpp import Llama 
import time

CONVERSATION_HISTORY_FILE = "data/conversations.json"
DEFAULT_MODEL_PATH = "models/airoboros-mistral2.2-7b.Q4_K_S.gguf"  # Update this with your actual GGUF filename
HISTORY_LIMIT = 10  # Maximum number of messages to keep in history per user

class LLMManager:
    def __init__(self, model_path=None):
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        
        # Initialize conversation history file if it doesn't exist
        if not os.path.exists(CONVERSATION_HISTORY_FILE):
            with open(CONVERSATION_HISTORY_FILE, "w") as f:
                json.dump({}, f)
        
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self._model = None
        
        # Verify model exists
        if not os.path.exists(self.model_path):
            print(f"❌ ERROR: Model file not found at {self.model_path}")
            print("Please ensure your GGUF model is in the models directory")
        else:
            print(f"✅ Model file found: {self.model_path}")
            # Load model immediately to verify it works
            try:
                self.initialize_model()
            except Exception as e:
                print(f"❌ ERROR initializing model: {str(e)}")
    
    def initialize_model(self):
        """Initialize the model with proper error handling"""
        try:
            print(f"🔄 Loading LLM model from {self.model_path}...")
            start_time = time.time()
            
            # Initialize the model with settings optimized for RTX 4070 Super
            self._model = Llama(
                model_path=self.model_path,
                n_ctx=10000,         # Context window size
                n_batch=512,        # Batch size for prompt processing
                n_threads=4,        # CPU threads - matches your 6 cores
                n_gpu_layers=15     # Higher value for RTX 4070 Super
            )
            
            load_time = time.time() - start_time
            print(f"✅ Model loaded in {load_time:.2f} seconds")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self._model = None
            raise e
    
    @property
    def model(self):
        """Lazy-load the model only when needed"""
        if self._model is None:
            try:
                self.initialize_model()
            except Exception as e:
                print(f"❌ Error in model getter: {e}")
                return None
                
        return self._model
    
    def get_response(self, user_id, prompt, system_prompt="You are Aina, a helpful AI assistant."):
        """Generate a response to the user's prompt"""
        if not self.model:
            return "I'm sorry, I'm having trouble thinking right now. The LLM model could not be loaded. Please check the logs and try again later."
        
        # Get conversation history
        history = self.get_conversation_history(user_id)
        
        # Build full prompt with history and system prompt
        full_prompt = f"{system_prompt}\n\n"
        
        # Add conversation history
        for entry in history:
            if entry["role"] == "user":
                full_prompt += f"User: {entry['content']}\n"
            else:
                full_prompt += f"Aina: {entry['content']}\n"
        
        # Add current prompt
        full_prompt += f"User: {prompt}\nAina:"
        
        try:
            # Generate response
            response = self.model.create_completion(
                full_prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.95,
                stop=["User:", "\n\n"]
            )
            
            # Extract generated text
            generated_text = response["choices"][0]["text"].strip()
            
            # Save to history
            self.add_to_history(user_id, prompt, generated_text)
            
            return generated_text
        except Exception as e:
            error_msg = f"❌ Error generating response: {e}"
            print(error_msg)
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
    
    def get_conversation_history(self, user_id):
        """Get conversation history for a specific user"""
        user_id = str(user_id)
        try:
            with open(CONVERSATION_HISTORY_FILE, "r") as f:
                conversations = json.load(f)
                return conversations.get(user_id, [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def add_to_history(self, user_id, user_message, bot_response):
        """Add a message exchange to the conversation history"""
        user_id = str(user_id)
        
        try:
            with open(CONVERSATION_HISTORY_FILE, "r") as f:
                conversations = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            conversations = {}
        
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Add user message
        conversations[user_id].append({
            "role": "user",
            "content": user_message,
            "timestamp": time.time()
        })
        
        # Add bot response
        conversations[user_id].append({
            "role": "assistant",
            "content": bot_response,
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(conversations[user_id]) > HISTORY_LIMIT * 2:  # *2 because each exchange is 2 messages
            conversations[user_id] = conversations[user_id][-HISTORY_LIMIT*2:]
        
        # Save updated conversations
        with open(CONVERSATION_HISTORY_FILE, "w") as f:
            json.dump(conversations, f, indent=4)
    
    def clear_history(self, user_id):
        """Clear conversation history for a user"""
        user_id = str(user_id)
        
        try:
            with open(CONVERSATION_HISTORY_FILE, "r") as f:
                conversations = json.load(f)
            
            if user_id in conversations:
                conversations[user_id] = []
                
                with open(CONVERSATION_HISTORY_FILE, "w") as f:
                    json.dump(conversations, f, indent=4)
                    
                return True
        except (json.JSONDecodeError, FileNotFoundError):
            pass
            
        return False