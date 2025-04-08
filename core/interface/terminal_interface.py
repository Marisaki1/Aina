import os
import sys
import time
import asyncio
import json
import readline  # For better input handling
from typing import Dict, List, Any, Optional, Callable

class TerminalInterface:
    """
    Terminal interface for interacting with Aina.
    Provides a command-line experience with advanced features.
    """
    
    def __init__(self, agent):
        """
        Initialize terminal interface.
        
        Args:
            agent: Agent instance
        """
        self.agent = agent
        self.running = False
        self.user_id = "terminal_user"  # Default user ID
        self.commands = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "clear": self.cmd_clear,
            "memory": self.cmd_memory,
            "vision": self.cmd_vision,
            "listen": self.cmd_listen,
            "speak": self.cmd_speak,
            "status": self.cmd_status,
            "reflect": self.cmd_reflect,
            "backup": self.cmd_backup
        }
        
        # Terminal state
        self.vision_active = False
        self.listening_active = False
        
        # Configure readline for command history
        readline.parse_and_bind("tab: complete")
        
        # Set up vision system if available
        try:
            from utils.vision.camera import CameraManager
            self.camera_manager = CameraManager()
            self.has_vision = True
        except (ImportError, ModuleNotFoundError):
            self.camera_manager = None
            self.has_vision = False
        
        # Set up audio system if available
        try:
            from utils.audio.speech_recognition import SpeechRecognizer
            from utils.audio.text_to_speech import TextToSpeech
            
            self.speech_recognizer = SpeechRecognizer()
            self.text_to_speech = TextToSpeech()
            self.has_audio = True
        except (ImportError, ModuleNotFoundError):
            self.speech_recognizer = None
            self.text_to_speech = None
            self.has_audio = False
    
    def start(self):
        """Start the terminal interface."""
        self.running = True
        
        # Terminal welcome
        self._clear_screen()
        self._print_welcome()
        
        # Main interaction loop
        while self.running:
            try:
                # Get user input
                user_input = input("\n\033[36m>\033[0m ").strip()
                
                # Check if this is a command
                if user_input.startswith("!"):
                    self._handle_command(user_input[1:])
                else:
                    # Process as conversation
                    self._process_message(user_input)
            
            except KeyboardInterrupt:
                print("\n\033[33mKeyboard interrupt detected. Type !exit to quit.\033[0m")
            except Exception as e:
                print(f"\n\033[31mError: {str(e)}\033[0m")
        
        # Clean up
        self._cleanup()
    
    def _handle_command(self, command_text):
        """Handle a terminal command."""
        # Split command and arguments
        parts = command_text.split(maxsplit=1)
        command = parts[0].lower() if parts else ""
        args = parts[1] if len(parts) > 1 else ""
        
        # Execute command if it exists
        if command in self.commands:
            self.commands[command](args)
        else:
            print(f"\033[31mUnknown command: {command}\033[0m")
            print("Type !help for available commands")
    
    def _process_message(self, message):
        """Process a conversational message."""
        if not message:
            return
        
        # Show thinking indicator
        self._print_thinking()
        
        try:
            # Get camera context if vision is active
            vision_context = None
            if self.vision_active and self.camera_manager:
                try:
                    frame = self.camera_manager.capture_frame()
                    vision_context = {
                        "vision_active": True,
                        "image_description": self.camera_manager.describe_frame(frame)
                    }
                except Exception as e:
                    print(f"\033[33mVision error: {e}\033[0m")
            
            # Create context
            context = {
                "interface_type": "terminal",
                "vision_context": vision_context,
                "timestamp": time.time()
            }
            
            # Get response from agent
            response = self.agent.process_message(
                user_id=self.user_id,
                message=message,
                interface_type="terminal",
                context=context
            )
            
            # Display response
            print(f"\n\033[35mAina:\033[0m {response}")
            
            # Speak response if TTS is active
            if self.text_to_speech and self.listening_active:
                self.text_to_speech.speak(response)
                
        except Exception as e:
            print(f"\033[31mError processing message: {str(e)}\033[0m")
    
    def _print_welcome(self):
        """Print welcome message."""
        print("\033[35m" + "=" * 60)
        print("                   AINA TERMINAL INTERFACE")
        print("=" * 60 + "\033[0m")
        print("\033[36mWelcome! I'm Aina, your AI assistant.\033[0m")
        print("Type your messages to chat with me, or use commands:")
        print("  !help     - Show available commands")
        print("  !exit     - Exit the terminal")
        print("  !vision   - Toggle webcam vision")
        print("  !listen   - Toggle speech recognition")
        
        # Show status of optional features
        if not self.has_vision:
            print("\033[33mNote: Vision system not available (missing dependencies)\033[0m")
        if not self.has_audio:
            print("\033[33mNote: Audio system not available (missing dependencies)\033[0m")
        
        print("\033[35m" + "-" * 60 + "\033[0m")
    
    def _print_thinking(self):
        """Show thinking animation."""
        sys.stdout.write("\033[33mThinking")
        for _ in range(3):
            time.sleep(0.3)
            sys.stdout.write(".")
            sys.stdout.flush()
        sys.stdout.write("\033[0m\r" + " " * 20 + "\r")
    
    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _cleanup(self):
        """Clean up resources before exit."""
        # Release camera if active
        if self.camera_manager:
            self.camera_manager.release()
        
        # Stop audio systems if active
        if self.speech_recognizer and self.listening_active:
            self.speech_recognizer.stop()
        
        # Backup memory
        self.agent.backup_memory()
        
        print("\n\033[36mThank you for talking with me! Goodbye.\033[0m")
    
    # Command implementations
    
    def cmd_help(self, args):
        """Show help information."""
        print("\n\033[36mAvailable Commands:\033[0m")
        print("  !help     - Show this help message")
        print("  !exit     - Exit the terminal")
        print("  !clear    - Clear the screen")
        print("  !memory   - Memory system commands")
        print("  !vision   - Control vision system")
        print("  !listen   - Toggle speech recognition")
        print("  !speak    - Text-to-speech a message")
        print("  !status   - Show system status")
        print("  !reflect  - Trigger memory reflection")
        print("  !backup   - Backup memory system")
        
        if args:
            # Show detailed help for specific command
            cmd = args.split()[0]
            if cmd == "memory":
                print("\n\033[36mMemory Commands:\033[0m")
                print("  !memory search [query]  - Search memories")
                print("  !memory profile         - View your user profile")
                print("  !memory clear           - Clear conversation history")
            elif cmd == "vision":
                print("\n\033[36mVision Commands:\033[0m")
                print("  !vision on              - Enable webcam vision")
                print("  !vision off             - Disable webcam vision")
                print("  !vision screenshot      - Capture and analyze screen")
                print("  !vision describe        - Describe what Aina sees")
    
    def cmd_exit(self, args):
        """Exit the terminal."""
        self.running = False
    
    def cmd_clear(self, args):
        """Clear the screen."""
        self._clear_screen()
        self._print_welcome()
    
    def cmd_memory(self, args):
        """Memory system commands."""
        if not args:
            print("\033[36mMemory Commands:\033[0m")
            print("  !memory search [query]  - Search memories")
            print("  !memory profile         - View your user profile")
            print("  !memory clear           - Clear conversation history")
            return
        
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcmd == "search" and subargs:
            # Search memories
            print(f"\033[36mSearching memories for: {subargs}\033[0m")
            
            memories = self.agent.search_memory(
                query=subargs,
                user_id=self.user_id
            )
            
            if memories:
                print("\n\033[36mFound memories:\033[0m")
                for i, memory in enumerate(memories, 1):
                    memory_type = memory.get("memory_type", "unknown")
                    similarity = memory.get("similarity", 0.0)
                    print(f"{i}. [{memory_type}] ({similarity:.2f}) {memory['text']}")
            else:
                print("\033[33mNo relevant memories found.\033[0m")
                
        elif subcmd == "profile":
            # Show user profile
            print(f"\033[36mRetrieving profile for user {self.user_id}\033[0m")
            
            user_info = self.agent.get_user_info(self.user_id)
            if user_info and user_info.get("memory_profile"):
                profile = user_info["memory_profile"]
                
                print("\n\033[36mUser Profile:\033[0m")
                
                if profile.get("traits"):
                    print("\nTraits:")
                    for trait in profile["traits"][:3]:
                        print(f"- {trait['text']}")
                
                if profile.get("preferences"):
                    print("\nPreferences:")
                    for pref in profile["preferences"][:3]:
                        print(f"- {pref['text']}")
                
                if profile.get("info"):
                    print("\nInformation:")
                    for info in profile["info"][:3]:
                        print(f"- {info['text']}")
                
                if profile.get("interaction_summaries"):
                    print("\nRecent Interactions:")
                    for summary in profile["interaction_summaries"][:1]:
                        print(f"- {summary['text']}")
            else:
                print("\033[33mNo profile information available.\033[0m")
                
        elif subcmd == "clear":
            # Clear conversation history
            self.agent.llm_manager.clear_history(self.user_id, interface_type="terminal")
            print("\033[36mConversation history cleared.\033[0m")
            
        else:
            print(f"\033[31mUnknown memory command: {subcmd}\033[0m")
    
    def cmd_vision(self, args):
        """Control vision system."""
        if not self.has_vision:
            print("\033[31mVision system not available.\033[0m")
            return
        
        if not args:
            status = "on" if self.vision_active else "off"
            print(f"\033[36mVision system is currently {status}.\033[0m")
            print("Usage:")
            print("  !vision on        - Enable webcam vision")
            print("  !vision off       - Disable webcam vision")
            print("  !vision screenshot - Capture and analyze screen")
            print("  !vision describe   - Describe what Aina sees")
            return
        
        subcmd = args.lower()
        
        if subcmd == "on":
            # Enable vision
            try:
                self.camera_manager.initialize()
                self.vision_active = True
                print("\033[36mVision system enabled. I can now see through the webcam.\033[0m")
            except Exception as e:
                print(f"\033[31mError enabling vision: {e}\033[0m")
                
        elif subcmd == "off":
            # Disable vision
            if self.vision_active:
                self.camera_manager.release()
                self.vision_active = False
                print("\033[36mVision system disabled.\033[0m")
            else:
                print("\033[33mVision system is already off.\033[0m")
                
        elif subcmd == "screenshot":
            # Capture and analyze screen
            try:
                if not self.camera_manager.has_screen_capture():
                    print("\033[31mScreen capture not available.\033[0m")
                    return
                    
                print("\033[36mCapturing screen...\033[0m")
                screenshot = self.camera_manager.capture_screen()
                description = self.camera_manager.describe_screen(screenshot)
                
                print("\033[36mScreen Analysis:\033[0m")
                print(description)
                
                # Store screen description in memory
                self.agent.memory_manager.episodic_memory.log_event(
                    text=f"Observed the user's screen: {description}",
                    event_type="vision",
                    importance=0.7,
                    context={"vision_type": "screen"}
                )
                
            except Exception as e:
                print(f"\033[31mError capturing screen: {e}\033[0m")
                
        elif subcmd == "describe":
            # Describe webcam view
            if not self.vision_active:
                print("\033[33mVision system is off. Turn it on first with '!vision on'.\033[0m")
                return
                
            try:
                print("\033[36mAnalyzing what I can see...\033[0m")
                frame = self.camera_manager.capture_frame()
                description = self.camera_manager.describe_frame(frame)
                
                print("\033[36mI can see:\033[0m")
                print(description)
                
                # Store vision description in memory
                self.agent.memory_manager.episodic_memory.log_event(
                    text=f"I saw: {description}",
                    event_type="vision",
                    importance=0.7,
                    context={"vision_type": "webcam"}
                )
                
            except Exception as e:
                print(f"\033[31mError processing vision: {e}\033[0m")
                
        else:
            print(f"\033[31mUnknown vision command: {subcmd}\033[0m")
    
    def cmd_listen(self, args):
        """Toggle speech recognition."""
        if not self.has_audio:
            print("\033[31mAudio system not available.\033[0m")
            return
        
        # Toggle listening mode
        self.listening_active = not self.listening_active
        
        if self.listening_active:
            try:
                # Start speech recognition
                self.speech_recognizer.start(callback=self._speech_callback)
                print("\033[36mSpeech recognition enabled. I'm listening.\033[0m")
            except Exception as e:
                self.listening_active = False
                print(f"\033[31mError enabling speech recognition: {e}\033[0m")
        else:
            # Stop speech recognition
            try:
                self.speech_recognizer.stop()
                print("\033[36mSpeech recognition disabled.\033[0m")
            except Exception as e:
                print(f"\033[31mError disabling speech recognition: {e}\033[0m")
    
    def cmd_speak(self, args):
        """Text-to-speech a message."""
        if not self.has_audio or not self.text_to_speech:
            print("\033[31mText-to-speech not available.\033[0m")
            return
        
        if not args:
            print("\033[33mUsage: !speak [message]\033[0m")
            return
        
        try:
            self.text_to_speech.speak(args)
            print(f"\033[36mSpoken: {args}\033[0m")
        except Exception as e:
            print(f"\033[31mError in text-to-speech: {e}\033[0m")
    
    def cmd_status(self, args):
        """Show system status."""
        status = self.agent.get_status()
        
        print("\n\033[36mSystem Status:\033[0m")
        print(f"Status: {status['status']}")
        print(f"Uptime: {status['uptime']}")
        print(f"Active Users: {status['active_users']}")
        
        print("\n\033[36mMemory Status:\033[0m")
        for memory_type, count in status['memory_stats'].items():
            print(f"{memory_type.capitalize()}: {count} memories")
        
        print("\n\033[36mInterface Status:\033[0m")
        print(f"Vision: {'Enabled' if self.vision_active else 'Disabled'}")
        print(f"Speech: {'Enabled' if self.listening_active else 'Disabled'}")
        
        # Additional system info
        if self.has_vision and self.camera_manager:
            print(f"Camera: {self.camera_manager.get_camera_info()}")
    
    def cmd_reflect(self, args):
        """Trigger memory reflection."""
        reflection_type = "daily"
        if args and args.lower() in ["daily", "weekly"]:
            reflection_type = args.lower()
        
        print(f"\033[36mGenerating {reflection_type} reflection...\033[0m")
        
        try:
            reflection = self.agent.create_reflection(reflection_type)
            
            print("\n\033[36mReflection Summary:\033[0m")
            print(reflection.get("summary", "No reflection generated."))
            
            if reflection.get("insights"):
                print("\n\033[36mInsights:\033[0m")
                for insight in reflection["insights"]:
                    print(f"- {insight['text']}")
            
            print(f"\n\033[36mAnalyzed {reflection.get('memory_count', 0)} memories.\033[0m")
            
        except Exception as e:
            print(f"\033[31mError generating reflection: {e}\033[0m")
    
    def cmd_backup(self, args):
        """Backup memory system."""
        print("\033[36mBacking up memory system...\033[0m")
        
        try:
            success = self.agent.backup_memory()
            if success:
                print("\033[36mMemory backup successful.\033[0m")
            else:
                print("\033[33mMemory backup completed with some errors.\033[0m")
        except Exception as e:
            print(f"\033[31mError backing up memory: {e}\033[0m")
    
    def _speech_callback(self, text):
        """Callback for speech recognition."""
        if not text:
            return
            
        # Print recognized speech
        print(f"\n\033[36mRecognized:\033[0m {text}")
        
        # Process as command or conversation
        if text.lower().startswith("command "):
            # Extract command without the "command" prefix
            command = text[8:].strip()
            print(f"\033[36mExecuting command:\033[0m {command}")
            self._handle_command(command)
        else:
            # Process as conversation
            self._process_message(text)