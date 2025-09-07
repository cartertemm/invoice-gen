# Invoice Generator

A modern, accessible GUI application for generating professional invoices quickly and easily. Perfect for freelancers, small businesses, and anyone who needs to create one-off invoices without the complexity of a full accounting stack.

## Why Use This?

- **Free and clean**: Generate professional PDFs with no watermarks or tracking pixels
- **Quick setup**: Up and running in minutes with minimal configuration
- **Template system**: Save and reuse invoice templates for regular clients
- **Accessible**: Works seamlessly with screen readers and assistive technology out of the box
- **No subscription needed**: Uses invoice-generator.com's generous free tier (100 invoices/month)

If you find yourself using this application frequently, it might be time to consider upgrading to a full-featured solution like QuickBooks or similar accounting software.

## Features

- Generate professional PDF invoices via invoice-generator.com API
- Support for multiple items with descriptions, quantities, unit costs, and discounts
- Template management: save, load, and manage frequently used configurations
- Accessible design with screen reader support and audio feedback
- Options dialog for API key management
- Tax display modes: Hide, show as amount, or show as percentage
- Real-time validation and error messages

## Getting Started

### Prerequisites
- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. **Install uv** (if you haven't already):
   ```bash
   # On Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and run**:
   ```bash
   git clone https://github.com/cartertemm/invoice-gen.git
   cd invoice-gen
   uv run invoice-gen
   ```

### Getting Your API Key

1. Create a free account at [invoice-generator.com/signup](https://invoice-generator.com/signup)
2. Go to **Settings** in your account dashboard
3. Click **"New API Key"** in the API Keys section
4. Copy the generated key

The free plan includes 100 invoices per month.

### Setting Your API Key

1. Open the application with `uv run invoice-gen`
2. Go to **File → Options** (or press Ctrl+O)
3. Paste your API key and click **OK**

Your API key is stored locally in `config.json`.

## Usage

### Creating Invoices

1. Fill in **From** (your business) and **To** (client) fields (required)
2. Add items with name, quantity, and unit cost
3. Set optional fields: invoice number, dates, tax, shipping, payment terms
4. Click **"Generate Invoice"** to create your PDF

### Templates

- **Save**: File → Templates → Save as Template (Ctrl+S)
- **Load**: File → Templates → Load Template (Ctrl+L)  
- **Manage**: File → Templates → Manage Templates

## Using as a Python Module

```python
from invoice_generator.invoice_api import create_invoice, create_item, create_api_client
from datetime import date

# Create invoice and add items
invoice = create_invoice(
    sender="Your Company\n123 Business St\nCity, ST 12345",
    recipient="Client Name\n456 Client Ave\nClient City, ST 67890"
)
invoice.add_item(create_item("Web Design", 1, 1500.00))

# Generate PDF
api = create_api_client("your-api-key-here")
result = api.generate_pdf(invoice, "invoice.pdf")
```

### Key Methods

- `create_invoice(sender, recipient)` - Create new invoice
- `create_item(name, quantity, unit_cost, description, discount)` - Create invoice item
- `api.generate_pdf(invoice, output_path)` - Generate PDF
- `api.validate_invoice(invoice)` - Validate before generation

## Configuration

The application creates these files:

- `config.json` - API key and settings (do not share)
- `templates/` - Saved invoice templates
- `invoice.pdf` - Default output location

## Troubleshooting

**"Error: API key required"** - Set your key in File → Options

**"Connection error"** - Check internet connection and invoice-generator.com accessibility

**"Validation errors"** - Ensure From/To fields are filled and at least one valid item is added

## License

MIT License. See license file for details.

## Support

- **Issues & Features**: GitHub issue tracker
- **API Questions**: [invoice-generator.com developers](https://invoice-generator.com/developers)