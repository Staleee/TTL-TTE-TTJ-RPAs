# Egypt Visa Form RPA Automation

Automated system for filling Egypt consulate visa application forms and generating PDFs.

## Features

- 🤖 **Automated Form Filling**: Fills visa applications using Selenium WebDriver
- 📄 **PDF Generation**: Exports completed forms as PDF documents
- 📦 **Batch Processing**: Process multiple applications from JSON files
- 🔍 **Validation**: Validates application data before submission
- 📊 **Detailed Logging**: Comprehensive logs and error tracking
- 📸 **Screenshots**: Captures screenshots for debugging and verification
- 🔄 **Error Recovery**: Retry logic and graceful error handling

## Project Structure

```
Egypt_visa_form_RPA/
├── main.py                  # Main entry point for batch processing
├── form_automation.py       # Selenium automation logic
├── pdf_generator.py         # PDF generation functionality
├── data_models.py          # Data models and validation
├── requirements.txt        # Python dependencies
├── config/
│   └── config.json         # Configuration and form selectors
├── data/
│   └── sample_application.json  # Example application data
├── output/                 # Generated PDF files (created at runtime)
├── logs/                   # Log files (created at runtime)
└── screenshots/            # Error screenshots (created at runtime)
```

## Requirements

- Python 3.8 or higher
- Google Chrome browser
- Internet connection

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Application Data Format

Create JSON files in the `data/` directory with the following structure:

```json
{
  "personal_info": {
    "first_name": "John",
    "middle_name": "Robert",
    "family_name": "Smith",
    "date_of_birth": "1985-03-15",
    "place_of_birth": "New York",
    "sex": "Male",
    "marital_status": "Married"
  },
  "nationality": {
    "present_nationality": "American",
    "nationality_of_origin": "American"
  },
  "occupation": {
    "occupation_arabic": "مهندس"
  },
  "passport": {
    "passport_number": "123456789",
    "passport_type": "Regular",
    "issued_at": "New York",
    "issued_on": "2020-01-15",
    "expires_on": "2030-01-15"
  },
  "addresses": {
    "permanent_address": "123 Main Street, New York, NY 10001, USA",
    "present_address": "456 Park Avenue, New York, NY 10022, USA"
  },
  "visa_details": {
    "visa_type": "Single",
    "duration_of_stay": "30 days",
    "date_of_arrival": "2026-03-01",
    "purpose_of_visit": "Tourism",
    "address_in_egypt": "Nile Hilton Hotel, Cairo",
    "port_of_entry": "Cairo International Airport"
  },
  "contact": {
    "phone_number": "+1234567890"
  },
  "relatives_in_egypt": [
    {
      "full_name": "Ahmed Mohamed",
      "address": "123 Tahrir Square, Cairo, Egypt"
    }
  ]
}
```

### Field Value Options

- **sex**: `"Male"` or `"Female"`
- **marital_status**: `"Single"`, `"Married"`, `"Widow"`, or `"Widower"`
- **visa_type**: `"Single"` or `"Multiple"`
- **Dates**: Format as `"YYYY-MM-DD"` (e.g., `"2026-03-01"`)

### Browser Configuration

Edit `config/config.json` to customize:

```json
{
  "browser": {
    "headless": false,  // Set to true to run without GUI
    "window_size": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

## Usage

### Batch Processing (Recommended)

Process all JSON files in the `data/` directory:

```bash
python main.py
```

This will:
1. Load all `.json` files from `data/` directory
2. Validate each application
3. Fill forms automatically
4. Generate PDFs in `output/` directory
5. Create detailed logs in `logs/` directory
6. Generate a summary report

### Single Application Test

Test with the sample application:

```bash
python form_automation.py
```

Or validate data only:

```bash
python data_models.py
```

## Output Files

### PDF Files
- Location: `output/`
- Naming: `{FirstName}_{FamilyName}_{timestamp}.pdf`
- Example: `John_Smith_20260115_143022.pdf`

### Log Files
- Location: `logs/`
- Types:
  - `automation_*.log` - Detailed automation logs
  - `batch_*.log` - Batch processing logs
  - `summary_*.json` - Processing summary in JSON format

### Screenshots
- Location: `screenshots/`
- Captured on errors and after form completion
- Naming: `{event}_{name}_{timestamp}.png`

## Troubleshooting

### Chrome Driver Issues
If you encounter ChromeDriver errors:
- The system automatically downloads the correct ChromeDriver version
- Ensure Chrome browser is installed and up to date

### Headless Mode Not Working
Set `"headless": false` in `config/config.json` to see the browser.

### Form Selectors Out of Date
If the website changes, update selectors in `config/config.json`:
```json
{
  "form_selectors": {
    "first_name": "input[name='fname']",
    ...
  }
}
```

### Validation Errors
Check the log files for specific validation errors. All required fields must be populated in your JSON data.

### PDF Generation Issues
If PDF generation fails:
- Check logs for specific errors
- Fallback screenshots will be saved as PNG files
- Ensure sufficient disk space in `output/` directory

## Advanced Usage

### Custom Configuration
Create a custom config file and pass it to the automation:

```python
from pathlib import Path
from form_automation import EgyptVisaFormAutomation

config = Path("my_custom_config.json")
automation = EgyptVisaFormAutomation(config)
```

### Process Specific Files
Modify `main.py` to process specific JSON files instead of all files in the directory.

### Retry Failed Applications
Check `logs/summary_*.json` for failed applications and reprocess them.

## Development

### Running Tests
```bash
# Validate sample data
python data_models.py

# Test form automation (interactive)
python form_automation.py
```

### Adding New Fields
1. Update `data/sample_application.json` with new field
2. Add field to `data_models.py` VisaApplication class
3. Add selector to `config/config.json`
4. Implement filling logic in `form_automation.py`

## Notes

- The automation respects the website structure as of January 2026
- Internet connection required for form submission
- PDF generation uses Chrome DevTools Protocol
- All dates should be in `YYYY-MM-DD` format
- Arabic text supported for occupation field

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review screenshots in `screenshots/` directory
3. Ensure all required fields are populated in JSON data
4. Verify Chrome browser is installed and updated

## License

This automation tool is for legitimate visa application purposes only.

