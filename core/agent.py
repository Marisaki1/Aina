import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Union

from .memory import MemoryManager
from .llm import LLMManager

# Set up logger
logger = logging.getLogger("aina.agent")

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
        logger.info("Initializing Aina agent...")
        self.start_time = time.time()
        
        # Create necessary directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/aina", exist_ok=True)
        
        # Initialize memory system
        logger.info("Initializing memory system...")
        self.memory_manager = MemoryManager(config_path)
        
        # Initialize LLM
        logger.info("Initializing language model...")
        self.llm_manager = LLMManager()
        
        # Connect systems
        self.llm_manager.set_memory_manager(self.memory_manager)
        
        # Connect reflection system with LLM for enhanced reflections
        self.memory_manager.reflection.set_llm_manager(self.llm_manager)
        
        # Store agent status
        self.status = "ready"
        self.last_activity = time.time()
        
        # Initialize active user sessions
        self.active_users = {}
        
        # Store daily reflection time
        self.last_reflection = time.time()
        self.last_consolidation = time.time()
        
        # Initialize utilities
        self._init_utilities()
        
        # Log initialization
        total_init_time = time.time() - self.start_time
        logger.info(f"Agent initialized in {total_init_time:.2f} seconds")
        
        # Store initialization in episodic memory
        self.memory_manager.episodic_memory.log_event(
            text=f"Aina agent initialized in {total_init_time:.2f} seconds",
            event_type="system",
            importance=0.7
        )
    
    def _init_utilities(self):
        """Initialize utility modules."""
        # These will be lazy-loaded when needed
        self._memory_dashboard = None
        self._memory_backup = None
        self._memory_consolidator = None
        
        # Background tasks
        self.background_tasks = {}
        self.background_running = False
    
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
        
        # Check if we should perform routine maintenance
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
                logger.info("Performing daily memory reflection...")
                self.memory_manager.trigger_reflection("daily")
                self.last_reflection = current_time
                logger.info("Daily reflection complete")
            except Exception as e:
                logger.error(f"Error in daily reflection: {e}")
        
        # Check if memory consolidation is due (7 days since last)
        if current_time - self.last_consolidation > 7 * 24 * 3600:
            try:
                # Perform consolidation in background
                if not self.is_task_running("consolidation"):
                    self.start_background_task("consolidation", self._perform_consolidation)
            except Exception as e:
                logger.error(f"Error starting consolidation: {e}")
    
    def _perform_consolidation(self):
        """Perform memory consolidation."""
        logger.info("Starting memory consolidation...")
        try:
            # Initialize consolidator if needed
            if not hasattr(self, "memory_consolidator") or not self.memory_consolidator:
                from utils.memory_consolidator import MemoryConsolidator
                self.memory_consolidator = MemoryConsolidator(
                    self.memory_manager, 
                    self.memory_manager.embedding_provider
                )
            
            # Consolidate episodic memories
            episodic_result = self.memory_consolidator.consolidate_episodic_memories(days=7)
            logger.info(f"Episodic memory consolidation: {episodic_result.get('message', 'completed')}")
            
            # Consolidate personal memories
            personal_result = self.memory_consolidator.consolidate_personal_memories()
            logger.info(f"Personal memory consolidation: {personal_result.get('message', 'completed')}")
            
            # Extract concepts
            concept_result = self.memory_consolidator.extract_concepts()
            logger.info(f"Concept extraction: {concept_result.get('message', 'completed')}")
            
            # Update last consolidation time
            self.last_consolidation = time.time()
            
            # Record in episodic memory
            self.memory_manager.episodic_memory.log_event(
                text="Performed memory consolidation and concept extraction",
                event_type="system",
                importance=0.7
            )
            
            logger.info("Memory consolidation complete")
            
        except Exception as e:
            logger.error(f"Error in memory consolidation: {e}")
    
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
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            user_info["memory_profile"] = None
        
        return user_info
    
    def analyze_user(self, user_id: str) -> Dict[str, Any]:
        """
        Perform in-depth analysis of a user.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            Analysis results
        """
        return self.memory_manager.reflection.analyze_user(user_id)
    
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
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            memory_stats = {"error": "Could not retrieve memory stats"}
        
        # Get background tasks
        tasks = {}
        for task_name, task_info in self.background_tasks.items():
            tasks[task_name] = {
                "running": task_info["thread"].is_alive() if task_info.get("thread") else False,
                "start_time": task_info.get("start_time", 0),
                "elapsed": time.time() - task_info.get("start_time", time.time()) if task_info.get("start_time") else 0
            }
        
        return {
            "status": self.status,
            "uptime": f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
            "uptime_seconds": uptime,
            "active_users": len(self.active_users),
            "last_activity": time.time() - self.last_activity,
            "memory_stats": memory_stats,
            "last_reflection": time.time() - self.last_reflection,
            "last_consolidation": time.time() - self.last_consolidation,
            "background_tasks": tasks
        }
    
    def start_background_task(self, task_name: str, task_func: Callable, *args, **kwargs) -> bool:
        """
        Start a background task.
        
        Args:
            task_name: Name of the task
            task_func: Function to run
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Success status
        """
        if task_name in self.background_tasks and self.background_tasks[task_name].get("thread") and self.background_tasks[task_name]["thread"].is_alive():
            logger.warning(f"Task {task_name} is already running")
            return False
        
        # Create and start thread
        thread = threading.Thread(
            target=self._run_background_task,
            args=(task_name, task_func) + args,
            kwargs=kwargs,
            daemon=True
        )
        
        # Store task info
        self.background_tasks[task_name] = {
            "thread": thread,
            "start_time": time.time()
        }
        
        # Start thread
        thread.start()
        logger.info(f"Started background task: {task_name}")
        
        return True
    
    def _run_background_task(self, task_name: str, task_func: Callable, *args, **kwargs):
        """Run a background task and handle cleanup."""
        try:
            # Run the task
            task_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in background task {task_name}: {e}")
        finally:
            # Mark task as completed
            if task_name in self.background_tasks:
                self.background_tasks[task_name]["end_time"] = time.time()
    
    def is_task_running(self, task_name: str) -> bool:
        """
        Check if a background task is running.
        
        Args:
            task_name: Name of the task
            
        Returns:
            True if task is running, False otherwise
        """
        return (task_name in self.background_tasks and 
                self.background_tasks[task_name].get("thread") and 
                self.background_tasks[task_name]["thread"].is_alive())
    
    def backup_memory(self, description: str = "", compress: bool = True) -> Dict[str, Any]:
        """
        Backup all memories.
        
        Args:
            description: Optional description of the backup
            compress: Whether to compress the backup
            
        Returns:
            Backup result
        """
        try:
            # Load backup manager if needed
            if not hasattr(self, "_memory_backup") or not self._memory_backup:
                from utils.memory_backup import MemoryBackupManager
                self._memory_backup = MemoryBackupManager(self.memory_manager)
            
            # Create backup
            result = self._memory_backup.create_backup(
                backup_type="manual",
                description=description,
                compress=compress
            )
            
            return result
        except Exception as e:
            logger.error(f"Error backing up memories: {e}")
            return {
                "status": "error",
                "message": f"Backup failed: {str(e)}"
            }
    
    def restore_backup(self, backup_id: Union[int, str]) -> Dict[str, Any]:
        """
        Restore from a backup.
        
        Args:
            backup_id: ID or filename of the backup to restore
            
        Returns:
            Restoration result
        """
        try:
            # Load backup manager if needed
            if not hasattr(self, "_memory_backup") or not self._memory_backup:
                from utils.memory_backup import MemoryBackupManager
                self._memory_backup = MemoryBackupManager(self.memory_manager)
            
            # Restore backup
            result = self._memory_backup.restore_backup(backup_id)
            
            return result
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return {
                "status": "error",
                "message": f"Restore failed: {str(e)}"
            }
    
    def list_backups(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            List of backup information
        """
        try:
            # Load backup manager if needed
            if not hasattr(self, "_memory_backup") or not self._memory_backup:
                from utils.memory_backup import MemoryBackupManager
                self._memory_backup = MemoryBackupManager(self.memory_manager)
            
            # List backups
            return self._memory_backup.list_backups(limit=limit)
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def start_scheduled_backups(self, interval_hours: int = 24) -> Dict[str, Any]:
        """
        Start scheduled backups.
        
        Args:
            interval_hours: Interval between backups in hours
            
        Returns:
            Status information
        """
        try:
            # Load backup manager if needed
            if not hasattr(self, "_memory_backup") or not self._memory_backup:
                from utils.memory_backup import MemoryBackupManager
                self._memory_backup = MemoryBackupManager(self.memory_manager)
            
            # Start scheduled backups
            return self._memory_backup.start_scheduled_backup(
                interval_hours=interval_hours,
                backup_type="scheduled"
            )
        except Exception as e:
            logger.error(f"Error starting scheduled backups: {e}")
            return {
                "status": "error",
                "message": f"Failed to start scheduled backups: {str(e)}"
            }
    
    def start_memory_dashboard(self, port: int = 5000) -> Dict[str, Any]:
        """
        Start the memory dashboard web interface.
        
        Args:
            port: Port to run the dashboard on
            
        Returns:
            Status information
        """
        try:
            # Initialize dashboard if needed
            if not hasattr(self, "_memory_dashboard") or not self._memory_dashboard:
                from utils.dashboard.memory_dashboard import MemoryDashboard
                self._memory_dashboard = MemoryDashboard(
                    memory_manager=self.memory_manager,
                    port=port
                )
            
            # Start dashboard
            self._memory_dashboard.start(open_browser=False)
            
            return {
                "status": "success",
                "message": f"Memory dashboard started on port {port}",
                "url": f"http://localhost:{port}"
            }
        except Exception as e:
            logger.error(f"Error starting memory dashboard: {e}")
            return {
                "status": "error",
                "message": f"Failed to start memory dashboard: {str(e)}"
            }
    
    def consolidate_memories(self) -> Dict[str, Any]:
        """
        Manually trigger memory consolidation.
        
        Returns:
            Status information
        """
        try:
            # Start consolidation in background
            if self.is_task_running("consolidation"):
                return {
                    "status": "warning",
                    "message": "Memory consolidation is already running"
                }
            
            success = self.start_background_task("consolidation", self._perform_consolidation)
            
            if success:
                return {
                    "status": "success",
                    "message": "Memory consolidation started in background"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to start memory consolidation"
                }
        except Exception as e:
            logger.error(f"Error starting memory consolidation: {e}")
            return {
                "status": "error",
                "message": f"Failed to start memory consolidation: {str(e)}"
            }
    
    def shutdown(self) -> bool:
        """
        Perform clean shutdown.
        
        Returns:
            Success status
        """
        try:
            logger.info("Shutting down agent...")
            
            # Stop background tasks
            self.background_running = False
            
            # Backup memories
            backup_result = self.backup_memory(description="Shutdown backup")
            logger.info(f"Shutdown backup: {backup_result.get('message', 'completed')}")
            
            # Stop dashboard if running
            if hasattr(self, "_memory_dashboard") and self._memory_dashboard:
                try:
                    self._memory_dashboard.stop()
                    logger.info("Memory dashboard stopped")
                except Exception as e:
                    logger.error(f"Error stopping memory dashboard: {e}")
            
            # Stop scheduled backups if running
            if hasattr(self, "_memory_backup") and self._memory_backup:
                try:
                    self._memory_backup.stop_scheduled_backup()
                    logger.info("Scheduled backups stopped")
                except Exception as e:
                    logger.error(f"Error stopping scheduled backups: {e}")
            
            # Log shutdown
            self.memory_manager.episodic_memory.log_event(
                text="Aina agent shutting down cleanly",
                event_type="system",
                importance=0.7
            )
            
            # Update status
            self.status = "shutdown"
            logger.info("Agent shutdown complete")
            
            return True
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            return False