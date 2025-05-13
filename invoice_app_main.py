import os
import sys
import django
import asyncio
import tempfile
import json  # Ensure json is imported
from pathlib import Path
from datetime import datetime
from nicegui import ui

# Add the project root to the path to ensure imports work correctly
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Check if preprocessing is enabled in the config
try:
    from Invoice_manager.src.utils.cfg import ConfigLoader
    config = ConfigLoader().config
    preprocessing_enabled = config["ocr"]["preprocessing"].get("enable_preprocessing", True)
    print(f"Preprocessing enabled: {preprocessing_enabled}")
except Exception as e:
    print(f"Could not load config: {e}")
    preprocessing_enabled = True  # Default to enabled if config can't be loaded

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_project.settings')
try:
    django.setup()
    from invoice_app.models import Invoice
    print("Successfully imported Django models")
except Exception as e:
    print(f"Error setting up Django environment: {e}")
    print("Database integration will be disabled")
    DJANGO_AVAILABLE = False
else:
    DJANGO_AVAILABLE = True

# Import the invoice processing function
try:
    from process_invoice import process_single_invoice
    print("Successfully imported process_single_invoice from process_invoice.py")
except ImportError as e:
    print(f"Warning: Could not import process_single_invoice: {e}")
    print("Using mock function instead for development/testing.")
    
    # Mock function for testing if the real one is not available
    async def mock_process_single_invoice(file_path, use_mistral_structured=False, direct_pdf_processing=True, **kwargs):
        """Mock function that simulates invoice processing"""
        print(f"MOCK: Processing {file_path} with mistral_structured={use_mistral_structured}, direct_pdf={direct_pdf_processing}")
        await asyncio.sleep(3)  # Simulate processing delay
        
        # Get file extension
        file_ext = Path(file_path).suffix.lower()
        
        # Simulate error for testing error handling
        if "error_test" in str(file_path).lower():
            raise ValueError("Simulated OCR error for error_test file")
        
        # Check if file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file size - if it's 0 bytes, raise an error
        if Path(file_path).stat().st_size == 0:
            raise ValueError(f"File {file_path} is empty")
        
        # For PDF files, ensure they're valid
        if file_ext == '.pdf':
            try:
                # Simulate reading PDF content
                with open(file_path, 'rb') as f:
                    first_bytes = f.read(5)
                    # Check if file starts with PDF signature
                    if first_bytes != b'%PDF-':
                        raise ValueError(f"File {file_path} is not a valid PDF file")
            except Exception as e:
                print(f"Error reading PDF: {e}")
                raise ValueError(f"Could not validate PDF file: {e}")
        
        # Return a mock response    
        return {
            "invoice_number": f"MOCK-{Path(file_path).stem[:5]}",
            "issue_date": "01/01/2023",
            "vendor_name": "Mock Vendor Inc.",
            "vendor_tax_id": "B12345678",
            "vendor_address": "123 Mock Street, Mock City",
            "buyer_name": "Mock Buyer Ltd.",
            "buyer_tax_id": "A87654321",
            "taxable_base": "100,00 €",
            "vat_rate": "21%",
            "vat_amount": "21,00 €",
            "total_amount": "121,00 €",
            "metadata": {
                "source_file": Path(file_path).name,
                "ocr_engine": "mock",
                "confidence_score": 0.95
            }
        }
    
    # Use the mock function
    process_single_invoice = mock_process_single_invoice


# Define table columns for invoice display
invoice_table_columns = [
    {'name': 'file_name', 'label': 'File Name', 'field': 'file_name', 'sortable': True, 'align': 'left'},
    {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True, 'align': 'left'},
    {'name': 'uploaded_at', 'label': 'Uploaded At', 'field': 'uploaded_at_formatted', 'sortable': True, 'align': 'left'},
    {'name': 'invoice_number', 'label': 'Invoice No.', 'field': 'invoice_number', 'align': 'left'},
    {'name': 'vendor_name', 'label': 'Vendor', 'field': 'vendor_name', 'align': 'left'},
    {'name': 'total_amount', 'label': 'Total', 'field': 'total_amount', 'align': 'right'},
    {'name': 'actions', 'label': 'Actions', 'field': 'id', 'align': 'center'}
]

# Global variable for the invoice table component
invoice_list_table = None


def format_invoice_for_table(invoice_obj):
    """
    Format an invoice object for display in the table
    
    Args:
        invoice_obj: A Django Invoice model instance
        
    Returns:
        A dictionary with formatted invoice data
    """
    try:
        # Create a minimal row with fallbacks for all values
        result = {
            'id': getattr(invoice_obj, 'id', 0),
            'file_name': 'N/A',
            'status': 'N/A',
            'uploaded_at_formatted': 'N/A',
            'invoice_number': 'N/A',
            'vendor_name': 'N/A',
            'total_amount': 'N/A',
        }
        
        # Print model attributes to debug
        print(f"Invoice object attributes: {dir(invoice_obj)}")
        print(f"Invoice object dict: {invoice_obj.__dict__}")
        
        # Safely get simple fields
        result['file_name'] = getattr(invoice_obj, 'file_name', 'N/A') or 'N/A'
        result['status'] = getattr(invoice_obj, 'status', 'N/A') or 'N/A'
        
        # Handle date field
        try:
            if hasattr(invoice_obj, 'upload_date') and invoice_obj.upload_date:
                result['uploaded_at_formatted'] = invoice_obj.upload_date.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as date_error:
            print(f"Error formatting date: {date_error}")
            
        # Handle extracted_data as JSON
        try:
            extracted_data = getattr(invoice_obj, 'extracted_data', None)
            if extracted_data and isinstance(extracted_data, dict):
                result['invoice_number'] = extracted_data.get('invoice_number', 'N/A')
                result['vendor_name'] = extracted_data.get('vendor_name', 'N/A')
                result['total_amount'] = extracted_data.get('total_amount', 'N/A')
            else:
                print(f"extracted_data is not a dictionary: {type(extracted_data)}")
        except Exception as json_error:
            print(f"Error handling extracted_data: {json_error}")
        
        return result
        
    except Exception as e:
        print(f"Unexpected error formatting invoice: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a safe fallback row
        return {
            'id': getattr(invoice_obj, 'id', 0),
            'file_name': 'Error',
            'status': 'Error',
            'uploaded_at_formatted': 'Error',
            'invoice_number': 'Error',
            'vendor_name': 'Error',
            'total_amount': 'Error',
        }


async def fetch_processed_invoices():
    """
    Fetch invoices from the database
    
    Returns:
        A list of Invoice model instances
    """
    if not DJANGO_AVAILABLE:
        print("Skipping invoice fetch - Django not available")
        return []
    
    try:
        # Use asyncio.to_thread to avoid blocking the UI
        def fetch_invoices():
            try:
                # Debug: print available fields on a model instance
                fields = [f.name for f in Invoice._meta.fields]
                print(f"Available fields in Invoice model: {fields}")
                
                # Check if there are any invoices
                count = Invoice.objects.count()
                print(f"Total invoices in database: {count}")
                
                # Just return without ordering for now (to isolate the issue)
                return list(Invoice.objects.all()[:10])
            except Exception as inner_e:
                print(f"Inner exception in fetch_invoices: {inner_e}")
                import traceback
                traceback.print_exc()
                return []  # Return empty list on any error
        
        print("Calling fetch_invoices via asyncio.to_thread...")
        invoices = await asyncio.to_thread(fetch_invoices)
        print(f"Fetched {len(invoices)} invoices from database")
        return invoices
    except Exception as e:
        print(f"Error in fetch_processed_invoices: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Could not fetch invoices: {e}", type='negative')
        return []


async def update_invoice_table():
    """Update the invoice list table with the latest data from the database"""
    global invoice_list_table
    
    if not invoice_list_table:
        print("Error: Invoice table not initialized yet for update.")
        return
    
    try:
        # Provide test data for debugging
        # This should work even if database access fails
        test_rows = [
            {
                'id': 0,
                'file_name': 'Test Invoice 1',
                'status': 'completed',
                'uploaded_at_formatted': '2023-01-01 12:00:00',
                'invoice_number': 'TEST-001',
                'vendor_name': 'Test Vendor',
                'total_amount': '100.00'
            },
            {
                'id': 1,
                'file_name': 'Test Invoice 2',
                'status': 'failed',
                'uploaded_at_formatted': '2023-01-02 13:00:00',
                'invoice_number': 'TEST-002',
                'vendor_name': 'Another Vendor',
                'total_amount': '200.00'
            }
        ]
        
        try:
            print("Trying to update table with test data first...")
            invoice_list_table.update_rows(test_rows)
            ui.notify('Table initialized with test data', type='info', timeout=1000)
        except Exception as test_error:
            print(f"Error updating table with test data: {test_error}")
            import traceback
            traceback.print_exc()
            
        if not DJANGO_AVAILABLE:
            print("Django not available - using only test data")
            return
            
        # Step 1: Fetch invoices
        try:
            raw_invoices = await fetch_processed_invoices()
            print(f"Raw invoices fetched: {len(raw_invoices)}")
        except Exception as fetch_error:
            print(f"Error fetching invoices: {fetch_error}")
            import traceback
            traceback.print_exc()
            raw_invoices = []
        
        # Step 2: Format each invoice for display, handling errors individually
        formatted_rows = []
        for inv in raw_invoices:
            try:
                formatted = format_invoice_for_table(inv)
                formatted_rows.append(formatted)
            except Exception as format_error:
                print(f"Error formatting invoice {getattr(inv, 'id', 'unknown')}: {format_error}")
                # Continue with other invoices even if one fails
        
        print(f"Formatted {len(formatted_rows)} rows for table display")
        
        # Step 3: Update the table with formatted rows
        if formatted_rows:  # Only update if we have data
            try:
                invoice_list_table.update_rows(formatted_rows)
                ui.notify('Invoice list updated with real data', type='info', timeout=1000)
            except Exception as update_error:
                print(f"Error updating table with real data: {update_error}")
                import traceback
                traceback.print_exc()
                # Fallback to empty table if update fails
                try:
                    invoice_list_table.update_rows([])
                except:
                    pass
        else:
            print("No rows to display in the table")
            try:
                # Keep test data if no real data is available
                pass
            except:
                pass
            
    except Exception as e:
        print(f"Error in update_invoice_table: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        ui.notify(f"Could not update invoice list: {e}", type='negative')


def handle_view_invoice(invoice_id):
    """Handle the view invoice action"""
    ui.notify(f"View action for invoice ID: {invoice_id} (not implemented yet)")


async def save_to_database(filename, content=None, ocr_result=None, status='completed', error_message=None):
    """
    Save invoice processing results to the database.
    
    Args:
        filename: Original filename of the uploaded invoice
        content: The file content (bytes) if available
        ocr_result: Dictionary containing OCR results (or None if processing failed)
        status: Processing status ('completed', 'error', etc.)
        error_message: Error message if processing failed
    
    Returns:
        The created Invoice object or None if database integration is disabled
    """
    if not DJANGO_AVAILABLE:
        print("Skipping database save - Django not available")
        return None
    
    try:
        # We need to handle the file field separately
        # For now, we'll just store the filename
        from django.utils import timezone
        
        # Wrap database operations in asyncio.to_thread to avoid blocking
        def create_invoice():
            # Create the invoice record
            invoice = Invoice(
                file_name=filename,
                status=status,
                extracted_data=ocr_result or {},
                error_message=error_message or ""
            )
            
            # Set processed_date if status is completed or failed
            if status in ['completed', 'failed']:
                invoice.processed_date = timezone.now()
                
            # Save without the file for now
            invoice.save()
            return invoice
            
        invoice = await asyncio.to_thread(create_invoice)
        print(f"Saved invoice record to database with ID: {invoice.id}")
        return invoice
    except Exception as e:
        print(f"Error saving to database: {e}")
        return None


async def handle_invoice_upload(e, result_area):
    """
    Handle the invoice upload event asynchronously.
    
    Args:
        e: The upload event arguments
        result_area: UI element to display processing status and results
    """
    result_area.clear()  # Clear previous results
    temp_file_path = None
    
    try:
        with result_area:
            filename = e.name
            ui.label(f"Processing {filename}...").classes('text-h6 text-center')
            
            # Define OCR pipeline steps with more robust structure
            progress_steps = [
                {
                    'name': "Preparing File", 
                    'state': 'pending', 
                    'time_taken': 0, 
                    'enabled': True,
                    'ui_elements': {},
                    'icon_name': 'hourglass_empty',
                    'icon_color': 'grey'
                },
                {
                    'name': f"Image Preprocessing{' (Disabled)' if not preprocessing_enabled else ''}", 
                    'state': 'pending', 
                    'time_taken': 0, 
                    'enabled': preprocessing_enabled,  # Set based on global config
                    'ui_elements': {},
                    'icon_name': 'hourglass_empty',
                    'icon_color': 'grey'
                },
                {
                    'name': "Performing OCR", 
                    'state': 'pending', 
                    'time_taken': 0, 
                    'enabled': True,
                    'ui_elements': {},
                    'icon_name': 'hourglass_empty',
                    'icon_color': 'grey'
                },
                {
                    'name': "Extracting Structured Data", 
                    'state': 'pending', 
                    'time_taken': 0, 
                    'enabled': True,
                    'ui_elements': {},
                    'icon_name': 'hourglass_empty',
                    'icon_color': 'grey'
                },
                {
                    'name': "Validating Data", 
                    'state': 'pending', 
                    'time_taken': 0, 
                    'enabled': True,
                    'ui_elements': {},
                    'icon_name': 'hourglass_empty',
                    'icon_color': 'grey'
                },
                {
                    'name': "Finalizing", 
                    'state': 'pending', 
                    'time_taken': 0, 
                    'enabled': True,
                    'ui_elements': {},
                    'icon_name': 'hourglass_empty',
                    'icon_color': 'grey'
                }
            ]
            
            # Create progress card
            with ui.card().classes('w-full max-w-md mx-auto q-mb-md'):
                with ui.card_section().classes('bg-primary text-white'):
                    with ui.row().classes('items-center'):
                        ui.spinner(size='sm', color='white').classes('q-mr-sm')
                        ui.label("OCR Processing Pipeline").classes('text-subtitle1')
                
                # Create container for progress steps
                progress_container = ui.column().classes('w-full')
                
                # Add UI elements for each step
                for i, step in enumerate(progress_steps):
                    # Create a row for each step that looks like a list item
                    with ui.row().classes('w-full items-center justify-between py-2 q-px-md border-bottom') as row:
                        # Left side: Step name and icon
                        with ui.row().classes('items-center'):
                            icon = ui.icon(step['icon_name'], color=step['icon_color'])
                            name_label = ui.label(step['name']).classes('q-ml-sm')
                        
                        # Right side: Status
                        status_label = ui.label("Pending...").classes('text-grey')
                    
                    # Store references to UI elements in the step's ui_elements dictionary
                    step['ui_elements'] = {
                        'row': row,
                        'icon': icon,
                        'name_label': name_label,
                        'status_label': status_label
                    }
            
            # Enhanced function to update step status with more options
            async def update_step_status(index, state, time_taken=None, custom_label=None):
                if index < len(progress_steps):
                    step = progress_steps[index]
                    step['state'] = state
                    
                    if state == 'in_progress':
                        step['icon_name'] = 'hourglass_bottom'
                        step['icon_color'] = 'blue'
                        step['ui_elements']['icon'].props(f'name=hourglass_bottom color=blue')
                        step['ui_elements']['status_label'].text = "In progress..."
                        step['ui_elements']['status_label'].classes(replace='text-blue')
                    elif state == 'done':
                        step['icon_name'] = 'check_circle'
                        step['icon_color'] = 'positive'
                        step['ui_elements']['icon'].props(f'name=check_circle color=positive')
                        if custom_label:
                            step['ui_elements']['status_label'].text = custom_label
                        elif time_taken is not None:
                            step['ui_elements']['status_label'].text = f"Done ({time_taken:.2f}s)"
                        else:
                            step['ui_elements']['status_label'].text = "Done"
                        step['ui_elements']['status_label'].classes(replace='text-positive')
                    elif state == 'skipped':
                        step['icon_name'] = 'skip_next'
                        step['icon_color'] = 'blue-grey'
                        step['ui_elements']['icon'].props(f'name=skip_next color=blue-grey')
                        step['ui_elements']['status_label'].text = custom_label or "Skipped"
                        step['ui_elements']['status_label'].classes(replace='text-blue-grey')
                    elif state == 'error':
                        step['icon_name'] = 'error'
                        step['icon_color'] = 'negative'
                        step['ui_elements']['icon'].props(f'name=error color=negative')
                        step['ui_elements']['status_label'].text = custom_label or "Error"
                        step['ui_elements']['status_label'].classes(replace='text-negative')
                    
                    # Small delay for visual effect
                    await asyncio.sleep(0.1)
            
            # Read content from the uploaded file
            content = e.content.read()
            
            # Start file preparation step
            await update_step_status(0, 'in_progress')
            
            # Save to a temporary file with the correct extension
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(content)
                # Explicitly flush the file to ensure it's written to disk
                temp_file.flush()
                os.fsync(temp_file.fileno())
                temp_file_path = Path(temp_file.name)
            
            # Add a small delay to ensure file system operations complete
            await asyncio.sleep(0.5)
            
            # Verify the file exists and has content
            if not temp_file_path.exists():
                raise FileNotFoundError(f"Temporary file {temp_file_path} doesn't exist")
                
            file_size = temp_file_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"Uploaded file is empty (0 bytes)")
                
            print(f"Temporary file created: {temp_file_path} ({file_size} bytes)")
            
            # Mark file preparation as done
            await update_step_status(0, 'done', 0.5)  # Simulated time
            
            # Start image preprocessing step based on configuration
            if preprocessing_enabled:
                await update_step_status(1, 'in_progress')
            else:
                # If preprocessing is disabled, mark as skipped
                await update_step_status(1, 'skipped', custom_label="Skipped (Disabled)")
            
            # Start OCR step - always enabled
            await update_step_status(2, 'in_progress')
            
            # Start timing the OCR process
            ocr_start_time = datetime.now()
            
            # Process the invoice asynchronously
            try:
                if asyncio.iscoroutinefunction(process_single_invoice):
                    # If it's already async
                    ocr_result = await process_single_invoice(
                        str(temp_file_path),
                        use_mistral_structured=True,
                        direct_pdf_processing=True
                    )
                else:
                    # Read a few bytes to verify the file is accessible
                    with open(temp_file_path, 'rb') as f:
                        header = f.read(1024)
                        print(f"File header size: {len(header)} bytes")
                    
                    # Run in a thread pool if it's synchronous
                    ocr_result = await asyncio.to_thread(
                        process_single_invoice,
                        str(temp_file_path),
                        use_mistral_structured=True,
                        direct_pdf_processing=True
                    )
                
                # Calculate total OCR time
                ocr_end_time = datetime.now()
                total_ocr_time = (ocr_end_time - ocr_start_time).total_seconds()
                
                # Get preprocessing status from result metadata if available
                preprocessing_actually_enabled = ocr_result.get('metadata', {}).get('preprocessing_enabled', preprocessing_enabled)
                
                # Confirm preprocessing status to the user
                if preprocessing_actually_enabled != preprocessing_enabled:
                    print(f"Warning: Preprocessing enabled state mismatch - UI: {preprocessing_enabled}, Backend: {preprocessing_actually_enabled}")
                
                # Update progress steps based on total time and preprocessing status
                # Distribute time among steps proportionally
                # If preprocessing was disabled: OCR: 70%, Extraction: 25%, Validation: 5%
                # If preprocessing was enabled: Preprocessing: 10%, OCR: 60%, Extraction: 25%, Validation: 5%
                
                # Preprocessing step may have been skipped or done already
                if preprocessing_actually_enabled:
                    # If enabled and not already marked done, update it now
                    if progress_steps[1]['state'] != 'done':
                        preproc_time = total_ocr_time * 0.10
                        await update_step_status(1, 'done', preproc_time)
                
                # OCR step (always enabled)
                ocr_portion = 0.70 if not preprocessing_actually_enabled else 0.60
                ocr_time = total_ocr_time * ocr_portion
                await update_step_status(2, 'done', ocr_time)
                
                # Extraction step
                extract_time = total_ocr_time * 0.25
                await update_step_status(3, 'done', extract_time)
                
                # Validation step
                validation_time = total_ocr_time * 0.05
                await update_step_status(4, 'done', validation_time)
                
                # Print the OCR result to debug
                print(f"OCR Result type: {type(ocr_result)}")
                print(f"OCR Result content: {ocr_result}")
                
                # Check if OCR result is None or not a dictionary
                if ocr_result is None:
                    raise ValueError("OCR processing returned None. The file may be unreadable or empty.")
                
                if not isinstance(ocr_result, dict):
                    # If it's not a dictionary, create a default dictionary with minimal information
                    print(f"WARNING: OCR result is not a dictionary: {type(ocr_result)}")
                    ocr_result = {
                        "invoice_number": "UNKNOWN",
                        "issue_date": "UNKNOWN",
                        "vendor_name": "UNKNOWN",
                        "total_amount": "UNKNOWN",
                        "metadata": {
                            "source_file": Path(temp_file_path).name,
                            "ocr_engine": "error",
                            "confidence_score": 0.0,
                            "error": f"OCR result is not a dictionary: {type(ocr_result)}"
                        }
                    }
                
                # Start finalizing step
                await update_step_status(5, 'in_progress')
                
                # Save successful results to database
                invoice = await save_to_database(
                    filename=filename,
                    content=content,  # Pass the file content
                    ocr_result=ocr_result,
                    status='completed'
                )
                
                # Mark finalizing as done
                await update_step_status(5, 'done', 0.3)  # Simulated time
                
                # Clear processing messages and show result
                result_area.clear()
                with result_area:
                    ui.notify(f"Successfully processed: {filename}", type='positive')
                    
                    # Notify about database save
                    if DJANGO_AVAILABLE:
                        if invoice:
                            ui.notify(f"OCR data for {filename} saved to database (ID: {invoice.id})", 
                                    type='positive')
                        else:
                            ui.notify(f"Warning: Could not save OCR data to database", 
                                    type='warning')
                    
                    ui.label(f"Results for {filename}").classes('text-h6 q-mt-md text-primary text-center')
                    
                    # Create containers for both display modes
                    invoice_detail_container = ui.column().classes('w-full')
                    with invoice_detail_container:
                        # Create toggle buttons for switching between views
                        with ui.row().classes('w-full justify-end q-mb-sm'):
                            structured_view_btn = ui.button('Structured View', icon='list').props('outline').classes('q-mr-xs')
                            json_view_btn = ui.button('Raw JSON', icon='code').props('outline')
                        
                        # Container for both views (only one visible at a time)
                        invoice_detail_content_area = ui.column().classes('w-full')
                        
                        # Structured view container
                        structured_display_element = ui.column().classes('w-full')
                        with structured_display_element:
                            # Display a card with key invoice details in a structured format
                            with ui.card().classes('w-full q-mb-md shadow-2 max-w-2xl mx-auto'):
                                # Main invoice information section
                                with ui.card_section().classes('bg-primary text-white'):
                                    ui.label("Invoice Details").classes('text-h6')
                                
                                with ui.card_section().classes('q-pa-md'):
                                    # Invoice Details Group
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("Invoice Number:").classes('text-bold')
                                        ui.label(ocr_result.get("invoice_number", "N/A")).classes('text-wrap break-words whitespace-normal')
                                    
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("Issue Date:").classes('text-bold')
                                        ui.label(ocr_result.get("issue_date", "N/A")).classes('text-wrap break-words whitespace-normal')
                                    
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("Due Date:").classes('text-bold')
                                        ui.label(ocr_result.get("due_date", "N/A")).classes('text-wrap break-words whitespace-normal')
                                    
                                    ui.separator().classes('q-my-sm')
                                    
                                    # Vendor information
                                    ui.label("Vendor Information").classes('text-subtitle1 q-mt-sm')
                                    
                                    with ui.row().classes('w-full justify-between items-start'):
                                        ui.label("Vendor Name:").classes('text-bold')
                                        ui.label(ocr_result.get("vendor_name", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                                    
                                    with ui.row().classes('w-full justify-between items-start'):
                                        ui.label("Vendor Tax ID:").classes('text-bold')
                                        ui.label(ocr_result.get("vendor_tax_id", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                                    
                                    if "vendor_address" in ocr_result:
                                        with ui.row().classes('w-full justify-between items-start'):
                                            ui.label("Vendor Address:").classes('text-bold')
                                            ui.label(ocr_result.get("vendor_address", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                                    
                                    ui.separator().classes('q-my-sm')
                                    
                                    # Amounts section
                                    ui.label("Amounts").classes('text-subtitle1 q-mt-sm')
                                    
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("Currency:").classes('text-bold')
                                        ui.label(ocr_result.get("currency", "EUR")).classes('text-wrap break-words whitespace-normal')
                                    
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("Taxable Amount:").classes('text-bold')
                                        ui.label(ocr_result.get("taxable_amount", ocr_result.get("taxable_base", "N/A"))).classes('text-wrap break-words whitespace-normal')
                                    
                                    # VAT information handling both formats
                                    vat_rate = "N/A"
                                    vat_amount = "N/A"
                                    
                                    # Check if we have vat_details (list format)
                                    if "vat_details" in ocr_result and isinstance(ocr_result["vat_details"], list) and len(ocr_result["vat_details"]) > 0:
                                        vat_detail = ocr_result["vat_details"][0]  # Take first VAT detail
                                        vat_rate = f"{vat_detail.get('rate', 'N/A')}%"
                                        vat_amount = vat_detail.get('amount', 'N/A')
                                    else:
                                        # Use simple format if available
                                        vat_rate = ocr_result.get("vat_rate", "N/A")
                                        vat_amount = ocr_result.get("vat_amount", "N/A")
                                    
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("VAT Rate:").classes('text-bold')
                                        ui.label(vat_rate).classes('text-wrap break-words whitespace-normal')
                                    
                                    with ui.row().classes('w-full justify-between'):
                                        ui.label("VAT Amount:").classes('text-bold')
                                        ui.label(vat_amount).classes('text-wrap break-words whitespace-normal')
                                    
                                    with ui.row().classes('w-full justify-between q-mb-md'):
                                        ui.label("Total Amount:").classes('text-bold text-h6')
                                        ui.label(ocr_result.get("total_amount", ocr_result.get("total_eur", "N/A"))).classes('text-h6 text-primary text-wrap break-words whitespace-normal')
                                
                                # Line items section if available
                                if "line_items" in ocr_result and isinstance(ocr_result["line_items"], list) and len(ocr_result["line_items"]) > 0:
                                    with ui.card_section().classes('bg-primary text-white'):
                                        ui.label("Line Items").classes('text-h6')
                                    
                                    with ui.card_section():
                                        # Process line items to ensure text wrapping in description
                                        wrapped_line_items = []
                                        for item in ocr_result["line_items"]:
                                            # Create a copy of the item with the same data
                                            wrapped_item = dict(item)
                                            # Add HTML for wrapping long descriptions if needed
                                            if 'description' in wrapped_item and wrapped_item['description']:
                                                # Ensure the description is properly prepared for display with wrapping
                                                wrapped_item['description'] = wrapped_item['description']
                                            wrapped_line_items.append(wrapped_item)
                                        
                                        # Create a custom table with text wrapping for descriptions
                                        line_items_table = ui.table(columns=[
                                            {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left', 'props': 'style="white-space: normal; word-break: break-all; max-width: 400px;"'},
                                            {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'align': 'center'},
                                            {'name': 'unit_price', 'label': 'Unit Price', 'field': 'unit_price', 'align': 'right'},
                                            {'name': 'line_total', 'label': 'Line Total', 'field': 'line_total', 'align': 'right'}
                                        ], rows=wrapped_line_items, row_key='description').classes('w-full').props('bordered dense wrap-cells')
                                        
                                        # Add custom slot for the description column to enable text wrapping
                                        line_items_table.add_slot('body-cell-description', '''
                                            <q-td :props="props" class="text-wrap break-words" style="max-width: 300px; white-space: normal;">
                                                {{ props.value }}
                                            </q-td>
                                        ''')
                                
                                # Metadata section in an expansion
                                if "metadata" in ocr_result:
                                    with ui.expansion("Processing Metadata", icon="info").classes('w-full q-mt-sm'):
                                        for key, value in ocr_result["metadata"].items():
                                            with ui.row().classes('w-full justify-between items-start'):
                                                ui.label(f"{key.replace('_', ' ').title()}:").classes('text-bold')
                                                if isinstance(value, (dict, list)):
                                                    ui.label(json.dumps(value, default=str)).classes('text-wrap break-words whitespace-normal max-w-70')
                                                else:
                                                    ui.label(str(value)).classes('text-wrap break-words whitespace-normal max-w-70')
                                    
                                    # Show validation errors if present
                                    if "validation_errors" in ocr_result["metadata"] and ocr_result["metadata"]["validation_errors"]:
                                        with ui.expansion("Validation Issues", icon="warning").classes('w-full text-warning'):
                                            for error in ocr_result["metadata"]["validation_errors"]:
                                                ui.label(f"{error.get('path', 'Field')}: {error.get('message', 'Invalid')}").classes('text-caption text-warning text-wrap break-words whitespace-normal')
                        
                        # Raw JSON view container - initially hidden
                        raw_json_display_element = ui.column().classes('w-full')
                        with raw_json_display_element:
                            # Display a card for the raw JSON data
                            with ui.card().classes('w-full q-mb-md shadow-2 max-w-2xl mx-auto'):
                                with ui.card_section().classes('bg-primary text-white'):
                                    ui.label("Raw JSON Data").classes('text-h6')
                                
                                with ui.card_section().classes('q-pa-md'):
                                    # Show the formatted JSON in a scrollable code block
                                    formatted_json = json.dumps(ocr_result, indent=2, default=str)
                                    ui.code(formatted_json, language='json').classes('w-full text-xs whitespace-pre-wrap break-all').style('max-height: 400px; overflow: auto;')
                        
                        # Initially hide the raw JSON view
                        raw_json_display_element.visible = False
                        
                        # Toggle function for the view buttons
                        def toggle_view_to_json():
                            structured_display_element.visible = False
                            raw_json_display_element.visible = True
                            structured_view_btn.props('outline')
                            json_view_btn.props('flat color=primary')
                        
                        def toggle_view_to_structured():
                            structured_display_element.visible = True
                            raw_json_display_element.visible = False
                            structured_view_btn.props('flat color=primary')
                            json_view_btn.props('outline')
                        
                        # Set initial state
                        toggle_view_to_structured()
                        
                        # Connect buttons to toggle functions
                        structured_view_btn.on_click(toggle_view_to_structured)
                        json_view_btn.on_click(toggle_view_to_json)
            
            except Exception as ex:
                # Find which step was in progress when the error occurred
                error_step_index = -1
                for i, step in enumerate(progress_steps):
                    if step['state'] == 'in_progress':
                        error_step_index = i
                        break
                
                # If we found a step in progress, mark it as error
                if error_step_index >= 0:
                    await update_step_status(error_step_index, 'error')
                    
                    # Mark remaining steps as skipped due to error
                    for i in range(error_step_index + 1, len(progress_steps)):
                        await update_step_status(i, 'skipped', custom_label="Skipped (Error)")
                
                # Handle errors
                result_area.clear()
                with result_area:
                    ui.notify(f"Error processing {e.name}: {str(ex)}", type='negative', multi_line=True, close_button='OK')
                    
                    # Create a more detailed error card with better formatting
                    with ui.card().classes('w-full bg-red-50 border-left-4 border-negative'):
                        with ui.card_section().classes('bg-negative text-white'):
                            ui.label(f"Error processing invoice: {e.name}").classes('text-h6')
                        
                        with ui.card_section().classes('q-pa-md'):
                            # Basic error information
                            ui.label(f"Error type: {type(ex).__name__}").classes('text-subtitle1 text-negative')
                            ui.label(f"Error message: {str(ex)}").classes('text-body1 q-mb-md')
                            
                            # Add file information if available
                            if temp_file_path:
                                with ui.expansion('File Information', icon='info').classes('w-full q-mb-md'):
                                    try:
                                        file_size = temp_file_path.stat().st_size if temp_file_path.exists() else "File doesn't exist"
                                        ui.label(f"Temporary file path: {temp_file_path}").classes('text-body2')
                                        ui.label(f"File size: {file_size} bytes").classes('text-body2')
                                        ui.label(f"File exists: {temp_file_path.exists()}").classes('text-body2')
                                        
                                        # Show file header if possible
                                        if temp_file_path.exists() and temp_file_path.stat().st_size > 0:
                                            try:
                                                with open(temp_file_path, 'rb') as f:
                                                    header = f.read(min(1024, temp_file_path.stat().st_size))
                                                    is_pdf = header.startswith(b'%PDF-')
                                                    ui.label(f"Valid PDF header: {is_pdf}").classes('text-body2')
                                            except Exception as read_error:
                                                ui.label(f"Error reading file: {read_error}").classes('text-body2 text-negative')
                                    except Exception as info_error:
                                        ui.label(f"Error getting file info: {info_error}").classes('text-body2 text-negative')
                            
                            # Add detailed traceback
                            with ui.expansion('Technical Details', icon='code').classes('w-full'):
                                import traceback
                                trace_str = traceback.format_exc()
                                ui.html(f"<pre class='text-negative'>{trace_str}</pre>").classes('q-pa-sm bg-grey-2 rounded-borders overflow-auto max-h-96')
                        
                        # Add troubleshooting tips
                        with ui.card_section().classes('bg-grey-3'):
                            ui.label("Troubleshooting Steps:").classes('text-subtitle1')
                            with ui.list().props('dense'):
                                ui.item("Make sure the file is a valid PDF document").classes('text-body2')
                                ui.item("Check that the file is not corrupted or password-protected").classes('text-body2')
                                ui.item("Try with a different PDF file").classes('text-body2')
                                ui.item("Check the file size (should not be empty)").classes('text-body2')
                                if "application/x-empty" in str(ex):
                                    ui.item("The Mistral API received an empty file - this could be a temporary issue").classes('text-body2 text-negative')
                
                print(f"Error processing invoice: {ex}")
                import traceback
                traceback.print_exc()
                
                # Save error to database
                invoice = await save_to_database(
                    filename=e.name,
                    content=content if 'content' in locals() else None,  # Pass content if it was read
                    status='failed',
                    error_message=str(ex)
                )
                
                # Notify about database save
                if DJANGO_AVAILABLE:
                    if invoice:
                        with result_area:
                            ui.notify(f"Error details for {e.name} saved to database (ID: {invoice.id})", 
                                    type='warning')
                    else:
                        with result_area:
                            ui.notify(f"Warning: Could not save error details to database", 
                                    type='warning')
                
                # Update the invoice table after error handling
                await update_invoice_table()
                
    except Exception as ex:
        # Handle errors
        result_area.clear()
        with result_area:
            ui.notify(f"Error processing {e.name}: {str(ex)}", type='negative', multi_line=True, close_button='OK')
            
            # Create a more detailed error card with better formatting
            with ui.card().classes('w-full bg-red-50 border-left-4 border-negative'):
                with ui.card_section().classes('bg-negative text-white'):
                    ui.label(f"Error processing invoice: {e.name}").classes('text-h6')
                
                with ui.card_section().classes('q-pa-md'):
                    # Basic error information
                    ui.label(f"Error type: {type(ex).__name__}").classes('text-subtitle1 text-negative')
                    ui.label(f"Error message: {str(ex)}").classes('text-body1 q-mb-md')
                    
                    # Add file information if available
                    if temp_file_path:
                        with ui.expansion('File Information', icon='info').classes('w-full q-mb-md'):
                            try:
                                file_size = temp_file_path.stat().st_size if temp_file_path.exists() else "File doesn't exist"
                                ui.label(f"Temporary file path: {temp_file_path}").classes('text-body2')
                                ui.label(f"File size: {file_size} bytes").classes('text-body2')
                                ui.label(f"File exists: {temp_file_path.exists()}").classes('text-body2')
                                
                                # Show file header if possible
                                if temp_file_path.exists() and temp_file_path.stat().st_size > 0:
                                    try:
                                        with open(temp_file_path, 'rb') as f:
                                            header = f.read(min(1024, temp_file_path.stat().st_size))
                                            is_pdf = header.startswith(b'%PDF-')
                                            ui.label(f"Valid PDF header: {is_pdf}").classes('text-body2')
                                    except Exception as read_error:
                                        ui.label(f"Error reading file: {read_error}").classes('text-body2 text-negative')
                            except Exception as info_error:
                                ui.label(f"Error getting file info: {info_error}").classes('text-body2 text-negative')
                    
                    # Add detailed traceback
                    with ui.expansion('Technical Details', icon='code').classes('w-full'):
                        import traceback
                        trace_str = traceback.format_exc()
                        ui.html(f"<pre class='text-negative'>{trace_str}</pre>").classes('q-pa-sm bg-grey-2 rounded-borders overflow-auto max-h-96')
                
                # Add troubleshooting tips
                with ui.card_section().classes('bg-grey-3'):
                    ui.label("Troubleshooting Steps:").classes('text-subtitle1')
                    with ui.list().props('dense'):
                        ui.item("Make sure the file is a valid PDF document").classes('text-body2')
                        ui.item("Check that the file is not corrupted or password-protected").classes('text-body2')
                        ui.item("Try with a different PDF file").classes('text-body2')
                        ui.item("Check the file size (should not be empty)").classes('text-body2')
                        if "application/x-empty" in str(ex):
                            ui.item("The Mistral API received an empty file - this could be a temporary issue").classes('text-body2 text-negative')
        
        print(f"Error processing invoice: {ex}")
        import traceback
        traceback.print_exc()
        
        # Save error to database
        invoice = await save_to_database(
            filename=e.name,
            content=content if 'content' in locals() else None,  # Pass content if it was read
            status='failed',
            error_message=str(ex)
        )
        
        # Notify about database save
        if DJANGO_AVAILABLE:
            if invoice:
                with result_area:
                    ui.notify(f"Error details for {e.name} saved to database (ID: {invoice.id})", 
                            type='warning')
            else:
                with result_area:
                    ui.notify(f"Warning: Could not save error details to database", 
                            type='warning')
        
        # Update the invoice table after error handling
        await update_invoice_table()
        
    finally:
        # Clean up the temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                os.unlink(temp_file_path)
                print(f"Deleted temporary file: {temp_file_path}")
            except Exception as ex:
                print(f"Error deleting temporary file {temp_file_path}: {ex}")


@ui.page('/')
async def main_page():
    """Main page of the Invoice OCR application"""
    global invoice_list_table
    
    ui.add_head_html("""
    <style>
    .q-page {
        padding: 24px;
        max-width: 1200px;
        margin: 0 auto;
    }
    .text-wrap {
        white-space: normal;
        word-break: break-word;
        overflow-wrap: break-word;
    }
    .max-w-full {
        max-width: 100%;
    }
    .json-viewer {
        max-height: 400px;
        overflow: auto;
        font-family: monospace;
        background-color: #f5f5f5;
        border-radius: 4px;
    }
    </style>
    """)
    
    with ui.column().classes('w-full items-center'):
        ui.label('Invoice Processing - OCR Integration').classes('text-h3 q-mb-md text-primary')
        
        with ui.card().classes('w-full q-mb-lg max-w-6xl shadow-3'):
            with ui.card_section().classes('bg-primary text-white'):
                ui.label('Overview').classes('text-h5')
            
            with ui.card_section():
                ui.label('This application allows you to upload and process invoice documents using OCR technology.').classes('text-body1')
                ui.label('Supported file formats: PDF, JPG, JPEG, PNG, TIFF').classes('text-caption')
                
                # Show database connection status
                if DJANGO_AVAILABLE:
                    with ui.row().classes('q-mt-sm items-center'):
                        ui.icon('check_circle', color='positive').classes('q-mr-xs')
                        ui.label('Database connection active - results will be saved').classes('text-positive')
                else:
                    with ui.row().classes('q-mt-sm items-center'):
                        ui.icon('warning', color='warning').classes('q-mr-xs')
                        ui.label('Database connection inactive - results will not be saved').classes('text-warning')
        
        # Card for upload functionality
        with ui.card().classes('w-full q-mb-lg max-w-6xl shadow-3'):
            with ui.card_section().classes('bg-primary text-white'):
                ui.label('Upload Invoice').classes('text-h5')
            
            with ui.card_section().classes('q-pa-md'):
                # Upload component
                uploader = ui.upload(
                    label="Select Invoice",
                    on_upload=lambda e: handle_invoice_upload(e, result_area),
                    auto_upload=True,
                    multiple=False,
                    max_file_size=20 * 1024 * 1024,  # 20MB limit
                ).props('accept=".pdf,.jpg,.jpeg,.png,.tiff" color="primary" outlined')
                
                # Result area for displaying status and results
                result_area = ui.column().classes('w-full p-4 border rounded-lg q-mt-md')
                
                with result_area:
                    with ui.row().classes('items-center justify-center w-full q-my-lg text-grey'):
                        ui.icon('cloud_upload', size='lg').classes('q-mr-md')
                        ui.label('Upload an invoice to begin processing').classes('text-body1')
        
        # Section for displaying processed invoices
        with ui.card().classes('w-full max-w-6xl shadow-3'):
            with ui.card_section().classes('bg-primary text-white flex justify-between items-center'):
                ui.label('Processed Invoices').classes('text-h5')
                ui.button("Refresh List", on_click=update_invoice_table, icon="refresh").props('flat dense')
            
            # Create the invoice table - wrap in try/except for safety
            try:
                print("Creating invoice table...")
                invoice_list_table = ui.table(
                    columns=invoice_table_columns,
                    rows=[],
                    row_key='id'
                ).classes('w-full').props('bordered dense')
                
                print("Adding table slot...")
                # Add actions column with view button
                invoice_list_table.add_slot('body-cell-actions', '''
                    <q-td :props="props" style="text-align: center;">
                        <q-btn flat dense round icon="visibility" @click="() => $parent.$emit('view_invoice', props.row.id)" />
                    </q-td>
                ''')
                
                print("Registering handler...")
                # Register handler for view invoice action
                invoice_list_table.on('view_invoice', lambda e: handle_view_invoice(e.args))
                
                print("Setting up table refresh...")
                # Use a timer for initial table load - allows page to fully render first
                ui.timer(0.5, lambda: update_invoice_table(), once=True)
                print("Table setup complete")
            except Exception as table_setup_error:
                print(f"Error setting up invoice table: {table_setup_error}")
                import traceback
                traceback.print_exc()


# Diagnostic function to test Django setup
def test_django_setup():
    if not DJANGO_AVAILABLE:
        print("Django not available - skipping test")
        return
        
    try:
        print("\n----- DJANGO DIAGNOSTICS -----")
        print(f"Django version: {django.get_version()}")
        print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
        
        # Test model access
        try:
            count = Invoice.objects.count()
            print(f"Invoice count: {count}")
            
            if count > 0:
                first = Invoice.objects.first()
                print(f"First invoice: ID={first.id}, file_name={first.file_name}")
                print(f"Model fields: {[f.name for f in Invoice._meta.fields]}")
        except Exception as model_error:
            print(f"Error accessing model: {model_error}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Error in Django diagnostics: {e}")
        import traceback
        traceback.print_exc()
    print("----- END DIAGNOSTICS -----\n")

# Run diagnostics before starting the app
test_django_setup()

# Run the application
ui.run(title="Invoice OCR Processor", reload=False, port=8080)

def view_invoice_modal(invoice_data):
    """Display invoice details in a modal dialog"""
    
    # Extract data from invoice record
    filename = invoice_data.get('file_name', 'Unknown')
    extracted_data = invoice_data.get('extracted_data')
    status = invoice_data.get('status')
    
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
        with ui.card_section().classes('bg-primary text-white'):
            ui.label(f"Invoice Details: {filename}").classes('text-h6')
        
        with ui.card_section():
            if status == 'error':
                ui.label("Error processing invoice").classes('text-negative')
                ui.label(invoice_data.get('error_message', 'Unknown error')).classes('text-caption text-wrap break-words whitespace-normal')
                return
            
            if not extracted_data:
                ui.label("No extracted data available").classes('text-warning')
                return
            
            # Display organized invoice details
            with ui.card().classes('w-full q-mb-md shadow-1'):
                # Main invoice information section
                with ui.card_section().classes('bg-primary text-white'):
                    ui.label("Invoice Details").classes('text-h6')
                
                with ui.card_section().classes('q-pa-md'):
                    # Invoice Details Group
                    with ui.row().classes('w-full justify-between'):
                        ui.label("Invoice Number:").classes('text-bold')
                        ui.label(extracted_data.get("invoice_number", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                    
                    with ui.row().classes('w-full justify-between'):
                        ui.label("Issue Date:").classes('text-bold')
                        ui.label(extracted_data.get("issue_date", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                    
                    with ui.row().classes('w-full justify-between'):
                        ui.label("Due Date:").classes('text-bold')
                        ui.label(extracted_data.get("due_date", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                    
                    ui.separator().classes('q-my-sm')
                    
                    # Vendor information
                    ui.label("Vendor Information").classes('text-subtitle1 q-mt-sm')
                    
                    with ui.row().classes('w-full justify-between items-start'):
                        ui.label("Vendor Name:").classes('text-bold')
                        ui.label(extracted_data.get("vendor_name", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                    
                    with ui.row().classes('w-full justify-between items-start'):
                        ui.label("Vendor Tax ID:").classes('text-bold')
                        ui.label(extracted_data.get("vendor_tax_id", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                    
                    if "vendor_address" in extracted_data:
                        with ui.row().classes('w-full justify-between items-start'):
                            ui.label("Vendor Address:").classes('text-bold')
                            ui.label(extracted_data.get("vendor_address", "N/A")).classes('text-wrap break-words whitespace-normal max-w-70')
                    
                    ui.separator().classes('q-my-sm')
                    
                    # Amounts section
                    ui.label("Amounts").classes('text-subtitle1 q-mt-sm')
                    
                    with ui.row().classes('w-full justify-between'):
                        ui.label("Currency:").classes('text-bold')
                        ui.label(extracted_data.get("currency", "EUR")).classes('text-wrap break-words whitespace-normal')
                    
                    with ui.row().classes('w-full justify-between'):
                        ui.label("Taxable Amount:").classes('text-bold')
                        ui.label(extracted_data.get("taxable_amount", extracted_data.get("taxable_base", "N/A"))).classes('text-wrap break-words whitespace-normal')
                    
                    # VAT information handling both formats
                    vat_rate = "N/A"
                    vat_amount = "N/A"
                    
                    # Check if we have vat_details (list format)
                    if "vat_details" in extracted_data and isinstance(extracted_data["vat_details"], list) and len(extracted_data["vat_details"]) > 0:
                        vat_detail = extracted_data["vat_details"][0]  # Take first VAT detail
                        vat_rate = f"{vat_detail.get('rate', 'N/A')}%"
                        vat_amount = vat_detail.get('amount', 'N/A')
                    else:
                        # Use simple format if available
                        vat_rate = extracted_data.get("vat_rate", "N/A")
                        vat_amount = extracted_data.get("vat_amount", "N/A")
                    
                    with ui.row().classes('w-full justify-between'):
                        ui.label("VAT Rate:").classes('text-bold')
                        ui.label(vat_rate).classes('text-wrap break-words whitespace-normal')
                    
                    with ui.row().classes('w-full justify-between'):
                        ui.label("VAT Amount:").classes('text-bold')
                        ui.label(vat_amount).classes('text-wrap break-words whitespace-normal')
                    
                    with ui.row().classes('w-full justify-between q-mb-md'):
                        ui.label("Total Amount:").classes('text-bold text-h6')
                        ui.label(extracted_data.get("total_amount", extracted_data.get("total_eur", "N/A"))).classes('text-h6 text-primary text-wrap break-words whitespace-normal')
                
                # Line items section if available
                if "line_items" in extracted_data and isinstance(extracted_data["line_items"], list) and len(extracted_data["line_items"]) > 0:
                    with ui.card_section().classes('bg-primary text-white'):
                        ui.label("Line Items").classes('text-h6')
                        
                        with ui.card_section():
                            # Create a custom table for line items with text wrapping
                            line_items_table = ui.table(columns=[
                                {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left', 'props': 'style="white-space: normal; word-break: break-all; max-width: 400px;"'},
                                {'name': 'quantity', 'label': 'Quantity', 'field': 'quantity', 'align': 'center'},
                                {'name': 'unit_price', 'label': 'Unit Price', 'field': 'unit_price', 'align': 'right'},
                                {'name': 'line_total', 'label': 'Line Total', 'field': 'line_total', 'align': 'right'}
                            ], rows=extracted_data["line_items"], row_key='description').classes('w-full').props('bordered dense wrap-cells')
                            
                            # Add custom slot for the description column to enable text wrapping
                            line_items_table.add_slot('body-cell-description', '''
                                <q-td :props="props" class="text-wrap break-words" style="max-width: 300px; white-space: normal;">
                                    {{ props.value }}
                                </q-td>
                            ''')
            
            # Metadata section in an expansion if available
            if "metadata" in extracted_data:
                with ui.expansion("Processing Metadata", icon="info").classes('w-full q-mt-sm'):
                    for key, value in extracted_data["metadata"].items():
                        with ui.row().classes('w-full justify-between items-start'):
                            ui.label(f"{key.replace('_', ' ').title()}:").classes('text-bold')
                            if isinstance(value, (dict, list)):
                                ui.label(json.dumps(value, default=str)).classes('text-wrap break-words whitespace-normal max-w-70')
                            else:
                                ui.label(str(value)).classes('text-wrap break-words whitespace-normal max-w-70')
            
            # Display full JSON data in a collapsible section
            with ui.expansion("Full JSON Data", icon="code").classes('w-full'):
                import json
                formatted_json = json.dumps(extracted_data, indent=2, default=str)
                ui.code(formatted_json, language='json').classes('w-full max-h-96 overflow-auto json-viewer q-mt-sm')
        
        # Footer with close button
        with ui.card_section().classes('bg-grey-2 text-right'):
            ui.button("Close", on_click=dialog.close).props('flat') 