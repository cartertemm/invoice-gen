import json
import os
import os
from typing import Dict, List, Optional, Any
from datetime import date
from .utils import sanitize_filename, prepare_for_json_serialization, safe_json_load, safe_json_save, ensure_directory


class TemplateManager:
	def __init__(self, templates_dir: str = "templates"):
		self.templates_dir = templates_dir
		ensure_directory(self.templates_dir)

	def save_template(self, name: str, field_values: Dict[str, Any]) -> bool:
		try:
			safe_name = sanitize_filename(name)
			file_path = os.path.join(self.templates_dir, f"{safe_name}.json")
			serializable_values = prepare_for_json_serialization(field_values)
			template_data = {
				"name": name,
				"created": date.today().isoformat(),
				"fields": serializable_values
			}
			with open(file_path, 'w', encoding='utf-8') as f:
				json.dump(template_data, f, indent=2, ensure_ascii=False)
			return True
		except (IOError, OSError):
			return False

	def load_template(self, name: str) -> Optional[Dict[str, Any]]:
		try:
			safe_name = sanitize_filename(name)
			file_path = os.path.join(self.templates_dir, f"{safe_name}.json")
			if not os.path.exists(file_path):
				return None
			with open(file_path, 'r', encoding='utf-8') as f:
				template_data = json.load(f)
			return self._process_loaded_data(template_data.get("fields", {}))
		except (IOError, OSError, json.JSONDecodeError):
			return None

	def list_templates(self) -> List[Dict[str, str]]:
		templates = []
		try:
			for filename in os.listdir(self.templates_dir):
				if filename.endswith('.json'):
					try:
						file_path = os.path.join(self.templates_dir, filename)
						with open(file_path, 'r', encoding='utf-8') as f:
							template_data = json.load(f)
						templates.append({
							"name": template_data.get("name", filename[:-5]),
							"filename": filename[:-5],
							"created": template_data.get("created", "Unknown"),
							"field_count": len(template_data.get("fields", {}))
						})
					except (IOError, json.JSONDecodeError):
						continue
			templates.sort(key=lambda x: x["name"].lower())
			return templates
		except OSError:
			return []

	def delete_template(self, name: str) -> bool:
		try:
			safe_name = sanitize_filename(name)
			file_path = os.path.join(self.templates_dir, f"{safe_name}.json")
			if os.path.exists(file_path):
				os.remove(file_path)
				return True
			return False
		except OSError:
			return False



	def _process_loaded_data(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
		processed = {}
		for key, value in field_data.items():
			if key in ['date', 'due_date'] and isinstance(value, str):
				try:
					processed[key] = value
				except ValueError:
					processed[key] = value
			else:
				processed[key] = value
		return processed


template_manager = TemplateManager()
