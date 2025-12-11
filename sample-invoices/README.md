# Sample Invoices

This directory contains sample invoice PDFs that can be used to test the invoice extraction system.

## Available Sample Invoices

1. **invoice_standard.pdf** - Standard invoice format with 2 line items
2. **invoice_services.pdf** - Service-based invoice (Acme Corporation)
3. **invoice_multiple_items.pdf** - Invoice with 3 line items (Tech Solutions Inc.)
4. **invoice_trading.pdf** - Trading company invoice with widget packages
5. **invoice_simple.pdf** - Simple single-item invoice (Small Business LLC)

## Usage

1. Start the application: `docker-compose up`
2. Navigate to http://localhost:3000
3. Drag and drop any of these PDF files onto the upload area
4. The system will extract structured data from the invoice
5. Review and edit the extracted information as needed

## Generating More Samples

To generate additional sample invoices:

```bash
cd backend
python generate_sample_invoices.py
```

This will create new sample invoices in the `sample-invoices/` directory.

## Testing Different Formats

These sample invoices demonstrate:

- Different invoice layouts
- Various line item counts (1-5 items)
- Different customer types (corporations, small businesses)
- Service vs. product invoices
- Different pricing structures

Use these to verify the AI extraction works correctly across different invoice formats.
