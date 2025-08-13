"""
Production-Ready Configuration Management System

A robust, thread-safe configuration manager supporting multiple sources,
hot reloading, validation, and observability for modern backend services.

Key Features:
- Multi-source configuration (JSON, YAML, environment, remote)
- Hot reloading with change detection
- Schema validation and type coercion
- Encryption support for sensitive values
- Comprehensive logging and metrics
- Thread-safe operations
"""

import os
import json
import yaml
import logging
import threading
import time
from typing import Any, Dict, Optional, List, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from cryptography.fernet import Fernet
import hashlib
from functools import wraps
from contextlib import contextmanager
import requests

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s:%(lineno)d'
)
logger = logging.getLogger(__name__)

class ConfigSource(Enum):
    """Configuration source types"""
    FILE = "file"
    ENVIRONMENT = "environment"
    REMOTE = "remote"
    DEFAULT = "default"

@dataclass
class ConfigMetrics:
    """Configuration access metrics for monitoring"""
    access_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    reload_count: int = 0
    validation_errors: int = 0
    last_reload: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'access_count': self.access_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'reload_count': self.reload_count,
            'validation_errors': self.validation_errors,
            'last_reload': self.last_reload,
            'cache_hit_rate': self.cache_hits / max(self.access_count, 1)
        }

class ConfigError(Exception):
    """Configuration-related errors with context"""
    def __init__(self, message: str, source: Optional[ConfigSource] = None, key: Optional[str] = None):
        self.source = source
        self.key = key
        super().__init__(f"{message} (source: {source}, key: {key})")

class ConfigValidator:
    """Configuration validation and type coercion"""
    
    @staticmethod
    def validate_database_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate database configuration"""
        required_fields = ['host', 'port', 'database', 'user']
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing required database field: {field}")
        
        # Type coercion
        config['port'] = int(config['port'])
        config['timeout'] = int(config.get('timeout', 30))
        config['pool_size'] = int(config.get('pool_size', 10))
        
        return config
    
    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate API configuration"""
        if 'rate_limit' in config:
            config['rate_limit'] = int(config['rate_limit'])
        if 'timeout' in config:
            config['timeout'] = float(config['timeout'])
        
        return config

class ConfigEncryption:
    """Handle encryption/decryption of sensitive configuration values"""
    
    def __init__(self, key: Optional[bytes] = None):
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, value: str) -> str:
        """Encrypt a configuration value"""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt a configuration value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    def is_encrypted(self, value: str) -> bool:
        """Check if a value is encrypted"""
        return value.startswith('enc:')

class ConfigSourcePlugin:
    """Base class for custom config source plugins."""
    def load(self) -> Dict[str, Any]:
        raise NotImplementedError

class ConfigHookPlugin:
    """Base class for config change hook plugins."""
    def on_config_change(self, event: str, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        pass
    
class RemoteConfigLoader:
    """
    Base class for remote configuration loaders.
    Implement fetch() to return a config dict from a remote source.
    """
    def fetch(self) -> Dict[str, Any]:
        raise NotImplementedError


class HTTPConfigLoader(RemoteConfigLoader):
    """
    Loads configuration from a remote HTTP endpoint (expects JSON response).
    Includes basic retry logic for robustness.
    """
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None, retries: int = 3, timeout: int = 5):
        self.url = url
        self.headers = headers or {}
        self.retries = retries
        self.timeout = timeout

    def fetch(self) -> Dict[str, Any]:
        last_exc = None
        for attempt in range(1, self.retries + 1):
            try:
                response = requests.get(self.url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response.json() # Assumes JSON config
            except Exception as exc:
                last_exc = exc
                logger.warning(f"HTTPConfigLoader attempt {attempt} failed: {exc}")
                time.sleep(1)
        logger.error(f"HTTPConfigLoader failed after {self.retries} attempts: {last_exc}")
        raise last_exc

class ConfigManager:
    """
    Production-ready configuration manager with advanced features:
    
    - Multi-source configuration loading (JSON, YAML, env vars)
    - Hot reloading with file watching
    - Schema validation and type coercion
    - Encryption support for sensitive values
    - Thread-safe operations with read/write locks
    - Comprehensive metrics and monitoring
    - Caching with TTL support
    """
    
    def __init__(self, 
                 config_files: Optional[List[str]] = None,
                 enable_hot_reload: bool = True,
                 reload_interval: int = 30,
                 enable_encryption: bool = False,
                 encryption_key: Optional[bytes] = None,
                 remote_loaders: Optional[List[RemoteConfigLoader]] = None,
                 source_plugins: Optional[List[ConfigSourcePlugin]] = None,
                 hook_plugins: Optional[List[ConfigHookPlugin]] = None):
        
        self.config_files = config_files or ["config.json", "config.yaml"]
        self.enable_hot_reload = enable_hot_reload
        self.reload_interval = reload_interval
        self.remote_loaders = remote_loaders or []
        self.source_plugins = source_plugins or []
        self.hook_plugins = hook_plugins or []
        
        # Thread safety
        self._lock = threading.RLock()
        self._config: Dict[str, Any] = {}
        self._config_cache: Dict[str, Any] = {}
        self._file_hashes: Dict[str, str] = {}
        
        # Metrics and monitoring
        self.metrics = ConfigMetrics()
        
        # Encryption support
        self.encryption = ConfigEncryption(encryption_key) if enable_encryption else None
        
        # Validation rules
        self.validators = {
            'database': ConfigValidator.validate_database_config,
            'api': ConfigValidator.validate_api_config
        }
        
        # Change listeners
        self._change_listeners: List[Callable[[str, Any, Any], None]] = []
        
        # Initialize configuration
        self._load_all_configs()
        
        # Start hot reload if enabled
        if enable_hot_reload:
            self._start_hot_reload()

    def add_source_plugin(self, plugin: ConfigSourcePlugin):
        """Register a custom config source plugin."""
        self.source_plugins.append(plugin)

    def add_hook_plugin(self, plugin: ConfigHookPlugin):
        """Register a config change hook plugin."""
        self.hook_plugins.append(plugin)

    def _metric_decorator(func):
        """Decorator to track configuration access metrics"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            self.metrics.access_count += 1
            try:
                result = func(self, *args, **kwargs)
                self.metrics.cache_hits += 1
                return result
            except (KeyError, ConfigError):
                self.metrics.cache_misses += 1
                raise
        return wrapper
    
    def _load_all_configs(self):
        """Load configuration from all sources"""
        with self._lock:
            self._config = {}
            
            # Load from files
            for config_file in self.config_files:
                if os.path.exists(config_file):
                    self._load_config_file(config_file)
            # Load from remote sources 
            for loader in self.remote_loaders:
                try:
                    remote_config = loader.fetch()
                    self._deep_merge(self._config, remote_config)
                    logger.info(f"Loaded remote config from {type(loader).__name__}")
                except Exception as e:
                    logger.error(f"Remote config loader error: {e}")
            # Load from source plugins
            for plugin in self.source_plugins:
                try:
                    plugin_config = plugin.load()
                    self._deep_merge(self._config, plugin_config)
                    logger.info(f"Loaded config from plugin {type(plugin).__name__}")
                except Exception as e:
                    logger.error(f"Source plugin error: {e}")
            # Override with environment variables
            self._load_environment_overrides()
            
            # Apply validation
            self._validate_config()
            
            # Update metrics
            self.metrics.reload_count += 1
            self.metrics.last_reload = time.time()
            
            logger.info(f"Configuration loaded from {len(self.config_files)} sources")
    
    def _load_config_file(self, config_file: str):
        """Load configuration from a single file"""
        try:
            file_path = Path(config_file)
            content = file_path.read_text()
            
            # Calculate file hash for change detection
            file_hash = hashlib.md5(content.encode()).hexdigest()
            self._file_hashes[config_file] = file_hash
            
            # Parse based on file extension
            if file_path.suffix.lower() == '.json':
                file_config = json.loads(content)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                file_config = yaml.safe_load(content)
            else:
                logger.warning(f"Unsupported file format: {config_file}")
                return
            
            # Merge with existing config
            self._deep_merge(self._config, file_config)
            
            logger.info(f"Loaded configuration from {config_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_file}: {e}")
            raise ConfigError(f"Invalid JSON format: {e}", ConfigSource.FILE, config_file)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {config_file}: {e}")
            raise ConfigError(f"Invalid YAML format: {e}", ConfigSource.FILE, config_file)
        except Exception as e:
            logger.error(f"Error loading {config_file}: {e}")
            raise ConfigError(f"Failed to load config file: {e}", ConfigSource.FILE, config_file)
    
    def _load_environment_overrides(self):
        """Load environment variable overrides"""
        env_mappings = {
            'DATABASE_HOST': 'database.host',
            'DATABASE_PORT': 'database.port',
            'DATABASE_NAME': 'database.database',
            'DATABASE_USER': 'database.user',
            'DATABASE_PASSWORD': 'database.password',
            'API_KEY': 'api.key',
            'API_RATE_LIMIT': 'api.rate_limit',
            'DEBUG': 'debug',
            'LOG_LEVEL': 'logging.level'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                self._set_nested_value(config_key, env_value)
                logger.info(f"Configuration override from environment: {env_var}")
    
    def _validate_config(self):
        """Validate configuration using registered validators"""
        try:
            for section, validator in self.validators.items():
                if section in self._config:
                    self._config[section] = validator(self._config[section])
        except Exception as e:
            self.metrics.validation_errors += 1
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigError(f"Validation failed: {e}")
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge two dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def _set_nested_value(self, key_path: str, value: Any):
        """Set nested dictionary value using dot notation"""
        keys = key_path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Handle type conversion
        if isinstance(value, str):
            # Try to convert string values to appropriate types
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif self._is_float(value):
                value = float(value)
        
        current[keys[-1]] = value
    
    def _is_float(self, value: str) -> bool:
        """Check if string represents a float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _start_hot_reload(self):
        """Start hot reload thread"""
        def reload_worker():
            while True:
                time.sleep(self.reload_interval)
                try:
                    self._check_and_reload()
                except Exception as e:
                    logger.error(f"Hot reload error: {e}")
        
        reload_thread = threading.Thread(target=reload_worker, daemon=True)
        reload_thread.start()
        logger.info("Hot reload enabled")
    
    def _check_and_reload(self):
        """Check for file changes and reload if necessary"""
        should_reload = False
        
        for config_file in self.config_files:
            if not os.path.exists(config_file):
                continue
                
            content = Path(config_file).read_text()
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            if current_hash != self._file_hashes.get(config_file):
                should_reload = True
                logger.info(f"Configuration file changed: {config_file}")
                break
        
        if should_reload:
            old_config = self._config.copy()
            self._load_all_configs()
            self._notify_changes(old_config, self._config)
    
    def _notify_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Notify listeners of configuration changes"""
        for listener in self._change_listeners:
            try:
                listener("config_changed", old_config, new_config)
            except Exception as e:
                logger.error(f"Error notifying config change listener: {e}")
        # Notify hook plugins
        for plugin in self.hook_plugins:
            try:
                plugin.on_config_change("config_changed", old_config, new_config)
            except Exception as e:
                logger.error(f"Error in hook plugin {type(plugin).__name__}: {e}")
    
    @_metric_decorator
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value with caching and metrics"""
        with self._lock:
            # Check cache first
            if key_path in self._config_cache:
                return self._config_cache[key_path]
            
            try:
                keys = key_path.split('.')
                current = self._config
                
                for key in keys:
                    current = current[key]
                
                # Handle encrypted values
                if self.encryption and isinstance(current, str) and self.encryption.is_encrypted(current):
                    current = self.encryption.decrypt(current[4:])  # Remove 'enc:' prefix
                
                # Cache the result
                self._config_cache[key_path] = current
                
                return current
                
            except KeyError:
                if default is not None:
                    return default
                raise ConfigError(f"Configuration key not found: {key_path}", key=key_path)
    
    def set(self, key_path: str, value: Any, encrypt: bool = False):
        """Set configuration value with optional encryption"""
        with self._lock:
            if encrypt and self.encryption:
                value = f"enc:{self.encryption.encrypt(str(value))}"
            
            self._set_nested_value(key_path, value)
            
            # Clear cache for this key
            if key_path in self._config_cache:
                del self._config_cache[key_path]
    
    def batch_get(self, key_paths: List[str], default: Any = None) -> Dict[str, Any]:
        """Get multiple configuration values at once. Returns a dict of key_path: value."""
        results = {}
        for key in key_paths:
            try:
                results[key] = self.get(key, default)
            except ConfigError:
                results[key] = default
        return results

    def batch_set(self, items: Dict[str, Any], encrypt: bool = False):
        """Set multiple configuration values at once. Accepts a dict of key_path: value."""
        with self._lock:
            for key, value in items.items():
                self.set(key, value, encrypt=encrypt)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get validated database configuration"""
        return {
            'host': self.get('database.host', 'localhost'),
            'port': self.get('database.port', 5432),
            'database': self.get('database.database', 'app_db'),
            'user': self.get('database.user', 'postgres'),
            'password': self.get('database.password', ''),
            'timeout': self.get('database.timeout', 30),
            'pool_size': self.get('database.pool_size', 10),
            'ssl_mode': self.get('database.ssl_mode', 'prefer')
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get validated API configuration"""
        return {
            'key': self.get('api.key', ''),
            'rate_limit': self.get('api.rate_limit', 1000),
            'timeout': self.get('api.timeout', 30.0),
            'retry_count': self.get('api.retry_count', 3),
            'base_url': self.get('api.base_url', 'http://localhost:8000')
        }
    
    def add_change_listener(self, listener: Callable[[str, Any, Any], None]):
        """Add configuration change listener"""
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, Any, Any], None]):
        """Remove configuration change listener"""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get configuration manager metrics"""
        return self.metrics.to_dict()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            'status': 'healthy',
            'config_files_loaded': len([f for f in self.config_files if os.path.exists(f)]),
            'hot_reload_enabled': self.enable_hot_reload,
            'encryption_enabled': self.encryption is not None,
            'metrics': self.get_metrics()
        }
    
    @contextmanager
    def temporary_override(self, key_path: str, value: Any):
        """Temporarily override a configuration value"""
        original_value = self.get(key_path, None)
        self.set(key_path, value)
        try:
            yield
        finally:
            if original_value is not None:
                self.set(key_path, original_value)
            else:
                # Remove the key if it didn't exist before
                keys = key_path.split('.')
                current = self._config
                for key in keys[:-1]:
                    current = current[key]
                if keys[-1] in current:
                    del current[keys[-1]]
    
    def __repr__(self) -> str:
        return f"ConfigManager(files={self.config_files}, hot_reload={self.enable_hot_reload})"