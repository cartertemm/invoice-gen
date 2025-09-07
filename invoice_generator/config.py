import json
import os
from typing import Optional, Any


class Config:
	"""Simple configuration system for storing settings."""

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

	def get(self, key: str, default: Any = None) -> Any:
		"""Get configuration value or default."""
		return self._data.get(key, default)

	def set(self, key: str, value: Any) -> None:
		"""Set configuration value and save."""
		self._data[key] = value
		self._save_config()

	def delete(self, key: str) -> None:
		"""Remove configuration key and save."""
		if key in self._data:
			del self._data[key]
			self._save_config()


# Global config instance
config = Config()