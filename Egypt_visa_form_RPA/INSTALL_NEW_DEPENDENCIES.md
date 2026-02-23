# Installing New Dependencies for QR Code Fix

## What Changed?

We've enhanced the QR code detection system to ensure it contains **complete and accurate** applicant data. This fix adds intelligent waiting mechanisms that detect when the server has finished processing the form and generating the QR code.

## New Dependencies

The fix requires two additional libraries:

1. **pyzbar** - For decoding QR codes to verify they contain correct data
2. **opencv-python-headless** - For image processing (required by pyzbar)

## Installation Instructions

### Quick Install (Recommended)

Run this command in your terminal:

```bash
cd /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA
pip3 install -r requirements.txt
```

### Manual Install

If the quick install doesn't work, install each package individually:

```bash
pip3 install pyzbar==0.1.9
pip3 install opencv-python-headless==4.8.1.78
```

### Troubleshooting

#### macOS Issues

If you encounter errors installing `pyzbar`, you may need to install `zbar` first:

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install zbar
brew install zbar

# Then install Python packages
pip3 install pyzbar opencv-python-headless
```

#### Linux Issues

On Linux, install system dependencies first:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install libzbar0 libzbar-dev

# Then install Python packages
pip3 install pyzbar opencv-python-headless
```

## Verify Installation

Test that the libraries are installed correctly:

```bash
python3 -c "import cv2; import pyzbar; print('✓ All dependencies installed successfully')"
```

If you see the success message, you're ready to go!

## What's New?

### Enhanced QR Code Detection

- **Network Idle Detection**: Waits for server to finish processing before capturing QR
- **QR Update Detection**: Monitors when QR image source changes (indicates regeneration)
- **QR Validation**: Decodes QR code to verify it contains data
- **Smart Timeouts**: Configurable wait times (default: 30 seconds)
- **Detailed Logging**: See exactly what's happening during form submission

### Configuration Options

New settings in `config/config.json`:

```json
"qr_settings": {
  "wait_timeout": 30,              // Max seconds to wait for QR generation
  "verification_enabled": true,     // Decode QR to verify data
  "network_idle_timeout": 15,      // Max seconds to wait for network idle
  "poll_interval": 1.5,            // Seconds between status checks
  "max_retries": 3                 // Future: retry failed submissions
}
```

## Testing the Fix

Run your normal workflow:

```bash
python3 main.py
```

Watch the logs for new messages:
- `📸 Capturing initial page state...`
- `⏳ Waiting for form submission to complete...`
- `✓ Network activity completed`
- `⏳ Waiting for QR code generation...`
- `✓ QR code updated after X.Xs`
- `🔍 Verifying QR code data...`
- `✅ QR code verified - 1 QR code(s) decoded successfully`

## Optional: Disable QR Verification

If QR decoding causes issues, you can disable it in `config/config.json`:

```json
"qr_settings": {
  "verification_enabled": false
}
```

The system will still use intelligent waiting, but won't decode the QR code.

## Need Help?

If you encounter any issues:
1. Check that all dependencies are installed: `pip3 list | grep -E "pyzbar|opencv"`
2. Review the log files in `logs/` for detailed error messages
3. Check screenshots in `screenshots/` for visual debugging

