# Email Configuration Guide

## How to Enable Email Sending for PDF

This agent now supports automatic PDF sending via email. Follow these steps to set it up:

### Step 1: Configure Your Email Account

#### For Gmail Users:
1. Go to your Google Account: https://myaccount.google.com/
2. Click on "Security" in the left sidebar
3. Enable "2-Step Verification" if not already enabled
4. Go to "App passwords" (you'll see this option after enabling 2FA)
5. Select "Mail" and "Windows Computer"
6. Google will generate a 16-character password - **copy this password**

#### For Other Email Providers:
- **Outlook/Hotmail**: Use your regular password or app password
- **Yahoo**: Generate an app password from Yahoo Account settings
- **Corporate Email**: Contact your IT department for SMTP settings and app password

### Step 2: Update Your .env File

Open `.env` file and add the following configuration:

```env
# Email Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password_here

# SMTP Server (defaults to Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Replace:**
- `your_email@gmail.com` with your actual email
- `your_app_password_here` with the 16-character password from Step 1

### Step 3: Use the Streamlit App

1. Start the Streamlit app:
   ```bash
   streamlit run practical.py
   ```

2. In the UI:
   - Enter the URL you want to summarize
   - (Optional) Enter an email address in the "Email" field
   - Click "Get Detailed Notes"
   - After notes are generated, click "📧 Send PDF to Email"
   - The PDF will be automatically sent to the provided email!

### Step 4: Use the FastAPI Endpoint

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Send a POST request with email:
   ```bash
   curl -X POST "http://localhost:8000/summarize" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://youtube.com/watch?v=...",
       "email": "recipient@gmail.com"
     }'
   ```

3. Response example:
   ```json
   {
     "status": "success",
     "url": "https://youtube.com/watch?v=...",
     "summary": "Your detailed notes...",
     "email_status": "PDF sent successfully to recipient@gmail.com",
     "email_sent": true
   }
   ```

## Troubleshooting

### "Email credentials not configured"
- Make sure `SENDER_EMAIL` and `SENDER_PASSWORD` are set in `.env`
- Restart your app after adding to `.env`

### "Email authentication failed"
- Verify you're using the **App Password**, not your regular password
- Check that 2-Factor Authentication is enabled on your Gmail account
- For other providers, verify the SMTP credentials

### "SMTP connection error"
- Check your internet connection
- Verify `SMTP_SERVER` and `SMTP_PORT` are correct for your email provider
- Some corporate networks may block SMTP port 587 - try port 465 (SSL) instead

### Email takes too long to arrive
- Check your spam/junk folder
- Gmail has some rate limiting - wait a few minutes between sending multiple emails

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to version control
- Keep your app password private
- Use app passwords instead of regular passwords for better security
- Consider using environment variables in production instead of `.env` files

## Email Providers' SMTP Settings

| Provider | SMTP Server | Port |
|----------|-------------|------|
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp-mail.outlook.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |
| Office 365 | smtp.office365.com | 587 |
| Zoho | smtp.zoho.com | 587 |

## Features

✅ **Streamlit App:**
- Optional email input field
- Send PDF directly from UI
- Real-time status messages

✅ **FastAPI API:**
- Email parameter in POST request
- Automatic PDF generation and sending
- Email status in response

Both interfaces support the same email functionality!
