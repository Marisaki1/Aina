import os
import json
import time
import traceback
from typing import Dict, List, Any, Optional, Union
from llama_cpp import Llama
import torch
from .prompt_templates import get_system_prompt

# Constants
DEFAULT_MODEL_PATH = "models/airoboros-mistral2.2-7b.Q4_K_S.gguf"  # Update this with your actual GGUF filename
CONVERSATION_HISTORY_FILE = "data/conversations.json"
TERMINAL_HISTORY_FILE = "data/terminal_history.json"
HISTORY_LIMIT = 10  # Maximum number of messages to keep in history per user

class LLMManager:
    """
    Core LLM functionality for both Discord bot and terminal interface.
    Manages model loading, inference, and conversation history.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the LLM manager.
        
        Args:
            model_path: Path to the LLM model file
        """
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        
        # Initialize conversation history files if they don't exist
        if not os.path.exists(CONVERSATION_HISTORY_FILE):
            with open(CONVERSATION_HISTORY_FILE, "w") as f:
                json.dump({}, f)
        
        if not os.path.exists(TERMINAL_HISTORY_FILE):
            with open(TERMINAL_HISTORY_FILE, "w") as f:
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
        
        # Initialize memory manager reference (will be set by the agent)
        self.memory_manager = None
    
    def set_memory_manager(self, memory_manager):
        """Set the memory manager instance for memory integration."""
        self.memory_manager = memory_manager
    
    def initialize_model(self):
        """Initialize the model with proper error handling."""
        try:
            print(f"🔄 Loading LLM model from {self.model_path}...")
            start_time = time.time()
            
            # Check for CUDA
            if not torch.cuda.is_available():
                print("⚠️ CUDA not available! Using CPU only mode.")
                gpu_layers = 0
            else:
                gpu_info = torch.cuda.get_device_properties(0)
                print(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
                print(f"   VRAM: {gpu_info.total_memory / (1024**3):.2f} GB")
                # For RTX 4070 Super with 12GB VRAM, use more GPU layers
                gpu_layers = 15  # Increased from 15 to utilize more GPU
            
            # Initialize the model with settings optimized for RTX 4070 Super
            self._model = Llama(
                model_path=self.model_path,
                n_ctx=4096,         # Reduced from 10000 to avoid memory pressure
                n_batch=512,        # Increased from 256 for better throughput
                n_threads=8,        # Increased from 4 for better CPU utilization
                n_gpu_layers=gpu_layers,
                use_mlock=True,     # Added to keep model in memory
                verbose=True        # Added to get more diagnostic information
            )
            
            load_time = time.time() - start_time
            print(f"✅ Model loaded in {load_time:.2f} seconds")
            print(f"🔄 Using {gpu_layers} GPU layers")
            
            # Quick test to verify GPU is working
            test_start = time.time()
            _ = self._model.create_completion("Test", max_tokens=1)
            test_time = time.time() - test_start
            print(f"✅ GPU test completed in {test_time:.2f} seconds")
            
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            traceback.print_exc()  # Add this to see full error trace
            self._model = None
            raise e
    
    @property
    def model(self):
        """Lazy-load the model only when needed."""
        if self._model is None:
            try:
                self.initialize_model()
            except Exception as e:
                print(f"❌ Error in model getter: {e}")
                return None
                
        return self._model
    
    def get_response(self, 
                    user_id: str, 
                    prompt: str, 
                    system_prompt: Optional[str] = None,
                    interface_type: str = "discord",
                    context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response to the user's prompt.
        
        Args:
            user_id: ID of the user
            prompt: User's input text
            system_prompt: System prompt (if None, will use default)
            interface_type: Type of interface ('discord' or 'terminal')
            context: Additional context for response generation
            
        Returns:
            Generated response text
        """
        if not self.model:
            return "I'm sorry, I'm having trouble thinking right now. The LLM model could not be loaded. Please check the logs and try again later."
        
        # Use default system prompt if not provided
        if system_prompt is None:
            system_prompt = get_system_prompt(interface_type)
        
        # Get conversation history
        history = self.get_conversation_history(user_id, interface_type)
        
        # Build full prompt with history and system prompt
        full_prompt = f"{system_prompt}\n\n"
        
        # Add relevant memories if memory manager is available
        if self.memory_manager and prompt:
            # Only retrieve memories for substantial prompts (more than 3 words)
            if len(prompt.split()) > 3:
                memories = self._retrieve_relevant_memories(user_id, prompt)
                if memories:
                    memory_text = self._format_memories(memories)
                    full_prompt += f"Relevant memories:\n{memory_text}\n\n"
        
        # Add conversation history (limit to last 5 exchanges to reduce context size)
        history = history[-10:]  # Last 5 exchanges (10 messages: 5 user, 5 assistant)
        for entry in history:
            if entry["role"] == "user":
                full_prompt += f"User: {entry['content']}\n"
            else:
                full_prompt += f"Aina: {entry['content']}\n"
        
        # Add current prompt
        full_prompt += f"User: {prompt}\nAina:"
        
        try:
            # Check context length and truncate if needed
            while len(full_prompt.split()) > 2000:  # Approximate token count
                # Remove oldest history entry (2 lines)
                lines = full_prompt.split('\n')
                if len(lines) > 4:  # Keep system prompt and current exchange
                    full_prompt = '\n'.join(lines[:2] + lines[4:])
                else:
                    break
            
            # Generate response with optimized parameters
            response = self.model.create_completion(
                full_prompt,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.95,
                top_k=40,           # Added parameter for better sampling
                repeat_penalty=1.1,  # Added parameter to reduce repetition
                stop=["User:", "\n\n"]
            )
            
            # Extract generated text
            generated_text = response["choices"][0]["text"].strip()
            
            # Save to history
            self.add_to_history(user_id, prompt, generated_text, interface_type)
            
            # Store interaction in memory if memory manager is available
            if self.memory_manager:
                self._store_interaction(user_id, prompt, generated_text)
            
            return generated_text
        except Exception as e:
            error_msg = f"❌ Error generating response: {e}"
            print(error_msg)
            traceback.print_exc()  # Add this to see full error trace
            return f"I'm sorry, I encountered an error while processing your request: {str(e)}"
    
    def get_conversation_history(self, user_id: str, interface_type: str = "discord") -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific user.
        
        Args:
            user_id: User ID
            interface_type: Type of interface ('discord' or 'terminal')
            
        Returns:
            List of conversation entries
        """
        user_id = str(user_id)
        history_file = TERMINAL_HISTORY_FILE if interface_type == "terminal" else CONVERSATION_HISTORY_FILE
        
        try:
            with open(history_file, "r") as f:
                conversations = json.load(f)
                return conversations.get(user_id, [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def add_to_history(self, 
                      user_id: str, 
                      user_message: str, 
                      bot_response: str, 
                      interface_type: str = "discord") -> None:
        """
        Add a message exchange to the conversation history.
        
        Args:
            user_id: User ID
            user_message: User's message
            bot_response: Bot's response
            interface_type: Type of interface ('discord' or 'terminal')
        """
        user_id = str(user_id)
        history_file = TERMINAL_HISTORY_FILE if interface_type == "terminal" else CONVERSATION_HISTORY_FILE
        
        try:
            with open(history_file, "r") as f:
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
        with open(history_file, "w") as f:
            json.dump(conversations, f, indent=4)
    
    def clear_history(self, user_id: str, interface_type: str = "discord") -> bool:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User ID
            interface_type: Type of interface ('discord' or 'terminal')
            
        Returns:
            Success status
        """
        user_id = str(user_id)
        history_file = TERMINAL_HISTORY_FILE if interface_type == "terminal" else CONVERSATION_HISTORY_FILE
        
        try:
            with open(history_file, "r") as f:
                conversations = json.load(f)
            
            if user_id in conversations:
                conversations[user_id] = []
                
                with open(history_file, "w") as f:
                    json.dump(conversations, f, indent=4)
                    
                return True
        except (json.JSONDecodeError, FileNotFoundError):
            pass
            
        return False
    
    def _retrieve_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to the current conversation.
        
        Args:
            user_id: User ID
            query: Current user message
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memories
        """
        if not self.memory_manager:
            return []
        
        # Search across all memory types
        memories = self.memory_manager.search_memories(
            query=query,
            memory_types=['core', 'episodic', 'semantic', 'personal'],
            limit=limit,
            user_id=user_id
        )
        
        return memories
    
    def _format_memories(self, memories: List[Dict[str, Any]]) -> str:
        """
        Format memories for inclusion in the prompt.
        
        Args:
            memories: List of memories
            
        Returns:
            Formatted memory text
        """
        if not memories:
            return ""
        
        memory_text = ""
        for i, memory in enumerate(memories, 1):
            memory_type = memory.get("memory_type", "unknown")
            similarity = memory.get("similarity", 0.0)
            memory_text += f"{i}. [{memory_type}] {memory['text']}\n"
        
        return memory_text
    
    def _store_interaction(self, user_id: str, user_message: str, bot_response: str) -> None:
        """
        Store an interaction in episodic memory.
        
        Args:
            user_id: User ID
            user_message: User's message
            bot_response: Bot's response
        """
        if not self.memory_manager:
            return
        
        # Create a summary of the interaction
        interaction_text = f"User asked: '{user_message}' and I responded: '{bot_response[:50]}...'"
        
        # Calculate importance (simple heuristic based on message length)
        importance = min(0.8, 0.4 + (len(user_message) / 1000))
        
        # Store in episodic memory
        self.memory_manager.episodic_memory.log_interaction(
            text=interaction_text,
            user_id=user_id,
            importance=importance,
            context={"message_length": len(user_message)}
        )