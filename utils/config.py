"""Configuration management utilities."""
import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


class Config:
    """Configuration manager with validation."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration structure and values."""
        required_sections = ['you', 'git', 'analysis', 'output']
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"Missing required config section: {section}")
        
        # Validate 'you' section
        you_config = self._config['you']
        if not you_config.get('full_name'):
            raise ConfigError("'you.full_name' is required")
        if not you_config.get('emails') or not isinstance(you_config['emails'], list):
            raise ConfigError("'you.emails' must be a non-empty list")
        
        # Validate output count
        bullets_count = self._config['output'].get('bullets_count', 0)
        if not isinstance(bullets_count, int) or bullets_count <= 0:
            raise ConfigError("'output.bullets_count' must be a positive integer")
    
    @property
    def person_name(self) -> str:
        return self._config['you']['full_name']
    
    @property
    def person_role(self) -> str:
        return self._config['you'].get('role', 'Software Engineer')
    
    @property
    def person_aliases(self) -> List[str]:
        return self._config['you'].get('aliases', [])
    
    @property
    def person_emails(self) -> List[str]:
        return self._config['you']['emails']
    
    @property
    def git_since(self) -> Optional[str]:
        return self._config['git'].get('since')
    
    @property
    def git_until(self) -> Optional[str]:
        return self._config['git'].get('until')
    
    @property
    def include_merge_commits(self) -> bool:
        return self._config['git'].get('include_merge_commits', False)
    
    @property
    def max_files(self) -> int:
        return self._config['analysis'].get('max_files', 2000)
    
    @property
    def hot_file_top_n(self) -> int:
        return self._config['analysis'].get('hot_file_top_n', 50)
    
    @property
    def languages_of_interest(self) -> List[str]:
        return self._config['analysis'].get('languages_of_interest', [])
    
    @property
    def bullets_count(self) -> int:
        return self._config['output']['bullets_count']
    
    @property
    def output_style(self) -> str:
        return self._config['output'].get('style', 'senior_technical_lead')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dotted key path."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value