#!/usr/bin/env python3
import os
import sys
import argparse
import time
import signal
import threading
from typing import Dict, Optional, Any, List, Union

from core.agent import Agent
from core.interface.terminal_interface import TerminalInterface
from utils.logging_utils import get_logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aina Terminal Interface - AI assistant with memory"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="data/aina/config/memory_config.json",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        default="models/j.gguf",
        help="Path to LLM model file"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--vision", 
        action="store_true",
        help="Enable vision system at startup"
    )
    
    parser.add_argument(
        "--listen", 
        action="store_true",
        help="Enable speech recognition at startup"
    )
    
    parser.add_argument(
        "--user", 
        type=str, 
        default="terminal_user",
        help="User ID for the terminal session"
    )
    
    return parser.parse_args()

def setup_environment(args):
    """Set up the environment before starting Aina."""
    # Create necessary directories
    os.makedirs("data/aina/config", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger = get_logger(
        name="aina_terminal",
        console_level=getattr(get_logger().logger, log_level),
        use_colors=True
    )
    
    # Check for model file
    if not os.path.exists(args.model):
        logger.warning(f"Model file not found: {args.model}")
        logger.info("Starting without LLM model. Please place a model file in the models directory.")
    
    return logger

def handle_signals(terminal_interface, logger):
    """Set up signal handlers for clean shutdown."""
    
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        if hasattr(terminal_interface, 'running'):
            terminal_interface.running = False
        
        # Give a moment for cleanup
        time.sleep(0.5)
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for Aina terminal interface."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup environment and logging
    logger = setup_environment(args)
    
    try:
        # Display startup message
        print("\n" + "=" * 60)
        print("  AINA TERMINAL INTERFACE - AI Assistant with Memory")
        print("=" * 60 + "\n")
        
        print("Starting Aina agent...")
        logger.info("Initializing Aina agent")
        
        # Initialize the agent
        agent = Agent(config_path=args.config)
        
        # Set model path if specified
        if args.model and os.path.exists(args.model):
            agent.llm_manager.model_path = args.model
            # This will be lazy-loaded when needed
        
        # Initialize terminal interface
        logger.info("Initializing terminal interface")
        terminal = TerminalInterface(agent)
        
        # Set user ID if specified
        if args.user:
            terminal.user_id = args.user
        
        # Setup signal handlers for clean shutdown
        handle_signals(terminal, logger)
        
        # Activate vision if requested
        if args.vision and terminal.has_vision:
            terminal.vision_active = True
            terminal.camera_manager.initialize()
            logger.info("Vision system activated")
        
        # Activate speech recognition if requested
        if args.listen and terminal.has_audio:
            terminal.listening_active = True
            terminal.speech_recognizer.start(callback=terminal._speech_callback)
            logger.info("Speech recognition activated")
        
        # Start interface
        logger.info("Starting terminal interface")
        terminal.start()
        
    except Exception as e:
        logger.exception(f"Error in main: {e}")
        print(f"\nError: {e}")
        print("Check the logs for more details.")
        
        # Try to clean up resources
        print("\nAttempting to clean up resources...")
        try:
            if 'terminal' in locals():
                terminal._cleanup()
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())