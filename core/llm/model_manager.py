import os
import time
import json
from typing import Dict, List, Any, Optional
from llama_cpp import Llama

class ModelManager:
    """
    Manages loading and optimization of LLM models.
    Provides a high-level interface for model selection and optimization.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model manager.
        
        Args:
            config_path: Path to model configuration file
        """
        # Default configuration
        self.config = {
            "default_model": "models/j.gguf",
            "models_directory": "models",
            "context_size": 10000,
            "batch_size": 256,
            "threads": 4,
            "gpu_layers": 15  # Optimized for RTX 4070 Super
        }
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                print(f"✅ Loaded model configuration from {config_path}")
            except Exception as e:
                print(f"❌ Error loading model configuration: {e}")
        
        # Create models directory
        os.makedirs(self.config["models_directory"], exist_ok=True)
        
        # Initialize models cache
        self._models = {}
        
        # Check for available models
        self._scan_models()
    
    def _scan_models(self) -> None:
        """Scan for available models in the models directory."""
        models_dir = self.config["models_directory"]
        models_found = [f for f in os.listdir(models_dir) if f.endswith(".gguf")]
        
        print(f"🔍 Found {len(models_found)} GGUF models in {models_dir}:")
        for model in models_found:
            model_path = os.path.join(models_dir, model)
            model_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
            print(f"  • {model} ({model_size:.1f} MB)")
    
    def load_model(self, 
                  model_path: Optional[str] = None,
                  gpu_layers: Optional[int] = None,
                  context_size: Optional[int] = None) -> Optional[Llama]:
        """
        Load a model with the specified parameters.
        
        Args:
            model_path: Path to the model file
            gpu_layers: Number of layers to offload to GPU
            context_size: Context window size
            
        Returns:
            Loaded model or None if loading failed
        """
        # Use default model if not specified
        if model_path is None:
            model_path = self.config["default_model"]
        
        # Use config values for unspecified parameters
        if gpu_layers is None:
            gpu_layers = self.config["gpu_layers"]
        
        if context_size is None:
            context_size = self.config["context_size"]
        
        # Check if model exists
        if not os.path.exists(model_path):
            print(f"❌ Model not found: {model_path}")
            return None
        
        # Create a cache key
        cache_key = f"{model_path}_{gpu_layers}_{context_size}"
        
        # Return cached model if available
        if cache_key in self._models:
            print(f"✅ Using cached model: {os.path.basename(model_path)}")
            return self._models[cache_key]
        
        # Load the model
        try:
            print(f"🔄 Loading model: {os.path.basename(model_path)}")
            print(f"   GPU Layers: {gpu_layers}, Context Size: {context_size}")
            
            start_time = time.time()
            
            model = Llama(
                model_path=model_path,
                n_ctx=context_size,
                n_batch=self.config["batch_size"],
                n_threads=self.config["threads"],
                n_gpu_layers=gpu_layers
            )
            
            load_time = time.time() - start_time
            print(f"✅ Model loaded in {load_time:.2f} seconds")
            
            # Cache the model
            self._models[cache_key] = model
            
            return model
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
    
    def unload_model(self, model_path: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Success status
        """
        # Find all cache keys for this model
        keys_to_remove = [k for k in self._models if k.startswith(f"{model_path}_")]
        
        if not keys_to_remove:
            print(f"⚠️ Model not loaded: {model_path}")
            return False
        
        # Remove from cache
        for key in keys_to_remove:
            del self._models[key]
        
        print(f"✅ Unloaded model: {os.path.basename(model_path)}")
        return True
    
    def get_optimal_parameters(self, gpu_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get optimal parameters for the current hardware.
        
        Args:
            gpu_info: GPU information (if available)
            
        Returns:
            Dictionary of optimal parameters
        """
        # Default parameters for RTX 4070 Super
        optimal_params = {
            "gpu_layers": 15,
            "context_size": 10000,
            "batch_size": 256,
            "threads": 4
        }
        
        # Adjust based on GPU info if provided
        if gpu_info:
            vram_gb = gpu_info.get("vram_gb", 0)
            
            if vram_gb > 20:  # High-end GPU (RTX 3090, 4090, etc.)
                optimal_params["gpu_layers"] = 30
                optimal_params["context_size"] = 16000
                optimal_params["batch_size"] = 512
            elif vram_gb > 10:  # Mid-range GPU (RTX 3070, 4070, etc.)
                optimal_params["gpu_layers"] = 15
                optimal_params["context_size"] = 10000
                optimal_params["batch_size"] = 256
            elif vram_gb > 6:  # Entry-level GPU (RTX 3060, etc.)
                optimal_params["gpu_layers"] = 8
                optimal_params["context_size"] = 8000
                optimal_params["batch_size"] = 128
            else:  # Low VRAM or no GPU
                optimal_params["gpu_layers"] = 0  # CPU only
                optimal_params["context_size"] = 4000
                optimal_params["batch_size"] = 64
        
        return optimal_params
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models in the models directory.
        
        Returns:
            List of model information
        """
        models = []
        models_dir = self.config["models_directory"]
        
        if not os.path.exists(models_dir):
            return models
        
        for filename in os.listdir(models_dir):
            if filename.endswith(".gguf"):
                model_path = os.path.join(models_dir, filename)
                model_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
                
                model_info = {
                    "filename": filename,
                    "path": model_path,
                    "size_mb": round(model_size, 1),
                    "is_loaded": any(k.startswith(f"{model_path}_") for k in self._models)
                }
                
                models.append(model_info)
        
        return models
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded models.
        
        Returns:
            Dictionary of model statistics
        """
        return {
            "loaded_models": len(self._models),
            "default_model": os.path.basename(self.config["default_model"]),
            "models_directory": self.config["models_directory"],
            "context_size": self.config["context_size"],
            "gpu_layers": self.config["gpu_layers"]
        }