import os
import json
from typing import Dict, Any, Optional
from datetime import date, datetime


def sanitize_filename(name: str) -> str:
	invalid_chars = '<>:"/\\|?*'
	safe_name = name
	for char in invalid_chars:
		safe_name = safe_name.replace(char, '_')
	return safe_name.strip()[:50]


def prepare_for_json_serialization(data: Dict[str, Any]) -> Dict[str, Any]:
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
	try:
		with open(file_path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except (IOError, OSError, json.JSONDecodeError):
		return None


def safe_json_save(file_path: str, data: Dict[str, Any]) -> bool:
	try:
		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
		return True
	except (IOError, OSError, json.JSONEncodeError):
		return False


def ensure_directory(directory: str) -> bool:
	try:
		if not os.path.exists(directory):
			os.makedirs(directory)
		return True
	except OSError:
		return False


def parse_wx_date_to_python(wx_date):
	try:
		if wx_date.IsValid():
			return date(wx_date.GetYear(), wx_date.GetMonth() + 1, wx_date.GetDay())
		return None
	except:
		return None


def python_date_to_wx_date(py_date, wx):
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