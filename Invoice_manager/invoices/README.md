# Invoices Directory

This directory is where you should place your invoice files for processing by the Invoice Manager.

## Supported File Types

The following file types are supported:
- PDF documents (`.pdf`)
- JPG/JPEG images (`.jpg`, `.jpeg`)
- PNG images (`.png`)
- TIFF images (`.tiff`, `.tif`)

## Tips for Best Results

1. **Use high-quality scans**: Higher resolution images (300 DPI or greater) will yield better OCR results.

2. **Keep files clean**: Make sure your invoice files are:
   - Not skewed or rotated
   - Free from major noise or artifacts
   - Well-lit with good contrast between text and background

3. **Use consistent naming**: Consider using a consistent naming pattern for your files (e.g., `YYYY-MM-DD_VendorName.pdf`) to easily track processed invoices.

## Processing Your Invoices

Once you've placed your invoice files in this directory, you can process them using:

```bash
# Process a single invoice
python -m src.main process invoices/my_invoice.pdf -o output/result.json

# Process all invoices in this directory
python -m src.main batch invoices/ -o output/ -f json
```

The processed results will be saved to the `output/` directory.

## Sample Invoices

If you need sample Spanish invoices for testing, consider:
- Creating samples from publicly available templates
- Using test invoices provided by accounting software
- Creating your own test invoices with realistic Spanish invoice fields

**Note**: Please do not place sensitive or confidential invoice data in this directory if you plan to share or distribute this code. 