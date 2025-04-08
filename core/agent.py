import os
import time
from typing import Dict, List, Any, Optional, Callable

from .memory import MemoryManager
from .llm import LLMManager

class Agent:
    """
    Core agent functionality, shared between Discord and terminal interfaces.
    Manages the AI's "mind" - LLM, memory, and other cognitive processes.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            config_path: Path to configuration file
        """
        print("🤖 Initializing Aina agent...")
        self.start_time = time.time()
        
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/aina", exist_ok=True)
        
        # Initialize memory system
        print("🧠 Initializing memory system...")
        self.memory_manager = MemoryManager(config_path)
        
        # Initialize LLM
        print("💭 Initializing language model...")
        self.llm_manager = LLMManager()
        
        # Connect systems
        self.llm_manager.set_memory_manager(self.memory_manager)
        
        # Store agent status
        self.status = "ready"
        self.last_activity = time.time()
        
        # Initialize active user sessions
        self.active_users = {}
        
        # Store daily reflection time
        self.last_reflection = time.time()
        
        # Log initialization
        total_init_time = time.time() - self.start_time
        print(f"✅ Agent initialized in {total_init_time:.2f} seconds")
        
        # Store initialization in episodic memory
        self.memory_manager.episodic_memory.log_event(
            text=f"Aina agent initialized in {total_init_time:.2f} seconds",
            event_type="system",
            importance=0.7
        )
    
    def process_message(self, 
                       user_id: str, 
                       message: str, 
                       interface_type: str = "discord",
                       context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            user_id: User ID
            message: User's message text
            interface_type: Interface type ('discord' or 'terminal')
            context: Additional context for the message
            
        Returns:
            Response text
        """
        # Update last activity
        self.last_activity = time.time()
        
        # Add user to active users if not already there
        if user_id not in self.active_users:
            self.active_users[user_id] = {
                "first_interaction": time.time(),
                "last_interaction": time.time(),
                "interaction_count": 0
            }
        
        # Update user activity
        self.active_users[user_id]["last_interaction"] = time.time()
        self.active_users[user_id]["interaction_count"] += 1
        
        # Check if we should perform routine memory maintenance
        self._check_routine_maintenance()
        
        # Process the message through the LLM
        response = self.llm_manager.get_response(
            user_id=user_id,
            prompt=message,
            interface_type=interface_type,
            context=context
        )
        
        return response
    
    def _check_routine_maintenance(self):
        """Check if routine maintenance tasks should be performed"""
        current_time = time.time()
        
        # Check if daily reflection is due (24 hours since last)
        if current_time - self.last_reflection > 24 * 3600:
            try:
                print("🔄 Performing daily memory reflection...")
                self.memory_manager.trigger_reflection("daily")
                self.last_reflection = current_time
                print("✅ Daily reflection complete")
            except Exception as e:
                print(f"❌ Error in daily reflection: {e}")
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get information about a user.
        
        Args:
            user_id: User ID
            
        Returns:
            User information
        """
        user_info = {}
        
        # Get activity stats if available
        if user_id in self.active_users:
            user_info["activity"] = self.active_users[user_id]
        
        # Get memories about the user if available
        try:
            user_profile = self.memory_manager.personal_memory.get_user_profile(user_id)
            user_info["memory_profile"] = user_profile
        except Exception:
            user_info["memory_profile"] = None
        
        return user_info
    
    def store_user_information(self, 
                              user_id: str,
                              info_text: str,
                              info_type: str = "general",
                              importance: float = 0.6) -> str:
        """
        Store information about a user.
        
        Args:
            user_id: User ID
            info_text: Information text
            info_type: Type of information
            importance: Importance score (0-1)
            
        Returns:
            Memory ID
        """
        return self.memory_manager.personal_memory.store_user_info(
            user_id=user_id,
            text=info_text,
            info_type=info_type,
            importance=importance
        )
    
    def search_memory(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search agent's memory.
        
        Args:
            query: Search query
            user_id: User ID for filtering personal memories
            
        Returns:
            List of matching memories
        """
        return self.memory_manager.search_memories(
            query=query,
            user_id=user_id
        )
    
    def create_reflection(self, reflection_type: str = "daily") -> Dict[str, Any]:
        """
        Create a reflection on recent memories.
        
        Args:
            reflection_type: Type of reflection ('daily' or 'weekly')
            
        Returns:
            Reflection data
        """
        return self.memory_manager.trigger_reflection(reflection_type)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Status information
        """
        uptime = time.time() - self.start_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Get memory stats
        try:
            memory_stats = {
                "core": self.memory_manager.storage.count("core"),
                "episodic": self.memory_manager.storage.count("episodic"),
                "semantic": self.memory_manager.storage.count("semantic"),
                "personal": self.memory_manager.storage.count("personal")
            }
        except Exception:
            memory_stats = {"error": "Could not retrieve memory stats"}
        
        return {
            "status": self.status,
            "uptime": f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
            "uptime_seconds": uptime,
            "active_users": len(self.active_users),
            "last_activity": time.time() - self.last_activity,
            "memory_stats": memory_stats,
            "last_reflection": time.time() - self.last_reflection
        }
    
    def backup_memory(self) -> bool:
        """
        Backup all memories.
        
        Returns:
            Success status
        """
        try:
            return self.memory_manager.backup_memories()
        except Exception as e:
            print(f"❌ Error backing up memories: {e}")
            return False
    
    def shutdown(self) -> bool:
        """
        Perform clean shutdown.
        
        Returns:
            Success status
        """
        try:
            # Backup memories
            self.backup_memory()
            
            # Log shutdown
            self.memory_manager.episodic_memory.log_event(
                text="Aina agent shutting down cleanly",
                event_type="system",
                importance=0.7
            )
            
            # Update status
            self.status = "shutdown"
            
            return True
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
            return False