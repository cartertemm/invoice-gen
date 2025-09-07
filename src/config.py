import json
import os
from typing import Optional


class Config:
	"""Simple configuration system for storing API key and other settings."""
	
	def __init__(self, config_file: str = 'config.json'):
		self.config_file = config_file
		self._data = self._load_config()
	
	def _load_config(self) -> dict:
		"""Load configuration from file or create empty config."""
		if os.path.exists(self.config_file):
			try:
				with open(self.config_file, 'r') as f:
					return json.load(f)
			except (json.JSONDecodeError, IOError):
				return {}
		return {}
	
	def _save_config(self) -> None:
		"""Save configuration to file."""
		try:
			with open(self.config_file, 'w') as f:
				json.dump(self._data, f, indent=2)
		except IOError:
			pass
	
	def get_api_key(self) -> Optional[str]:
		"""Get stored API key."""
		return self._data.get('api_key')
	
	def set_api_key(self, api_key: str) -> None:
		"""Store API key."""
		self._data['api_key'] = api_key
		self._save_config()
	
	def clear_api_key(self) -> None:
		"""Remove stored API key."""
		if 'api_key' in self._data:
			del self._data['api_key']
			self._save_config()


# Global config instance
config = Config()