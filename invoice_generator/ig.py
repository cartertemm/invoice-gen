import wx
import wx.adv
from datetime import date
from .invoice_api import *
from .config import config
from .speech import speak
from .templates import template_manager
from .template_dialogs import SaveTemplateDialog, LoadTemplateDialog, ManageTemplatesDialog
from .utils import parse_wx_date_to_python, python_date_to_wx_date


class OptionsDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, title="Options", size=(400, 200), 
						   style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self._create_ui()
		self._load_settings()

	def _create_ui(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		api_box = wx.StaticBoxSizer(wx.StaticBox(self, label="API Configuration"), wx.VERTICAL)
		api_label = wx.StaticText(self, label="API Key:")
		self.api_key_ctrl = wx.TextCtrl(self, size=(300, -1), style=wx.TE_PASSWORD)
		self.api_key_ctrl.SetToolTip("Get your API key from invoice-generator.com Settings page")
		show_key_btn = wx.Button(self, label="Show/Hide", size=(80, -1))
		show_key_btn.Bind(wx.EVT_BUTTON, self._on_toggle_password)
		api_row = wx.BoxSizer(wx.HORIZONTAL)
		api_row.Add(api_label, 0)
		api_row.Add(self.api_key_ctrl, 1, wx.EXPAND | wx.RIGHT, 8)
		api_row.Add(show_key_btn, 0)
		api_box.Add(api_row, 0, wx.EXPAND | wx.ALL, 4)
		self.status_text = wx.StaticText(self, label="")
		api_box.Add(self.status_text, 0, wx.ALL, 4)
		main_sizer.Add(api_box, 0, wx.EXPAND | wx.ALL, 12)
		btn_sizer = wx.StdDialogButtonSizer()
		ok_btn = wx.Button(self, wx.ID_OK, "OK")
		cancel_btn = wx.Button(self, wx.ID_CANCEL, "Cancel")
		ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
		cancel_btn.Bind(wx.EVT_BUTTON, self._on_cancel)
		btn_sizer.AddButton(ok_btn)
		btn_sizer.AddButton(cancel_btn)
		btn_sizer.Realize()
		main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 12)
		self.SetSizer(main_sizer)
		self.Layout()
		ok_btn.SetDefault()

	def _load_settings(self):
		api_key = config.get('api_key')
		if api_key:
			self.api_key_ctrl.SetValue(api_key)
			self.status_text.SetLabel("API key loaded from saved settings")
		else:
			self.status_text.SetLabel("No API key saved")

	def _on_toggle_password(self, event):
		current_style = self.api_key_ctrl.GetWindowStyle()
		if current_style & wx.TE_PASSWORD:
			new_style = current_style & ~wx.TE_PASSWORD
		else:
			new_style = current_style | wx.TE_PASSWORD
		value = self.api_key_ctrl.GetValue()
		insertion_point = self.api_key_ctrl.GetInsertionPoint()
		parent = self.api_key_ctrl.GetParent()
		size = self.api_key_ctrl.GetSize()
		pos = self.api_key_ctrl.GetPosition()
		self.api_key_ctrl.Destroy()
		self.api_key_ctrl = wx.TextCtrl(parent, size=size, style=new_style)
		self.api_key_ctrl.SetValue(value)
		self.api_key_ctrl.SetInsertionPoint(insertion_point)
		self.Layout()

	def _on_ok(self, event):
		api_key = self.api_key_ctrl.GetValue().strip()
		if api_key:
			config.set('api_key', api_key)
			self.status_text.SetLabel("API key saved successfully")
		else:
			config.delete('api_key')
			self.status_text.SetLabel("API key cleared")
		self.EndModal(wx.ID_OK)

	def _on_cancel(self, event):
		self.EndModal(wx.ID_CANCEL)


class EditableListCtrl(wx.ListCtrl):
	def __init__(self, parent):
		wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT)
		self.InsertColumn(0, "Name", width=120)
		self.InsertColumn(1, "Description", width=150)
		self.InsertColumn(2, "Quantity", width=70)
		self.InsertColumn(3, "Unit cost", width=90)
		self.InsertColumn(4, "Discount", width=90)

	def add_item(self, item=None):
		if not item:
			return False
		if not item.get('name') or item.get('unit_cost') is None or item.get('unit_cost') <= 0:
			return False
		index = self.GetItemCount()
		name = item['name'] if item and 'name' in item else ''
		desc = item['description'] if item and 'description' in item else ''
		qty = str(item['quantity']) if item and 'quantity' in item else '1'
		cost = str(item['unit_cost']) if item and 'unit_cost' in item else ''
		disc = str(item['discount']) if item and 'discount' in item and item['discount'] is not None else ''
		self.InsertItem(index, name)
		self.SetItem(index, 1, desc)
		self.SetItem(index, 2, qty)
		self.SetItem(index, 3, cost)
		self.SetItem(index, 4, disc)
		return True

	def remove_selected(self):
		index = self.GetFirstSelected()
		if index >= 0:
			self.DeleteItem(index)

	def get_items(self):
		items = []
		count = self.GetItemCount()
		for idx in range(count):
			name = self.GetItemText(idx)
			if not name.strip():
				continue
			description = self.GetItem(idx, 1).GetText()
			try:
				qty_text = self.GetItem(idx, 2).GetText()
				cost_text = self.GetItem(idx, 3).GetText()
				if not cost_text.strip():
					continue
				qty = int(qty_text or 1)
				cost = float(cost_text)
				if qty <= 0 or cost <= 0:
					continue
			except ValueError:
				continue
			disc = self.GetItem(idx, 4).GetText()
			try:
				discount = float(disc) if disc else None
				if discount is not None and discount < 0:
					discount = None
			except ValueError:
				discount = None
			item = {'name': name, 'quantity': qty, 'unit_cost': cost}
			if description.strip():
				item['description'] = description
			if discount is not None:
				item['discount'] = discount
			items.append(item)
		return items


class InvoiceFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="Invoice Generator", size=(700, 800))
		self.panel = wx.Panel(self)
		self.fields = {}
		self._setup_field_definitions()
		self._create_menu()
		self._build_ui()

	def _create_menu(self):
		menubar = wx.MenuBar()
		file_menu = wx.Menu()
		options_item = file_menu.Append(wx.ID_ANY, "&Options\tCtrl+O", "Configure application settings")
		file_menu.AppendSeparator()
		template_menu = wx.Menu()
		load_template_item = template_menu.Append(wx.ID_ANY, "&Load Template\tCtrl+L", "Load values from a saved template")
		save_template_item = template_menu.Append(wx.ID_ANY, "&Save as Template\tCtrl+S", "Save current values as a template")
		manage_templates_item = template_menu.Append(wx.ID_ANY, "&Manage Templates", "View and delete existing templates")
		file_menu.AppendSubMenu(template_menu, "&Templates")
		file_menu.AppendSeparator()
		exit_item = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl+Q", "Exit the application")
		menubar.Append(file_menu, "&File")
		self.SetMenuBar(menubar)
		self.Bind(wx.EVT_MENU, self._on_options, options_item)
		self.Bind(wx.EVT_MENU, self._on_load_template, load_template_item)
		self.Bind(wx.EVT_MENU, self._on_save_template, save_template_item)
		self.Bind(wx.EVT_MENU, self._on_manage_templates, manage_templates_item)
		self.Bind(wx.EVT_MENU, self._on_exit, exit_item)

	def _setup_field_definitions(self):
		self.field_configs = {
			'text': {
				'number': {'label': 'Invoice number', 'hint': 'Invoice number (optional)', 'size': (150,-1)},
				'currency': {'label': 'Currency', 'hint': 'ISO 4217 3-digit code (default: USD)', 'size': (80,-1)},
				'payment_terms': {'label': 'Payment terms', 'hint': 'e.g. "NET 30", "Due on receipt"', 'size': (150,-1)},
				'logo': {'label': 'Logo URL', 'hint': 'URL to your company logo image', 'size': (300,-1)},
			},
			'multiline': {
				'from': {'label': 'From (required)', 'hint': 'Your organization billing address and contact info', 'size': (300,80)},
				'to': {'label': 'To (required)', 'hint': 'Entity being billed - name, address, contact', 'size': (300,80)},
				'ship_to': {'label': 'Ship to', 'hint': 'Shipping address (if different from billing)', 'size': (300,60)},
				'notes': {'label': 'Notes', 'hint': 'Extra information not included elsewhere', 'size': (300,60)},
				'terms': {'label': 'Terms & conditions', 'hint': 'Detailed terms and conditions', 'size': (300,80)},
			},
			'numeric': {
				'discounts': {'label': 'Discounts amount', 'hint': 'Subtotal discounts (numbers only)'},
				'tax': {'label': 'Tax amount', 'hint': 'Tax amount (numbers only)'},
				'shipping': {'label': 'Shipping cost', 'hint': 'Shipping cost (numbers only)'},
				'amount_paid': {'label': 'Amount paid', 'hint': 'Amount already paid (for partial payments)'},
			},
			'date': {
				'date': {'label': 'Invoice date', 'hint': 'Invoice date (default: current date)'},
				'due_date': {'label': 'Due date', 'hint': 'Payment due date'},
			},
			'item_inputs': {
				'item_name': {'type': 'text', 'label': 'Item name', 'hint': 'Name of the product or service', 'size': (200,-1)},
				'item_description': {'type': 'text', 'label': 'Description', 'hint': 'Optional item details or description', 'size': (200,-1)},
				'item_quantity': {'type': 'spin', 'label': 'Qty', 'hint': 'Number of units', 'min': 1, 'max': 999999, 'initial': 1, 'size': (80,-1)},
				'item_unit_cost': {'type': 'spin_double', 'label': 'Unit cost', 'hint': 'Price per unit (required)', 'min': 0, 'max': 999999, 'size': (100,-1)},
				'item_discount': {'type': 'spin_double', 'label': 'Discount', 'hint': 'Item discount amount (optional)', 'min': 0, 'max': 999999, 'size': (100,-1)},
			}
		}

	def _create_field_row(self, parent_sizer, field_name, config, field_type):
		if field_type == 'multiline':
			row_sizer = wx.BoxSizer(wx.VERTICAL)
			label = wx.StaticText(self.panel, label=config['label'])
			ctrl = wx.TextCtrl(self.panel, size=config['size'], style=wx.TE_MULTILINE)
			row_sizer.Add(label, 0, wx.BOTTOM, 4)
			row_sizer.Add(ctrl, 0, wx.EXPAND)
		else:
			row_sizer = wx.BoxSizer(wx.HORIZONTAL)
			label = wx.StaticText(self.panel, label=config['label'])
			if field_type == 'text':
				ctrl = wx.TextCtrl(self.panel, size=config['size'])
			elif field_type == 'numeric':
				ctrl = wx.SpinCtrlDouble(self.panel, min=0, max=999999, initial=0, inc=0.01, size=(120,-1))
				ctrl.SetDigits(2)
			elif field_type == 'date':
				ctrl = wx.adv.DatePickerCtrl(self.panel, size=(120,-1))
			row_sizer.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
			row_sizer.Add(ctrl, 1 if field_type == 'text' else 0, wx.EXPAND if field_type == 'text' else 0)
		if 'hint' in config:
			ctrl.SetToolTip(config['hint'])
		self.fields[field_name] = ctrl
		parent_sizer.Add(row_sizer, 0, wx.EXPAND | wx.ALL, 4)
		return ctrl

	def _create_item_input_field(self, parent_sizer, field_name, config):
		"""Create item input controls."""
		ctrl_type = config['type']
		label = wx.StaticText(self.panel, label=config['label'])
		if ctrl_type == 'text':
			ctrl = wx.TextCtrl(self.panel, size=config['size'])
		elif ctrl_type == 'spin':
			ctrl = wx.SpinCtrl(self.panel, min=config['min'], max=config['max'], 
							  initial=config['initial'], size=config['size'])
		elif ctrl_type == 'spin_double':
			ctrl = wx.SpinCtrlDouble(self.panel, min=config['min'], max=config['max'], 
								   initial=0, inc=0.01, size=config['size'])
			ctrl.SetDigits(2)
		ctrl.SetToolTip(config['hint'])
		setattr(self, field_name, ctrl)
		return label, ctrl

	def _create_section(self, parent_sizer, title, field_type):
		"""Create a section with title and fields."""
		if title:
			section_label = wx.StaticText(self.panel, label=title)
			parent_sizer.Add(section_label, 0, wx.ALL, 4)
		for field_name, config in self.field_configs[field_type].items():
			self._create_field_row(parent_sizer, field_name, config, field_type)

	def _build_ui(self):
		"""Build the entire UI using consistent patterns."""
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		form_sizer = wx.BoxSizer(wx.VERTICAL)
		self._create_section(form_sizer, None, 'text')
		self._create_section(form_sizer, None, 'multiline') 
		self._create_section(form_sizer, None, 'numeric')
		self._create_section(form_sizer, None, 'date')
		self._create_display_options(form_sizer)
		self._create_item_section(form_sizer)
		main_sizer.Add(form_sizer, 0, wx.EXPAND | wx.ALL, 12)
		self._create_items_list(main_sizer)
		self._create_generation_controls(main_sizer)
		self.panel.SetSizer(main_sizer)

	def _create_display_options(self, parent_sizer):
		"""Create display options section."""
		section_label = wx.StaticText(self.panel, label="Invoice Display Options")
		parent_sizer.Add(section_label, 0, wx.ALL, 4)
		tax_row = wx.BoxSizer(wx.HORIZONTAL)
		tax_label = wx.StaticText(self.panel, label="Tax display")
		self.tax_field = wx.Choice(self.panel, choices=['Hide', 'Show', 'Percentage'], size=(100,-1))
		self.tax_field.SetSelection(2)
		tax_row.Add(tax_label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
		tax_row.Add(self.tax_field, 0)
		parent_sizer.Add(tax_row, 0, wx.EXPAND | wx.ALL, 4)
		for field_name, label_text in [('discounts_field', 'Show discounts line'), ('shipping_field', 'Show shipping line')]:
			row = wx.BoxSizer(wx.HORIZONTAL)
			label = wx.StaticText(self.panel, label=field_name.replace('_field', '').title())
			checkbox = wx.CheckBox(self.panel, label=label_text)
			setattr(self, field_name, checkbox)
			row.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
			row.Add(checkbox, 0)
			parent_sizer.Add(row, 0, wx.EXPAND | wx.ALL, 4)

	def _create_item_section(self, parent_sizer):
		"""Create item input section."""
		items_label = wx.StaticText(self.panel, label='Invoice Items')
		parent_sizer.Add(items_label, 0, wx.ALL, 4)
		for field_name in ['item_name', 'item_description']:
			config = self.field_configs['item_inputs'][field_name]
			row = wx.BoxSizer(wx.HORIZONTAL)
			label, ctrl = self._create_item_input_field(parent_sizer, field_name, config)
			row.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 8)
			row.Add(ctrl, 1, wx.EXPAND)
			parent_sizer.Add(row, 0, wx.EXPAND | wx.ALL, 4)
		nums_row = wx.BoxSizer(wx.HORIZONTAL)
		for field_name in ['item_quantity', 'item_unit_cost', 'item_discount']:
			config = self.field_configs['item_inputs'][field_name]
			label, ctrl = self._create_item_input_field(parent_sizer, field_name, config)
			nums_row.Add(label, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 4)
			nums_row.Add(ctrl, 0, wx.RIGHT, 8)
		parent_sizer.Add(nums_row, 0, wx.EXPAND | wx.ALL, 4)

	def _create_items_list(self, parent_sizer):
		"""Create items list and controls."""
		items_label = wx.StaticText(self.panel, label="Invoice items")
		parent_sizer.Add(items_label, 0, wx.LEFT | wx.BOTTOM, 10)
		self.listctrl = EditableListCtrl(self.panel)
		parent_sizer.Add(self.listctrl, 0, wx.ALL | wx.EXPAND, 10)
		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		add_btn = wx.Button(self.panel, label="Add Item")
		rem_btn = wx.Button(self.panel, label="Remove Item")
		add_btn.Bind(wx.EVT_BUTTON, self.on_add_item)
		rem_btn.Bind(wx.EVT_BUTTON, self.on_remove_item)
		btn_sizer.Add(add_btn)
		btn_sizer.Add(rem_btn, 0, wx.LEFT, 8)
		parent_sizer.Add(btn_sizer, 0, wx.ALL, 8)

	def _create_generation_controls(self, parent_sizer):
		"""Create generation button and status."""
		gen_btn = wx.Button(self.panel, label="Generate Invoice")
		gen_btn.Bind(wx.EVT_BUTTON, self.on_generate)
		parent_sizer.Add(gen_btn, 0, wx.ALL, 10)
		self.message = wx.StaticText(self.panel, label="", size=(400,25))
		parent_sizer.Add(self.message, 0, wx.ALL | wx.EXPAND, 10)

	def on_add_item(self, event):
		name = self.item_name.GetValue().strip()
		description = self.item_description.GetValue().strip()
		quantity = self.item_quantity.GetValue()
		unit_cost = self.item_unit_cost.GetValue()
		discount = self.item_discount.GetValue()
		if not name:
			self.display("Error: Item name is required")
			return
		if unit_cost <= 0:
			self.display("Error: Unit cost must be greater than 0")
			return
		item = {
			'name': name,
			'quantity': quantity,
			'unit_cost': unit_cost
		}
		if description:
			item['description'] = description
		if discount > 0:
			item['discount'] = discount
		if self.listctrl.add_item(item):
			self.item_name.SetValue("")
			self.item_description.SetValue("")
			self.item_quantity.SetValue(1)
			self.item_unit_cost.SetValue(0)
			self.item_discount.SetValue(0)
			self.display(f"Item added: {item['name']}, cost: {item['unit_cost']}")
		else:
			self.display("Error: Failed to add item")

	def on_remove_item(self, event):
		self.listctrl.remove_selected()

	def _on_options(self, event):
		"""Show options dialog."""
		dialog = OptionsDialog(self)
		result = dialog.ShowModal()
		dialog.Destroy()
		if result == wx.ID_OK:
			self.display("Settings updated")

	def _on_exit(self, event):
		"""Handle exit menu item."""
		self.Close()

	def _on_save_template(self, event):
		"""Handle save template menu item."""
		dialog = SaveTemplateDialog(self)
		result = dialog.ShowModal()
		if result == wx.ID_OK:
			template_name = dialog.get_template_name()
			field_values = self._get_current_field_values()
			if template_manager.save_template(template_name, field_values):
				self.display(f"Template '{template_name}' saved successfully")
			else:
				self.display(f"Failed to save template '{template_name}'")
		dialog.Destroy()

	def _on_load_template(self, event):
		"""Handle load template menu item."""
		dialog = LoadTemplateDialog(self)
		result = dialog.ShowModal()
		if result == wx.ID_OK:
			template_filename = dialog.get_selected_template()
			field_values = template_manager.load_template(template_filename)
			if field_values:
				self._set_field_values(field_values)
				self.display(f"Template loaded successfully")
			else:
				self.display("Failed to load template")
		dialog.Destroy()

	def _on_manage_templates(self, event):
		"""Handle manage templates menu item."""
		dialog = ManageTemplatesDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def on_generate(self, event):
		try:
			sender = self.fields.get('from', wx.TextCtrl()).GetValue().strip()
			recipient = self.fields.get('to', wx.TextCtrl()).GetValue().strip()
			if not sender:
				self.display("Error: 'From' field is required")
				return
			if not recipient:
				self.display("Error: 'To' field is required")
				return
			invoice = create_invoice(sender, recipient)
			raw_items = self.listctrl.get_items()
			if not raw_items:
				item_count = self.listctrl.GetItemCount()
				if item_count > 0:
					# Show what we're actually getting from the list control
					debug_info = []
					for i in range(item_count):
						name = self.listctrl.GetItemText(i)
						cost_text = self.listctrl.GetItem(i, 3).GetText()
						debug_info.append(f"'{name}':'{cost_text}'")
					self.display(f"Error: {item_count} items present but invalid. Data: {', '.join(debug_info)}")
				else:
					self.display("Error: At least one item is required")
				return
			for item_data in raw_items:
				try:
					item = create_item(
						name=item_data['name'],
						quantity=item_data['quantity'],
						unit_cost=item_data['unit_cost'],
						description=item_data.get('description'),
						discount=item_data.get('discount')
					)
					invoice.add_item(item)
				except ValueError as e:
					self.display(f"Error in item '{item_data.get('name', 'Unknown')}': {e}")
					return
			for field_name in self.field_configs['text'].keys():
				value = self.fields[field_name].GetValue().strip()
				if value:
					setattr(invoice, field_name, value)
			multiline_mapping = {'ship_to': 'ship_to', 'notes': 'notes', 'terms': 'terms'}
			for field_name, attr_name in multiline_mapping.items():
				value = self.fields[field_name].GetValue().strip()
				if value:
					setattr(invoice, attr_name, value)
			for field_name in self.field_configs['numeric'].keys():
				value = self.fields[field_name].GetValue()
				if value > 0:
					setattr(invoice, field_name, value)
			for field_name in ['date', 'due_date']:
				date_ctrl = self.fields[field_name]
				date_value = date_ctrl.GetValue()
				if date_value.IsValid():
					py_date = date(date_value.GetYear(), date_value.GetMonth() + 1, date_value.GetDay())
					setattr(invoice, field_name, py_date)
			tax_choice = self.tax_field.GetSelection()
			tax_display = False if tax_choice == 0 else True if tax_choice == 1 else "%"
			invoice.display_fields = DisplayFields(
				tax=tax_display,
				discounts=self.discounts_field.GetValue(),
				shipping=self.shipping_field.GetValue()
			)
			api_key = config.get('api_key')
			api = create_api_client(api_key)
			validation_errors = api.validate_invoice(invoice)
			if validation_errors:
				self.display("Validation errors: " + "; ".join(validation_errors))
				return
			msg = api.generate_pdf(invoice)
			self.display(msg)
		except Exception as e:
			self.display(f"Error: {str(e)}")
			raise

	def display(self, message):
		speak(message)
		self.message.SetLabel(message)

	def _get_current_field_values(self):
		"""Get current values from all form fields."""
		values = {}
		for field_type in ['text', 'multiline']:
			for field_name in self.field_configs[field_type].keys():
				if field_name in self.fields:
					values[field_name] = self.fields[field_name].GetValue()
		for field_name in self.field_configs['numeric'].keys():
			if field_name in self.fields:
				values[field_name] = self.fields[field_name].GetValue()
		for field_name in self.field_configs['date'].keys():
			if field_name in self.fields:
				date_ctrl = self.fields[field_name]
				date_value = date_ctrl.GetValue()
				if date_value.IsValid():
					py_date = date(date_value.GetYear(), date_value.GetMonth() + 1, date_value.GetDay())
					values[field_name] = py_date.isoformat()
		values['tax_display'] = self.tax_field.GetSelection()
		values['discounts_display'] = self.discounts_field.GetValue()
		values['shipping_display'] = self.shipping_field.GetValue()
		return values

	def _set_field_values(self, values):
		"""Set form fields from template values."""
		for field_type in ['text', 'multiline']:
			for field_name in self.field_configs[field_type].keys():
				if field_name in values and field_name in self.fields:
					self.fields[field_name].SetValue(str(values[field_name]))
		for field_name in self.field_configs['numeric'].keys():
			if field_name in values and field_name in self.fields:
				try:
					self.fields[field_name].SetValue(float(values[field_name]))
				except (ValueError, TypeError):
					pass
		for field_name in self.field_configs['date'].keys():
			if field_name in values and field_name in self.fields:
				try:
					if isinstance(values[field_name], str):
						from datetime import datetime
						date_obj = datetime.fromisoformat(values[field_name]).date()
						wx_date = wx.DateTime(date_obj.day, date_obj.month - 1, date_obj.year)
						self.fields[field_name].SetValue(wx_date)
				except (ValueError, TypeError):
					pass
		if 'tax_display' in values:
			try:
				self.tax_field.SetSelection(int(values['tax_display']))
			except (ValueError, TypeError):
				pass
		if 'discounts_display' in values:
			self.discounts_field.SetValue(bool(values['discounts_display']))
		if 'shipping_display' in values:
			self.shipping_field.SetValue(bool(values['shipping_display']))


class InvoiceApp(wx.App):
	def OnInit(self):
		frame = InvoiceFrame()
		frame.Show()
		return True
