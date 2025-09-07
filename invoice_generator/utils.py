import os
import json
from typing import Dict, Any, Optional
from datetime import date, datetime


def sanitize_filename(name: str) -> str:
	"""Remove invalid filesystem characters and ensures proper length.
	In the event of a `filename` that is > 50 bytes, the extension will be preserved.
	Note: This function does not take into account restrictive NTFS max path limitations.
	"""
	invalid_chars = '<>:"/\\|?*'
	safe_name = name
	for char in invalid_chars:
		safe_name = safe_name.replace(char, '_')
	safe_name = safe_name.strip()
	# If name with extension would be too long, truncate the base name
	if len(safe_name) > 50:
		if '.' in safe_name:
			base, ext = safe_name.rsplit('.', 1)
			max_base_len = 50 - len(ext) - 1  # -1 for the dot
			if max_base_len > 0:
				return f"{base[:max_base_len]}.{ext}"
		return safe_name[:50]
	return safe_name


def prepare_for_json_serialization(data: Dict[str, Any]) -> Dict[str, Any]:
	"""Convert date objects to ISO format strings for JSON serialization."""
	serializable = {}
	for key, value in data.items():
		if isinstance(value, date):
			serializable[key] = value.isoformat()
		elif hasattr(value, 'isoformat'):
			serializable[key] = value.isoformat()
		else:
			serializable[key] = value
	return serializable


def safe_json_load(file_path: str) -> Optional[Dict[str, Any]]:
	"""Load JSON file with error handling.
	Returns a `dict` containing the JSON on success, `None` on failure.
	"""
	try:
		with open(file_path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except (IOError, OSError, json.JSONDecodeError):
		return None


def safe_json_save(file_path: str, data: Dict[str, Any]) -> bool:
	"""Save data as JSON file with error handling.
	Returns a bool (`True` on success, `False` on failure).
	"""
	try:
		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
		return True
	except (IOError, OSError, json.JSONEncodeError):
		return False


def ensure_directory(directory: str) -> bool:
	"""Create directory if it doesn't exist.
	Returns a bool (`True` on success, `False` on failure).
	"""
	try:
		if not os.path.exists(directory):
			os.makedirs(directory)
		return True
	except OSError:
		return False


def parse_wx_date_to_python(wx_date):
	"""Convert wxPython DateTime to Python date object.
	Returns a datetime` object on success, `None` on failure.
	"""
	try:
		if wx_date.IsValid():
			return date(wx_date.GetYear(), wx_date.GetMonth() + 1, wx_date.GetDay())
		return None
	except:
		return None


def python_date_to_wx_date(py_date, wx):
	"""Convert Python date object to wxPython DateTime.
	Returns a `wx.DateTime` object on success, `None` on failure.
	"""
	try:
		if isinstance(py_date, str):
			date_obj = datetime.fromisoformat(py_date).date()
		elif isinstance(py_date, date):
			date_obj = py_date
		else:
			return None
		return wx.DateTime(date_obj.day, date_obj.month - 1, date_obj.year)
	except:
		return None
