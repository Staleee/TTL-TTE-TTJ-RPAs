# Railway Deployment Guide

## 🚀 Deploy Egypt Visa Form RPA to Railway

This guide will help you deploy your visa form automation as a webhook service on Railway.

---

## 📋 Pre-Deployment Checklist

✅ All deployment files created:
- `app.py` - Flask webhook server
- `Dockerfile` - Container configuration  
- `railway.toml` - Railway settings
- `requirements.txt` - Updated with Flask/Gunicorn
- `.dockerignore` - Exclude unnecessary files
- `.gitignore` - Git ignore rules
- `form_automation.py` - Updated for headless mode

---

## 🔧 Step 1: Initialize Git Repository

```bash
cd /Users/saharsabbagh/Desktop/Egypt_visa_form_RPA

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Egypt Visa Form RPA with webhook support"
```

---

## 🌐 Step 2: Push to GitHub

```bash
# Create a new repository on GitHub first, then:

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/egypt-visa-rpa.git

# Push
git branch -M main
git push -u origin main
```

---

## 🚂 Step 3: Deploy to Railway

### Option A: Deploy from GitHub (Recommended)

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select your `egypt-visa-rpa` repository
6. Railway will:
   - Auto-detect the Dockerfile
   - Build the container
   - Deploy your service
   - Assign a public URL

### Option B: Deploy from CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

## 🌍 Step 4: Get Your Webhook URL

After deployment, Railway will give you a URL like:
```
https://egypt-visa-rpa-production.up.railway.app
```

Your webhook endpoints will be:
- **Health Check**: `https://your-app.railway.app/health`
- **Generate PDF**: `https://your-app.railway.app/generate-visa-pdf`
- **API Docs**: `https://your-app.railway.app/`

---

## 🧪 Step 5: Test Your Webhook

### Test Health Endpoint

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Egypt Visa Form RPA",
  "timestamp": "2026-01-16T14:00:00.000000"
}
```

### Test PDF Generation

```bash
curl -X POST https://your-app.railway.app/generate-visa-pdf \
  -H "Content-Type: application/json" \
  -d '{
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
  }' \
  --output test_visa.pdf
```

---

## 📡 Using the Webhook in Your Application

### Python Example

```python
import requests

def generate_visa_pdf(application_data, output_path='visa.pdf'):
    """
    Generate visa PDF via Railway webhook
    
    Args:
        application_data: dict with visa application data
        output_path: where to save the PDF
    
    Returns:
        True if successful, False otherwise
    """
    url = 'https://your-app.railway.app/generate-visa-pdf'
    
    try:
        response = requests.post(
            url,
            json=application_data,
            timeout=120  # 2 minutes timeout
        )
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ PDF saved to {output_path}")
            return True
        else:
            error = response.json()
            print(f"Error: {error}")
            return False
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False

# Usage
data = {
    "personal_info": {
        "first_name": "John",
        # ... rest of data
    }
}

generate_visa_pdf(data, 'john_smith_visa.pdf')
```

### JavaScript/Node.js Example

```javascript
const fetch = require('node-fetch');
const fs = require('fs');

async function generateVisaPDF(applicationData, outputPath = 'visa.pdf') {
    const url = 'https://your-app.railway.app/generate-visa-pdf';
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(applicationData),
            timeout: 120000  // 2 minutes
        });
        
        if (response.ok) {
            const buffer = await response.buffer();
            fs.writeFileSync(outputPath, buffer);
            console.log(`✓ PDF saved to ${outputPath}`);
            return true;
        } else {
            const error = await response.json();
            console.error('Error:', error);
            return false;
        }
    } catch (error) {
        console.error('Request failed:', error);
        return false;
    }
}

// Usage
const data = {
    personal_info: {
        first_name: 'John',
        // ... rest of data
    }
};

generateVisaPDF(data, 'john_smith_visa.pdf');
```

---

## 🔍 Monitoring & Debugging

### View Logs in Railway

1. Go to your Railway project
2. Click on your service
3. Click "Deployments"
4. Click on the active deployment
5. View real-time logs

### Common Issues

**Issue**: "PDF generation failed"
- Check logs for Selenium errors
- Verify Chrome/ChromeDriver compatibility
- Ensure headless mode is working

**Issue**: "Timeout errors"
- Increase timeout in `railway.toml` (currently 300s)
- Check if form website is accessible

**Issue**: "Out of memory"
- Railway free tier has 512MB RAM limit
- Upgrade to Hobby plan ($5/month) for 8GB RAM

---

## ⚙️ Configuration

### Environment Variables (Optional)

In Railway dashboard, you can set:

- `PORT` - Automatically set by Railway (8080)
- `RAILWAY_ENVIRONMENT` - Automatically set to `production`
- Custom variables if needed

### Scaling

Railway auto-scales based on your plan:
- **Free**: 1 instance, 512MB RAM
- **Hobby ($5/mo)**: 1 instance, 8GB RAM  
- **Pro ($20/mo)**: Multiple instances, 32GB RAM

---

## 📊 Performance Notes

- **Cold Start**: First request may take 10-20 seconds (container startup)
- **Warm**: Subsequent requests ~30-40 seconds
- **Concurrent**: 1 worker = 1 request at a time (Selenium limitation)
- **Scaling**: For multiple concurrent requests, deploy multiple instances

---

## 💰 Cost Estimate

- **Railway Free Tier**: 500 hours/month free
- **Hobby Plan**: $5/month for 8GB RAM (recommended)
- **Execution Time**: ~40s per PDF = ~90 PDFs per hour
- **Monthly**: ~65,000 PDFs on Hobby plan

---

## 🔒 Security Recommendations

1. **Add Authentication**: Protect your endpoint with API keys
2. **Rate Limiting**: Prevent abuse
3. **Input Validation**: Already included in `data_models.py`
4. **HTTPS**: Automatically provided by Railway
5. **Private Networking**: Use Railway's private networking for backend calls

---

## 🎯 What's Included

✅ QR Code Fix - Intelligent waiting for complete data
✅ Headless Chrome - Runs without display
✅ Error Handling - Graceful failures with detailed errors
✅ Health Checks - Railway monitors service health
✅ Auto-scaling - Railway handles traffic spikes
✅ Logging - Full request/response logging
✅ PDF in Response - Direct download from webhook

---

## 📞 Support

If you encounter issues:

1. Check Railway logs
2. Test locally with: `python app.py`
3. Verify Dockerfile builds: `docker build -t visa-rpa .`
4. Check GitHub Issues: Your repository issues

---

## 🎉 You're Ready!

Your Egypt Visa Form RPA is now deployed as a webhook service on Railway!

**Next Steps:**
1. Test the webhook endpoints
2. Integrate into your application
3. Monitor performance and logs
4. Scale as needed

Happy automating! 🚀

