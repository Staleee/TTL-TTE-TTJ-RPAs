# Quick Start Guide

## Current Status

✅ **Code**: Fully implemented and ready  
✅ **Dependencies**: Installed  
⚠️ **ChromeDriver**: Needs installation  

## Install ChromeDriver (Choose ONE method)

### Method 1: Direct Download (Recommended)

1. **Download ChromeDriver**: Open this link in your browser:
   ```
   https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.87/mac-arm64/chromedriver-mac-arm64.zip
   ```

2. **Extract the ZIP file** (double-click in Finder or use terminal):
   ```bash
   cd ~/Downloads
   unzip chromedriver-mac-arm64.zip
   ```

3. **Move to project** (replace the path if your project is elsewhere):
   ```bash
   mkdir -p /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA/bin
   mv chromedriver-mac-arm64/chromedriver /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA/bin/
   chmod +x /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA/bin/chromedriver
   ```

4. **Remove quarantine** (macOS security):
   ```bash
   xattr -d com.apple.quarantine /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA/bin/chromedriver
   ```

### Method 2: Install Homebrew + ChromeDriver

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ChromeDriver
brew install chromedriver

# Remove quarantine
xattr -d com.apple.quarantine $(which chromedriver)
```

### Method 3: Use Firefox Instead

If Chrome installation is problematic, I can modify the code to use Firefox (geckodriver). Let me know!

## Test the Installation

Once ChromeDriver is installed, test it:

```bash
cd /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA

# Quick test
./bin/chromedriver --version

# Or if installed via Homebrew:
chromedriver --version
```

You should see something like: `ChromeDriver 131.0.6778.87`

## Run the Automation

```bash
cd /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA
python3 main.py
```

**What will happen:**
1. ✅ Browser opens automatically
2. ✅ Navigates to Egypt visa form
3. ✅ Fills all fields from `data/sample_application.json`
4. ✅ Generates PDF
5. ✅ Saves to `output/John_Smith_[timestamp].pdf`
6. ✅ Creates logs in `logs/`
7. ✅ Browser closes

## Troubleshooting

### "chromedriver cannot be opened" error

Run this:
```bash
xattr -d com.apple.quarantine /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA/bin/chromedriver
```

### Still having issues?

You can manually download and place ChromeDriver:
1. Go to: https://googlechromelabs.github.io/chrome-for-testing/
2. Find your Chrome version: `Chrome > About Google Chrome`
3. Download matching ChromeDriver for `mac-arm64`
4. Extract and place in `/Users/saharsabbagh/Desktop/Egypt_visa_form_RPA/bin/`
5. Make executable: `chmod +x bin/chromedriver`

## What's Next?

Once ChromeDriver works:

1. **Customize data**: Edit `data/sample_application.json` with real info
2. **Add more applications**: Create multiple JSON files in `data/`
3. **Run batch**: `python3 main.py` processes all applications
4. **Check output**: PDFs in `output/`, logs in `logs/`

---

Need help? Check:
- `README.md` - Full documentation
- `SETUP_INSTRUCTIONS.md` - Detailed setup
- `logs/` folder - Error details

