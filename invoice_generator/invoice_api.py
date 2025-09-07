from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from enum import Enum
import requests
import json
from .utils import sanitize_filename


class InvoiceFormat(Enum):
	PDF = "pdf"
	UBL = "ubl"


class Currency(Enum):
	USD = "USD"
	EUR = "EUR"
	GBP = "GBP"
	CAD = "CAD"
	AUD = "AUD"
	JPY = "JPY"


class Language(Enum):
	ENGLISH = "en"
	FRENCH = "fr"
	GERMAN = "de"
	SPANISH = "es"
	THAI = "th"


@dataclass
class CustomField:
	name: str
	value: str
	def to_dict(self) -> Dict[str, str]:
		return {"name": self.name, "value": self.value}


@dataclass
class InvoiceItem:
	name: str
	quantity: int
	unit_cost: float
	description: Optional[str] = None
	discount: Optional[float] = None

	def __post_init__(self):
		if not self.name.strip():
			raise ValueError("Item name cannot be empty")
		if self.quantity <= 0:
			raise ValueError("Quantity must be positive")
		if self.unit_cost < 0:
			raise ValueError("Unit cost cannot be negative")
		if self.discount is not None and self.discount < 0:
			raise ValueError("Discount cannot be negative")

	def total_cost(self) -> float:
		subtotal = self.quantity * self.unit_cost
		if self.discount:
			subtotal -= self.discount
		return max(0, subtotal)

	def to_dict(self) -> Dict[str, Any]:
		result = {
			"name": self.name,
			"quantity": self.quantity,
			"unit_cost": self.unit_cost
		}
		if self.description:
			result["description"] = self.description
		if self.discount is not None:
			result["discount"] = self.discount
		return result


@dataclass
class DisplayFields:
	"""Controls which subtotal lines are shown on the invoice."""
	tax: Union[bool, str] = "%"  # True, False, or "%" for percentage
	discounts: bool = False
	shipping: bool = False

	def to_dict(self) -> Dict[str, Union[bool, str]]:
		"""Convert to API format."""
		return {
			"tax": self.tax,
			"discounts": self.discounts,
			"shipping": self.shipping
		}


@dataclass
class Invoice:
	"""Complete invoice data structure."""
	# Required fields
	sender: str  # "from" in API
	recipient: str  # "to" in API
	items: List[InvoiceItem] = field(default_factory=list)
	# Optional identification
	number: Optional[str] = None
	date: Optional[date] = None
	due_date: Optional[date] = None
	# Financial details
	currency: str = "USD"
	tax: float = 0.0
	discounts: float = 0.0
	shipping: float = 0.0
	amount_paid: float = 0.0
	# Contact and shipping
	ship_to: Optional[str] = None
	payment_terms: Optional[str] = None
	# Branding and content
	logo: Optional[str] = None
	notes: Optional[str] = None
	terms: Optional[str] = None
	# Advanced options
	custom_fields: List[CustomField] = field(default_factory=list)
	display_fields: DisplayFields = field(default_factory=DisplayFields)

	def __post_init__(self):
		"""Validate invoice data."""
		if not self.sender.strip():
			raise ValueError("Sender information is required")
		if not self.recipient.strip():
			raise ValueError("Recipient information is required")

	def add_item(self, item: InvoiceItem) -> None:
		"""Add an item to the invoice."""
		self.items.append(item)

	def add_custom_field(self, name: str, value: str) -> None:
		"""Add a custom field to the invoice."""
		self.custom_fields.append(CustomField(name, value))

	def subtotal(self) -> float:
		"""Calculate subtotal of all items."""
		return sum(item.total_cost() for item in self.items)

	def total(self) -> float:
		"""Calculate final total including tax, discounts, shipping."""
		subtotal = self.subtotal()
		total = subtotal + self.tax + self.shipping - self.discounts
		return max(0, total)

	def balance_due(self) -> float:
		"""Calculate remaining balance after payments."""
		return max(0, self.total() - self.amount_paid)

	def to_dict(self) -> Dict[str, Any]:
		"""Convert invoice to API format."""
		data = {
			"from": self.sender,
			"to": self.recipient,
			"items": [item.to_dict() for item in self.items],
			"fields": self.display_fields.to_dict()
		}
		# Add optional fields only if they have values
		optional_fields = {
			"number": self.number,
			"currency": self.currency if self.currency != "USD" else None,
			"payment_terms": self.payment_terms,
			"logo": self.logo,
			"notes": self.notes,
			"terms": self.terms,
			"ship_to": self.ship_to
		}
		# Add non-zero financial fields
		if self.tax > 0:
			data["tax"] = self.tax
		if self.discounts > 0:
			data["discounts"] = self.discounts
		if self.shipping > 0:
			data["shipping"] = self.shipping
		if self.amount_paid > 0:
			data["amount_paid"] = self.amount_paid
		# Add dates if specified
		if self.date:
			data["date"] = self.date.strftime("%Y-%m-%d")
		if self.due_date:
			data["due_date"] = self.due_date.strftime("%Y-%m-%d")
		# Add non-empty optional fields
		for key, value in optional_fields.items():
			if value:
				data[key] = value
		# Add custom fields if any
		if self.custom_fields:
			data["custom_fields"] = [field.to_dict() for field in self.custom_fields]
		return data


class InvoiceGeneratorAPI:
	"""Client for the invoice-generator.com API."""
	BASE_URL = "https://invoice-generator.com"

	def __init__(self, api_key: str):
		"""
		Initialize the API client.
		Args:
			api_key: API key for authenticated requests.
				This used to be optional but is now required.
		"""
		self.api_key = api_key
		self.session = requests.Session()
		self._setup_headers()

	def _setup_headers(self) -> None:
		"""Configure default headers for API requests."""
		self.session.headers.update({
			"Content-Type": "application/json",
			"User-Agent": "InvoiceGenerator-Python-Client/1.0"
		})
		if self.api_key:
			self.session.headers["Authorization"] = f"Bearer {self.api_key}"

	def _generate_filename(self, invoice: Invoice, extension: str) -> str:
		"""
		Generate filename based on invoice number.
		Args:
			invoice: The invoice data
			extension: File extension (without dot)
		Returns:
			Sanitized filename
		"""
		base_name = "invoice"
		if invoice.number and invoice.number.strip():
			base_name += f"_{invoice.number.strip()}"
		filename = f"{base_name}.{extension}"
		return sanitize_filename(filename)

	def generate_pdf(self, invoice: Invoice, output_path: str = None) -> str:
		"""
		Generate a PDF invoice.
		Args:
			invoice: The invoice data to generate
			output_path: Where to save the PDF file (if None, uses invoice number)
		Returns:
			Success message or error details
		Raises:
			requests.RequestException: On network or API errors
		"""
		if output_path is None:
			output_path = self._generate_filename(invoice, "pdf")
		return self._generate_invoice(invoice, InvoiceFormat.PDF, output_path)

	def generate_ubl(self, invoice: Invoice, output_path: str = None) -> str:
		"""
		Generate an e-invoice in UBL format.
		Args:
			invoice: The invoice data to generate
			output_path: Where to save the UBL XML file (if None, uses invoice number)
		Returns:
			Success message or error details
		Raises:
			requests.RequestException: On network or API errors
		"""
		if output_path is None:
			output_path = self._generate_filename(invoice, "xml")
		return self._generate_invoice(invoice, InvoiceFormat.UBL, output_path)

	def _generate_invoice(self, invoice: Invoice, format_type: InvoiceFormat, output_path: str) -> str:
		"""Internal method to generate invoices."""
		try:
			# Choose endpoint based on format
			url = self.BASE_URL
			if format_type == InvoiceFormat.UBL:
				url += "/ubl"
			# Prepare data
			data = invoice.to_dict()
			# Make request
			response = self.session.post(url, json=data, timeout=30)
			if response.status_code == 200:
				# Save the file
				with open(output_path, 'wb') as f:
					f.write(response.content)
				return f"Invoice saved as {output_path}"
			else:
				return f"Error {response.status_code}: {response.text}"
		except requests.exceptions.Timeout:
			return "Error: Request timed out"
		except requests.exceptions.ConnectionError:
			return "Error: Unable to connect to the API"
		except requests.exceptions.RequestException as e:
			return f"Error: {str(e)}"
		except IOError as e:
			return f"Error saving file: {str(e)}"

	def validate_invoice(self, invoice: Invoice) -> List[str]:
		"""
		Validate an invoice without generating it.
		Args:
			invoice: The invoice to validate
		Returns:
			List of validation errors (empty if valid)
		"""
		errors = []
		# Check for required items
		if not invoice.items:
			errors.append("At least one item is required")
		try:
			# This will raise ValueError for invalid data
			invoice.to_dict()
		except ValueError as e:
			errors.append(str(e))
		if invoice.due_date and invoice.date and invoice.due_date < invoice.date:
			errors.append("Due date cannot be before invoice date")
		if invoice.amount_paid > invoice.total():
			errors.append("Amount paid cannot exceed total")
		return errors

	def get_supported_currencies(self) -> List[str]:
		"""Get list of supported currency codes."""
		return [currency.value for currency in Currency]

	def get_supported_languages(self) -> List[str]:
		"""Get list of supported language codes for localization."""
		return [lang.value for lang in Language]


# Convenience functions for easy usage
def create_invoice(sender: str, recipient: str) -> Invoice:
	"""Create a new invoice with required fields."""
	return Invoice(sender=sender, recipient=recipient)


def create_item(name: str, quantity: int, unit_cost: float, 
			   description: str = None, discount: float = None) -> InvoiceItem:
	"""Create a new invoice item."""
	return InvoiceItem(
		name=name,
		quantity=quantity,
		unit_cost=unit_cost,
		description=description,
		discount=discount
	)


def create_api_client(api_key: str = None) -> InvoiceGeneratorAPI:
	"""Create a new API client instance."""
	return InvoiceGeneratorAPI(api_key=api_key)


# Example usage
if __name__ == "__main__":
	# Create an invoice
	invoice = create_invoice(
		sender="ACME Corp\n123 Business St\nCity, ST 12345",
		recipient="Client Company\n456 Client Ave\nClient City, ST 67890"
	)
	# Add items
	invoice.add_item(create_item("Web Design", 1, 1500.00, "Custom website design"))
	invoice.add_item(create_item("Hosting Setup", 1, 200.00, "Initial hosting configuration"))
	# Set additional details
	invoice.number = "INV-2024-001"
	invoice.date = date.today()
	invoice.payment_terms = "NET 30"
	invoice.tax = 150.00
	# Generate PDF
	api = create_api_client("your-api-key-here")
	result = api.generate_pdf(invoice)
	print(result)
