from fastapi import FastAPI
from pydantic import BaseModel

import os
import re
from dotenv import load_dotenv

# ✅ Groq LLM Client
from groq import Groq

# ✅ YouTube Transcript API (Latest v1.2.4)
from youtube_transcript_api import YouTubeTranscriptApi

# ✅ Article + Documentation Extraction
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urljoin

# ✅ OCR Tools
from PIL import Image
import pytesseract
from io import BytesIO

# ✅ PDF and Email Tools
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


# ✅ Load Environment Variables
load_dotenv()

# ✅ Groq API Key Setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ✅ FastAPI App Init
app = FastAPI(title="Universal URL Summarizer Agent ✅")


# ✅ Request Schema
class URLRequest(BaseModel):
    url: str
    email: str = None  # Optional email for sending PDF


# ✅ Prompt for Notes Generation
SYSTEM_PROMPT = """
You are an expert AI Notes Generator.

Summarize the given content into important structured bullet points.
Cover all key concepts properly.
Limit the summary to 250-300 words.
"""

# -------------------------------
# ✅ Extract YouTube Video ID
# -------------------------------
def get_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None


# -------------------------------
# ✅ YouTube Transcript Tool (Manual + Auto)
# -------------------------------
def extract_youtube_transcript(url):
    try:
        video_id = get_video_id(url)
        if not video_id:
            return None

        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # ✅ Try manual transcript first
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except:
            transcript = transcript_list.find_generated_transcript(["en"])

        fetched = transcript.fetch()
        transcript_text = " ".join([snippet.text for snippet in fetched])

        return transcript_text

    except Exception as e:
        str.error(f"❌ Transcript Error: {e}")
        return None


# -------------------------------
# ✅ Article Text Tool
# -------------------------------
def extract_article_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text


# -------------------------------
# ✅ Extract Images from Article
# -------------------------------
def extract_image_urls(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    img_urls = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            img_urls.append(urljoin(url, src))

    return img_urls[:3]  # only first 3 images


# -------------------------------
# ✅ OCR from Image URLs
# -------------------------------
def ocr_from_image_url(img_url):
    try:
        img_data = requests.get(img_url).content
        img = Image.open(BytesIO(img_data))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except:
        return ""


# -------------------------------
# ✅ Documentation Extract Tool (Text + OCR)
# -------------------------------
def extract_article_with_images(url):
    text = extract_article_text(url)

    image_urls = extract_image_urls(url)

    ocr_text = ""
    for img_url in image_urls:
        ocr_text += "\n" + ocr_from_image_url(img_url)

    full_content = text + "\n\nImportant Text from Images:\n" + ocr_text
    return full_content


# -------------------------------
# ✅ Groq Summarizer Tool
# -------------------------------
def summarize_with_groq(content):
    content = content[:7000]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Generate notes in bullet points:\n" + content}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# -------------------------------
# ✅ Router Agent
# -------------------------------
def route_input(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    else:
        return "article"


# -------------------------------
# ✅ Master Agent Pipeline
# -------------------------------
def agent_pipeline(url):

    input_type = route_input(url)

    if input_type == "youtube":
        content = extract_youtube_transcript(url)

    else:
        content = extract_article_with_images(url)

    if not content:
        return None

    return summarize_with_groq(content)


# -------------------------------------------------
# ✅ PDF & Email Functions
# -------------------------------------------------

def create_pdf(summary):
    """Create PDF from summary text"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for line in summary.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True)
    
    return pdf.output(dest='S').encode('latin-1')


def send_pdf_via_email(pdf_data, recipient_email):
    """Send PDF to recipient email using SMTP"""
    try:
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        
        if not sender_email or not sender_password:
            return False, "Email credentials not configured"
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Your AI Generated Notes - PDF Attached"
        
        body = """
Dear User,

Here is your AI-generated summary notes from the URL you provided.

This PDF contains detailed and organized notes generated using our Universal Notes Generator.

Best Regards,
Universal Notes Generator Agent
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename='notes.pdf')
        msg.attach(part)
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True, f"PDF sent successfully to {recipient_email}"
        
    except smtplib.SMTPAuthenticationError:
        return False, "Email authentication failed"
    except smtplib.SMTPException as e:
        return False, f"Email sending failed: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


# -------------------------------------------------

@app.get("/")
def home():
    return {"message": "Universal Summarizer Agent is running ✅"}


@app.post("/summarize")
def summarize(request: URLRequest):

    url = request.url

    summary = agent_pipeline(url)

    if not summary:
        return {"status": "error", "message": "Could not extract content from this URL."}

    result = {
        "status": "success",
        "url": url,
        "summary": summary
    }
    
    # Send email if provided
    if request.email:
        pdf_data = create_pdf(summary)
        success, message = send_pdf_via_email(pdf_data, request.email)
        result["email_status"] = message
        result["email_sent"] = success
    
    return result
