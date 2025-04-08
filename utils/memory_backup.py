import os
import time
import json
import shutil
import zipfile
import datetime
import sqlite3
import threading
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Set up logger
logger = logging.getLogger("aina.backup")
logger.setLevel(logging.INFO)

class MemoryBackupManager:
    """
    Manages backup and restoration of memory systems.
    Provides scheduled backups, compression, and versioning.
    """
    
    def __init__(self, memory_manager, backup_dir: str = "data/aina/backups"):
        """
        Initialize backup manager.
        
        Args:
            memory_manager: MemoryManager instance
            backup_dir: Directory for storing backups
        """
        self.memory_manager = memory_manager
        self.backup_dir = backup_dir
        self.backup_metadata_db = os.path.join(backup_dir, "backup_metadata.db")
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Backup schedule settings
        self.scheduled_backup_active = False
        self.scheduled_backup_thread = None
        self.backup_interval_hours = 24  # Default: daily backup
        
        # Default retention policy
        self.retention_policy = {
            "daily": 7,    # Keep daily backups for 7 days
            "weekly": 4,   # Keep weekly backups for 4 weeks
            "monthly": 6,  # Keep monthly backups for 6 months
            "yearly": 2    # Keep yearly backups for 2 years
        }
        
        logger.info(f"Backup manager initialized with backup directory: {backup_dir}")
    
    def _init_database(self):
        """Initialize SQLite database for backup metadata."""
        try:
            conn = sqlite3.connect(self.backup_metadata_db)
            cursor = conn.cursor()
            
            # Create table for backup metadata
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                filename TEXT NOT NULL,
                backup_type TEXT NOT NULL,
                size INTEGER NOT NULL,
                memory_counts TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                retention_days INTEGER DEFAULT 30
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Backup metadata database initialized")
        except Exception as e:
            logger.error(f"Error initializing backup database: {e}")
    
    def create_backup(self, 
                    backup_type: str = "manual", 
                    description: str = "", 
                    compress: bool = True) -> Dict[str, Any]:
        """
        Create a backup of all memory systems.
        
        Args:
            backup_type: Type of backup ('manual', 'daily', 'weekly', 'monthly', 'yearly')
            description: Optional description of the backup
            compress: Whether to compress the backup
            
        Returns:
            Backup result information
        """
        logger.info(f"Starting {backup_type} backup...")
        start_time = time.time()
        
        # Create timestamp-based directory name
        timestamp = int(time.time())
        date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"{backup_type}_{date_str}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup each memory type
            memory_counts = {}
            for memory_type in ['core', 'episodic', 'semantic', 'personal']:
                # Create type directory
                type_dir = os.path.join(backup_path, memory_type)
                os.makedirs(type_dir, exist_ok=True)
                
                # Backup memory collection
                success = self.memory_manager.storage.backup(memory_type, type_dir)
                
                if success:
                    # Count memories
                    count = self.memory_manager.storage.count(memory_type)
                    memory_counts[memory_type] = count
                    logger.info(f"  ✓ Backed up {count} {memory_type} memories")
                else:
                    logger.warning(f"  ✗ Failed to backup {memory_type} memories")
            
            # Backup reflection files
            reflection_dir = os.path.join(backup_path, "reflections")
            os.makedirs(reflection_dir, exist_ok=True)
            
            # Copy daily reflections
            daily_src = "data/aina/reflections/daily"
            daily_dst = os.path.join(reflection_dir, "daily")
            if os.path.exists(daily_src):
                shutil.copytree(daily_src, daily_dst)
                logger.info("  ✓ Backed up daily reflections")
            
            # Copy weekly reflections
            weekly_src = "data/aina/reflections/weekly"
            weekly_dst = os.path.join(reflection_dir, "weekly")
            if os.path.exists(weekly_src):
                shutil.copytree(weekly_src, weekly_dst)
                logger.info("  ✓ Backed up weekly reflections")
            
            # Copy conversation history
            conversations_file = "data/conversations.json"
            if os.path.exists(conversations_file):
                shutil.copy2(conversations_file, backup_path)
                logger.info("  ✓ Backed up conversation history")
            
            # Copy terminal history
            terminal_history = "data/terminal_history.json"
            if os.path.exists(terminal_history):
                shutil.copy2(terminal_history, backup_path)
                logger.info("  ✓ Backed up terminal history")
            
            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "date": date_str,
                "type": backup_type,
                "description": description,
                "memory_counts": memory_counts,
                "total_memories": sum(memory_counts.values())
            }
            
            with open(os.path.join(backup_path, "backup_info.json"), "w") as f:
                json.dump(backup_info, f, indent=2)
            
            # Compress if requested
            final_path = backup_path
            size_bytes = self._get_directory_size(backup_path)
            
            if compress:
                final_path = self._compress_backup(backup_path)
                # Delete original directory after compression
                if os.path.exists(final_path):
                    shutil.rmtree(backup_path)
                    size_bytes = os.path.getsize(final_path)
                    logger.info(f"  ✓ Compressed backup to {os.path.basename(final_path)}")
            
            # Record in database
            self._record_backup(
                timestamp=timestamp,
                filename=os.path.basename(final_path),
                backup_type=backup_type,
                size=size_bytes,
                memory_counts=json.dumps(memory_counts),
                description=description,
                status="complete"
            )
            
            # Apply retention policy
            self._apply_retention_policy()
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Backup completed in {elapsed_time:.2f} seconds")
            
            return {
                "status": "success",
                "message": f"Backup completed successfully in {elapsed_time:.2f} seconds",
                "backup_path": final_path,
                "memory_counts": memory_counts,
                "total_memories": sum(memory_counts.values()),
                "size_bytes": size_bytes,
                "size_mb": size_bytes / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating backup: {e}")
            
            # Record failed backup
            self._record_backup(
                timestamp=timestamp,
                filename=backup_name,
                backup_type=backup_type,
                size=0,
                memory_counts="{}",
                description=f"Failed: {str(e)}",
                status="failed"
            )
            
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
            Restoration result information
        """
        logger.info(f"Starting restoration from backup {backup_id}...")
        start_time = time.time()
        
        try:
            # Get backup info
            backup_info = self._get_backup_info(backup_id)
            
            if not backup_info:
                return {
                    "status": "error",
                    "message": f"Backup {backup_id} not found"
                }
            
            # Get backup path
            backup_filename = backup_info["filename"]
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Check if backup exists
            if not os.path.exists(backup_path):
                return {
                    "status": "error",
                    "message": f"Backup file {backup_filename} not found"
                }
            
            # If backup is compressed, extract it
            temp_dir = None
            if backup_filename.endswith(".zip"):
                temp_dir = os.path.join(self.backup_dir, "temp_restore")
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                os.makedirs(temp_dir, exist_ok=True)
                
                # Extract zip
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Use extracted directory
                backup_path = temp_dir
            
            # Restore each memory type
            for memory_type in ['core', 'episodic', 'semantic', 'personal']:
                type_dir = os.path.join(backup_path, memory_type)
                if os.path.exists(type_dir):
                    success = self.memory_manager.storage.restore(memory_type, type_dir)
                    if success:
                        logger.info(f"  ✓ Restored {memory_type} memories")
                    else:
                        logger.warning(f"  ✗ Failed to restore {memory_type} memories")
            
            # Restore reflection files
            reflection_src = os.path.join(backup_path, "reflections")
            if os.path.exists(reflection_src):
                reflection_dst = "data/aina/reflections"
                
                # Clear existing reflections
                if os.path.exists(reflection_dst):
                    shutil.rmtree(reflection_dst)
                
                # Copy reflections
                shutil.copytree(reflection_src, reflection_dst)
                logger.info("  ✓ Restored reflections")
            
            # Restore conversation history
            conversations_file = os.path.join(backup_path, "conversations.json")
            if os.path.exists(conversations_file):
                shutil.copy2(conversations_file, "data/conversations.json")
                logger.info("  ✓ Restored conversation history")
            
            # Restore terminal history
            terminal_file = os.path.join(backup_path, "terminal_history.json")
            if os.path.exists(terminal_file):
                shutil.copy2(terminal_file, "data/terminal_history.json")
                logger.info("  ✓ Restored terminal history")
            
            # Clean up temp directory if used
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            elapsed_time = time.time() - start_time
            logger.info(f"✅ Restore completed in {elapsed_time:.2f} seconds")
            
            return {
                "status": "success",
                "message": f"Restore completed successfully in {elapsed_time:.2f} seconds",
                "backup_info": backup_info
            }
            
        except Exception as e:
            logger.error(f"❌ Error restoring backup: {e}")
            
            # Clean up temp directory if used
            if 'temp_dir' in locals() and temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            return {
                "status": "error",
                "message": f"Restore failed: {str(e)}"
            }
    
    def list_backups(self, 
                   backup_type: Optional[str] = None, 
                   limit: int = 20) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            backup_type: Filter by backup type (optional)
            limit: Maximum number of backups to return
            
        Returns:
            List of backup information
        """
        try:
            conn = sqlite3.connect(self.backup_metadata_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM backups WHERE status = 'complete'"
            params = []
            
            if backup_type:
                query += " AND backup_type = ?"
                params.append(backup_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            backups = []
            for row in rows:
                backup = dict(row)
                backup["memory_counts"] = json.loads(backup["memory_counts"])
                backup["date"] = datetime.datetime.fromtimestamp(backup["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                backup["size_mb"] = backup["size"] / (1024 * 1024)
                backups.append(backup)
            
            conn.close()
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def start_scheduled_backup(self, 
                             interval_hours: int = 24,
                             backup_type: str = "scheduled") -> Dict[str, Any]:
        """
        Start scheduled backups.
        
        Args:
            interval_hours: Interval between backups in hours
            backup_type: Type to assign to these backups
            
        Returns:
            Status information
        """
        if self.scheduled_backup_active:
            return {
                "status": "warning",
                "message": "Scheduled backup is already running"
            }
        
        self.backup_interval_hours = interval_hours
        self.scheduled_backup_active = True
        
        # Start backup thread
        self.scheduled_backup_thread = threading.Thread(
            target=self._scheduled_backup_worker,
            args=(interval_hours, backup_type),
            daemon=True
        )
        self.scheduled_backup_thread.start()
        
        logger.info(f"Started scheduled backups every {interval_hours} hours")
        
        return {
            "status": "success",
            "message": f"Scheduled backups started (every {interval_hours} hours)"
        }
    
    def stop_scheduled_backup(self) -> Dict[str, Any]:
        """
        Stop scheduled backups.
        
        Returns:
            Status information
        """
        if not self.scheduled_backup_active:
            return {
                "status": "warning",
                "message": "No scheduled backup is running"
            }
        
        self.scheduled_backup_active = False
        
        # Wait for thread to terminate
        if self.scheduled_backup_thread and self.scheduled_backup_thread.is_alive():
            self.scheduled_backup_thread.join(timeout=1.0)
        
        logger.info("Stopped scheduled backups")
        
        return {
            "status": "success",
            "message": "Scheduled backups stopped"
        }
    
    def set_retention_policy(self, policy: Dict[str, int]) -> Dict[str, Any]:
        """
        Set backup retention policy.
        
        Args:
            policy: Dictionary with retention days for each backup type
            
        Returns:
            Status information
        """
        # Validate policy
        valid_types = ["daily", "weekly", "monthly", "yearly", "manual", "scheduled"]
        for backup_type, days in policy.items():
            if backup_type not in valid_types:
                return {
                    "status": "error",
                    "message": f"Invalid backup type: {backup_type}"
                }
            
            if not isinstance(days, int) or days < 1:
                return {
                    "status": "error",
                    "message": f"Invalid retention days for {backup_type}: {days}"
                }
        
        # Update policy
        self.retention_policy.update(policy)
        
        # Apply new policy
        self._apply_retention_policy()
        
        logger.info(f"Updated retention policy: {self.retention_policy}")
        
        return {
            "status": "success",
            "message": "Retention policy updated",
            "policy": self.retention_policy
        }
    
    def _scheduled_backup_worker(self, interval_hours: int, backup_type: str) -> None:
        """Background worker for scheduled backups."""
        logger.info(f"Scheduled backup worker started (interval: {interval_hours} hours)")
        
        while self.scheduled_backup_active:
            try:
                # Create backup
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                description = f"Scheduled backup ({current_date})"
                
                # Determine backup type based on date
                now = datetime.datetime.now()
                actual_type = backup_type
                
                # If it's the first day of the month, make it a monthly backup
                if now.day == 1:
                    actual_type = "monthly"
                    description = f"Monthly backup ({now.strftime('%Y-%m')})"
                
                # If it's the first day of the year, make it a yearly backup
                if now.day == 1 and now.month == 1:
                    actual_type = "yearly"
                    description = f"Yearly backup ({now.year})"
                
                # If it's Sunday, make it a weekly backup
                if now.weekday() == 6:  # 6 = Sunday
                    actual_type = "weekly"
                    week_number = now.isocalendar()[1]
                    description = f"Weekly backup (Week {week_number}, {now.year})"
                
                # For regular days
                if actual_type == backup_type:
                    actual_type = "daily"
                    description = f"Daily backup ({now.strftime('%Y-%m-%d')})"
                
                # Create the backup
                self.create_backup(
                    backup_type=actual_type,
                    description=description,
                    compress=True
                )
                
                # Apply retention policy
                self._apply_retention_policy()
                
                # Sleep until next backup time
                for _ in range(interval_hours * 60 * 60):
                    if not self.scheduled_backup_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in scheduled backup: {e}")
                # Sleep for a while before retrying
                time.sleep(60 * 60)  # 1 hour
    
    def _compress_backup(self, backup_path: str) -> str:
        """
        Compress a backup directory into a zip file.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            Path to compressed file
        """
        # Create zip filename
        zip_path = backup_path + ".zip"
        
        # Create zip file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add files
            for root, _, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(backup_path))
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def _record_backup(self, 
                     timestamp: int, 
                     filename: str, 
                     backup_type: str,
                     size: int,
                     memory_counts: str,
                     description: str,
                     status: str) -> None:
        """Record backup metadata in the database."""
        try:
            conn = sqlite3.connect(self.backup_metadata_db)
            cursor = conn.cursor()
            
            # Set retention days based on policy
            retention_days = 30  # Default
            if backup_type in self.retention_policy:
                retention_days = self.retention_policy[backup_type]
            
            # Insert record
            cursor.execute(
                '''
                INSERT INTO backups (
                    timestamp, filename, backup_type, size, 
                    memory_counts, description, status, retention_days
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (timestamp, filename, backup_type, size, 
                 memory_counts, description, status, retention_days)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording backup: {e}")
    
    def _get_backup_info(self, backup_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """Get backup information from database."""
        try:
            conn = sqlite3.connect(self.backup_metadata_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query based on ID or filename
            if isinstance(backup_id, int) or backup_id.isdigit():
                cursor.execute("SELECT * FROM backups WHERE id = ?", (int(backup_id),))
            else:
                # Remove .zip extension if present
                if backup_id.endswith('.zip'):
                    filename = backup_id
                else:
                    filename = backup_id
                    
                cursor.execute("SELECT * FROM backups WHERE filename = ?", (filename,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                backup = dict(row)
                backup["memory_counts"] = json.loads(backup["memory_counts"])
                return backup
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return None
    
    def _apply_retention_policy(self) -> None:
        """Apply retention policy to clean up old backups."""
        try:
            conn = sqlite3.connect(self.backup_metadata_db)
            cursor = conn.cursor()
            
            # Get current time
            now = int(time.time())
            
            # Get backups to delete
            cursor.execute(
                '''
                SELECT id, filename FROM backups 
                WHERE status = 'complete' 
                AND (timestamp + retention_days * 86400) < ?
                ''',
                (now,)
            )
            
            to_delete = cursor.fetchall()
            
            # Delete each backup
            for backup_id, filename in to_delete:
                # Delete file
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                
                # Update status in database
                cursor.execute(
                    "UPDATE backups SET status = 'deleted' WHERE id = ?",
                    (backup_id,)
                )
                
                logger.info(f"Deleted expired backup: {filename}")
            
            conn.commit()
            conn.close()
            
            if to_delete:
                logger.info(f"Applied retention policy: deleted {len(to_delete)} expired backups")
                
        except Exception as e:
            logger.error(f"Error applying retention policy: {e}")
    
    def _get_directory_size(self, path: str) -> int:
        """Get the total size of a directory in bytes."""
        total_size = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        
        return total_size