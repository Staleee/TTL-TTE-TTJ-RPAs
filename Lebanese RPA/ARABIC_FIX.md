# Arabic Text Display Fix

## Problem
The `accompanied_by_arabic` field was not displaying in the generated PDF because:
1. The code used macOS-specific font paths that don't exist on Railway's Linux servers
2. Exception handling silently failed, causing the Arabic text to not render

## Solution Implemented

### 1. Updated `fill_visa_form.py`
Modified the `insert_arabic_text()` function to:
- Try multiple font sources in order (macOS → Linux → PyMuPDF built-in)
- Add verbose logging to track which font is used
- Proper fallback handling with error messages

### 2. Cross-Platform Font Fallback
The code now uses a smart fallback system that works on any platform:
- Tries system fonts (macOS, Linux) first
- Falls back to PyMuPDF's built-in "figo" font which supports Unicode/Arabic
- Railway deployment uses built-in fonts (no custom installation needed)

## How It Works

The system now tries fonts in this order:
1. **macOS fonts** (local development):
   - GeezaPro.ttc
   - SFArabic.ttf

2. **Linux fonts** (Railway production):
   - DejaVuSans.ttf
   - LiberationSans-Regular.ttf
   - NotoSansArabic-Regular.ttf
   - FreeSans.ttf

3. **PyMuPDF built-in** (fallback):
   - figo font

4. **Last resort** (won't render Arabic correctly):
   - Helvetica

## Testing

### Local Test (macOS)
```bash
python3 fill_visa_form.py --output output/test_arabic.pdf
```

Output should show:
```
✓ Arabic text inserted using: {'fontfile': '/System/Library/Fonts/GeezaPro.ttc', 'fontname': 'GeezaPro'}
```

### Railway Test
After deployment, test with:
```bash
curl -X POST https://your-app.railway.app/generate \
  -H "Content-Type: application/json" \
  -d @visa_applicant_data.json \
  --output test.pdf
```

Check the Railway logs for font selection message.

## Arabic Text Format

The field expects Arabic text in the `visa_applicant_data.json`:
```json
{
  "accompanied_by_arabic": "اسم المرافق"
}
```

The system automatically:
1. Adds the prefix "ﺑﻤﺮاﻓﻘﺔ  " (meaning "accompanied by")
2. Reshapes Arabic text for proper letter connections
3. Applies bidirectional algorithm for right-to-left display

## Files Modified
- ✅ `fill_visa_form.py` - Enhanced Arabic font handling with cross-platform support
- ✅ `railway.json` - Railway deployment configuration (uses auto-detection)

## Deployment

1. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "Fix Arabic text display with cross-platform font support"
   git push origin main
   ```

2. **Railway auto-deploys** with new font configuration

3. **Verify in logs** - Look for:
   - "✓ Arabic text inserted using: ..."

## Current Arabic Value

⚠️ **Note**: The current value in `visa_applicant_data.json` is:
```json
"accompanied_by_arabic": " يسسي"
```

This appears to be placeholder or test text. Update it with the actual Arabic name you want to display.

---

**Status**: ✅ Fixed and ready for deployment
**Date**: January 15, 2026

