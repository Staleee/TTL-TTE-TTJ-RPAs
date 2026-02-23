# Setup Instructions

## What We've Built

Your Egypt Visa Form RPA automation is complete! Here's what's ready:

✅ **Data Models** - JSON schema and validation (`data_models.py`)  
✅ **Form Automation** - Selenium-based form filler (`form_automation.py`)  
✅ **PDF Generation** - Export forms as PDFs (`pdf_generator.py`)  
✅ **Batch Processing** - Process multiple applications (`main.py`)  
✅ **Configuration** - Customizable settings (`config/config.json`)  
✅ **Sample Data** - Example application (`data/sample_application.json`)  
✅ **Error Handling** - Comprehensive logging and screenshots  

## Quick Setup (Required)

### 1. Install ChromeDriver

**Option A: Using Homebrew (Recommended for macOS)**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ChromeDriver
brew install chromedriver

# Remove quarantine attribute (macOS security)
xattr -d com.apple.quarantine $(which chromedriver)
```

**Option B: Manual Download**
1. Check your Chrome version: `Google Chrome > About Google Chrome`
2. Download matching ChromeDriver from https://googlechromelabs.github.io/chrome-for-testing/
3. Unzip and move to `/usr/local/bin/`:
   ```bash
   unzip chromedriver-mac-arm64.zip
   sudo mv chromedriver /usr/local/bin/
   sudo chmod +x /usr/local/bin/chromedriver
   sudo xattr -d com.apple.quarantine /usr/local/bin/chromedriver
   ```

**Option C: Use webdriver-manager (Already configured)**
The system will auto-download ChromeDriver when you run it if you have a stable internet connection.

### 2. Verify Installation

```bash
cd /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA
python3 test_simple.py
```

If the browser opens and navigates to the form, you're ready!

## Running the Automation

### Test Data Validation
```bash
python3 data_models.py
```

### Run Single Application (Interactive Test)
```bash
python3 form_automation.py
```
This will fill the sample application. Press Enter when done to close the browser.

### Run Batch Processing
```bash
python3 main.py
```
This processes all `.json` files in the `data/` directory.

## Creating Your Application Data

1. Copy `data/sample_application.json` to a new file
2. Update with real applicant information
3. Save in the `data/` directory
4. Run `python3 main.py`

## Troubleshooting

### ChromeDriver Issues

**Error: "chromedriver cannot be opened because the developer cannot be verified"**
```bash
sudo xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

**Error: "Unable to obtain driver for chrome"**
- Install ChromeDriver using one of the options above
- Verify: `which chromedriver`
- Check Chrome version matches ChromeDriver version

### Network Download Issues (webdriver-manager)

If auto-download fails, manually install ChromeDriver (see Option B above).

### Form Selector Issues

If the website structure changes, update `config/config.json` with new selectors.

To inspect the form:
1. Open https://dubai.egyptconsulates.org/new-forms/visas.html
2. Right-click > Inspect
3. Find form fields and update selectors in config

## Next Steps

1. **Install ChromeDriver** (see options above)
2. **Test the automation**: `python3 test_simple.py`
3. **Update sample data** with real application info
4. **Run the automation**: `python3 main.py`
5. **Check outputs**:
   - PDFs in `output/` folder
   - Logs in `logs/` folder
   - Screenshots in `screenshots/` folder

## Support

All functionality is implemented and ready to use once ChromeDriver is installed!

Check `README.md` for detailed usage instructions.

