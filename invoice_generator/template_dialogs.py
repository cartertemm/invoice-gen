import wx
from .templates import template_manager


class SaveTemplateDialog(wx.Dialog):
	"""Dialog for saving current values as a template."""

	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, title="Save as Template", size=(400, 150),
						   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.template_name = ""
		self._create_ui()

	def _create_ui(self):
		"""Build the save template dialog UI."""
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		name_label = wx.StaticText(self, label="Template Name:")
		self.name_ctrl = wx.TextCtrl(self, size=(350, -1))
		self.name_ctrl.SetToolTip("Enter a name for this template")
		main_sizer.Add(name_label, 0, wx.ALL, 8)
		main_sizer.Add(self.name_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
		# Status text
		self.status_text = wx.StaticText(self, label="")
		main_sizer.Add(self.status_text, 0, wx.ALL, 8)
		btn_sizer = wx.StdDialogButtonSizer()
		save_btn = wx.Button(self, wx.ID_OK, "Save")
		cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		save_btn.Bind(wx.EVT_BUTTON, self._on_save)
		cancel_btn.Bind(wx.EVT_BUTTON, self._on_cancel)
		btn_sizer.AddButton(save_btn)
		btn_sizer.AddButton(cancel_btn)
		btn_sizer.Realize()
		main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)
		self.SetSizer(main_sizer)
		self.Layout()
		save_btn.SetDefault()
		self.name_ctrl.SetFocus()

	def _on_save(self, event):
		"""Handle save button."""
		name = self.name_ctrl.GetValue().strip()
		if not name:
			self.status_text.SetLabel("Please enter a template name")
			return
		self.template_name = name
		self.EndModal(wx.ID_OK)

	def _on_cancel(self, event):
		"""Handle cancel button."""
		self.EndModal(wx.ID_CANCEL)

	def get_template_name(self):
		"""Get the entered template name."""
		return self.template_name


class LoadTemplateDialog(wx.Dialog):
	"""Dialog for loading a saved template."""

	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, title="Load Template", size=(500, 400),
						   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.selected_template = None
		self._create_ui()
		self._load_templates()

	def _create_ui(self):
		"""Build the load template dialog UI."""
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		info_label = wx.StaticText(self, label="Select a template to load:")
		main_sizer.Add(info_label, 0, wx.ALL, 8)
		self.template_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		self.template_list.InsertColumn(0, "Name", width=200)
		self.template_list.InsertColumn(1, "Created", width=100)
		self.template_list.InsertColumn(2, "Fields", width=80)
		main_sizer.Add(self.template_list, 1, wx.EXPAND | wx.ALL, 8)
		# Status text
		self.status_text = wx.StaticText(self, label="")
		main_sizer.Add(self.status_text, 0, wx.ALL, 8)
		# Buttons
		btn_sizer = wx.StdDialogButtonSizer()
		load_btn = wx.Button(self, wx.ID_OK, "Load")
		cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		load_btn.Bind(wx.EVT_BUTTON, self._on_load)
		cancel_btn.Bind(wx.EVT_BUTTON, self._on_cancel)
		btn_sizer.AddButton(load_btn)
		btn_sizer.AddButton(cancel_btn)
		btn_sizer.Realize()
		main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)
		self.SetSizer(main_sizer)
		self.Layout()
		load_btn.SetDefault()

	def _load_templates(self):
		"""Load available templates into the list."""
		templates = template_manager.list_templates()
		if not templates:
			self.status_text.SetLabel("No templates found")
			return
		for i, template in enumerate(templates):
			index = self.template_list.InsertItem(i, template["name"])
			self.template_list.SetItem(index, 1, template["created"])
			self.template_list.SetItem(index, 2, str(template["field_count"]))
			self.template_list.SetItemData(index, i)
		self.templates = templates  # Keep reference for loading
		self.status_text.SetLabel(f"Found {len(templates)} templates")

	def _on_load(self, event):
		"""Handle load button."""
		selection = self.template_list.GetFirstSelected()
		if selection == -1:
			self.status_text.SetLabel("Please select a template to load")
			return
		template_index = self.template_list.GetItemData(selection)
		self.selected_template = self.templates[template_index]["filename"]
		self.EndModal(wx.ID_OK)

	def _on_cancel(self, event):
		"""Handle cancel button."""
		self.EndModal(wx.ID_CANCEL)

	def get_selected_template(self):
		"""Get the selected template filename."""
		return self.selected_template


class ManageTemplatesDialog(wx.Dialog):
	"""Dialog for managing existing templates."""

	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, title="Manage Templates", size=(600, 450),
						   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self._create_ui()
		self._load_templates()

	def _create_ui(self):
		"""Build the template management dialog UI."""
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		info_label = wx.StaticText(self, label="Manage your saved templates:")
		main_sizer.Add(info_label, 0, wx.ALL, 8)
		self.template_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		self.template_list.InsertColumn(0, "Name", width=250)
		self.template_list.InsertColumn(1, "Created", width=120)
		self.template_list.InsertColumn(2, "Fields", width=80)
		main_sizer.Add(self.template_list, 1, wx.EXPAND | wx.ALL, 8)
		action_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.delete_btn = wx.Button(self, label="Delete Selected")
		self.refresh_btn = wx.Button(self, label="Refresh")
		self.delete_btn.Bind(wx.EVT_BUTTON, self._on_delete)
		self.refresh_btn.Bind(wx.EVT_BUTTON, self._on_refresh)
		action_sizer.Add(self.delete_btn, 0, wx.RIGHT, 8)
		action_sizer.Add(self.refresh_btn, 0)
		main_sizer.Add(action_sizer, 0, wx.ALL, 8)
		# Status text
		self.status_text = wx.StaticText(self, label="")
		main_sizer.Add(self.status_text, 0, wx.ALL, 8)
		# Close button
		btn_sizer = wx.StdDialogButtonSizer()
		close_btn = wx.Button(self, wx.ID_OK, "Close")
		close_btn.Bind(wx.EVT_BUTTON, self._on_close)
		btn_sizer.AddButton(close_btn)
		btn_sizer.Realize()
		main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)
		self.SetSizer(main_sizer)
		self.Layout()

	def _load_templates(self):
		"""Load available templates into the list."""
		self.template_list.DeleteAllItems()
		templates = template_manager.list_templates()
		if not templates:
			self.status_text.SetLabel("No templates found")
			self.delete_btn.Enable(False)
			return
		for i, template in enumerate(templates):
			index = self.template_list.InsertItem(i, template["name"])
			self.template_list.SetItem(index, 1, template["created"])
			self.template_list.SetItem(index, 2, str(template["field_count"]))
			self.template_list.SetItemData(index, i)
		self.templates = templates  # Keep reference
		self.status_text.SetLabel(f"Found {len(templates)} templates")
		self.delete_btn.Enable(True)

	def _on_delete(self, event):
		"""Handle delete button."""
		selection = self.template_list.GetFirstSelected()
		if selection == -1:
			self.status_text.SetLabel("Please select a template to delete")
			return
		template_index = self.template_list.GetItemData(selection)
		template = self.templates[template_index]
		dlg = wx.MessageDialog(self, 
							   f"Are you sure you want to delete the template '{template['name']}'?",
							   "Confirm Deletion",
							   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			if template_manager.delete_template(template["filename"]):
				self.status_text.SetLabel(f"Template '{template['name']}' deleted successfully")
				self._load_templates()  # Refresh list
			else:
				self.status_text.SetLabel(f"Failed to delete template '{template['name']}'")
		dlg.Destroy()

	def _on_refresh(self, event):
		"""Handle refresh button."""
		self._load_templates()

	def _on_close(self, event):
		"""Handle close button."""
		self.EndModal(wx.ID_OK)
