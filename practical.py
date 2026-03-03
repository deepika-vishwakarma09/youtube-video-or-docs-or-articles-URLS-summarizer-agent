import streamlit as st
from dotenv import load_dotenv
import os
import re
import mlflow
import mlflow.pyfunc


# Groq LLM
from groq import Groq

# YouTube Transcript API
from youtube_transcript_api import YouTubeTranscriptApi

# Article + Documentation Tools
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urljoin

# OCR Tools (Images inside Docs)
from PIL import Image
import pytesseract
from io import BytesIO
from fpdf import FPDF

# Email Sending
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


# Load Environment Variables
load_dotenv()

print("=" * 50)
print("ENVIRONMENT VARIABLES LOADED:")
print(f"SENDER_EMAIL: {os.getenv('SENDER_EMAIL')}")
print(f"SENDER_PASSWORD: {os.getenv('SENDER_PASSWORD')}")
print(f"SMTP_SERVER: {os.getenv('SMTP_SERVER', 'smtp.gmail.com')}")
print(f"SMTP_PORT: {os.getenv('SMTP_PORT', 587)}")
print("=" * 50)

# Groq Client Setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Prompt
SYSTEM_PROMPT = """
You are an expert AI Notes Generator.

Summarize the given content into important structured bullet points.
Cover all key concepts properly.
Limit the summary to 250–300 words.
"""


# Extract YouTube Video ID
def get_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None



# YouTube Transcript Tool (Manual + Auto)
def extract_youtube_transcript(url):
    try:
        video_id = get_video_id(url)
        if not video_id:
            return None

        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        # Try manual transcript first
        try:
            transcript = transcript_list.find_manually_created_transcript(["en","hi"])
        except:
            transcript = transcript_list.find_generated_transcript(["en","hi"])

        fetched = transcript.fetch()
        transcript_text = " ".join([snippet.text for snippet in fetched])

        return transcript_text

    except Exception as e:
        st.error(f" Transcript Error: {e}")
        return None



#  Article Text Tool
def extract_article_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text


# Extract Images from Article
def extract_image_urls(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    img_urls = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            img_urls.append(urljoin(url, src))

    return img_urls[:3]  # only first 3 images

# OCR from Image URLs
def ocr_from_image_url(img_url):
    try:
        img_data = requests.get(img_url).content
        img = Image.open(BytesIO(img_data))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except:
        return ""



# Documentation Extract Tool (Text + OCR)

def extract_article_with_images(url):
    text = extract_article_text(url)

    image_urls = extract_image_urls(url)

    ocr_text = ""
    for img_url in image_urls:
        ocr_text += "\n" + ocr_from_image_url(img_url)

    full_content = text + "\n\nImportant Text from Images:\n" + ocr_text
    return full_content


# Groq Summarizer Tool
def summarize_with_groq(content, url_type="youtube"):

    with mlflow.start_run():

        mlflow.log_param("url_type", url_type)
        mlflow.log_param("model", "llama-3.1-8b-instant")

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]
        )

        summary = response.choices[0].message.content

        #  Log summary safely
        mlflow.log_text(summary, "summary.txt")

        return summary


# Router Agent

def route_input(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    else:
        return "article"



# Master Agent Pipeline
def agent_pipeline(url):

    input_type = route_input(url)

    if input_type == "youtube":
        content = extract_youtube_transcript(url)
    else:
        content = extract_article_with_images(url)

    if not content:
        return None

    return summarize_with_groq(content, url_type=input_type)


# PDF Creation Function

def create_pdf(summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split summary into lines and add to PDF
    for line in summary.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True)
    
    # Return PDF as bytes for download
    return pdf.output(dest='S').encode('latin-1')


# Email Sending Function
def send_pdf_via_email(pdf_data, recipient_email):
    """
    Send PDF to recipient email using SMTP
    """
    try:
        # Get email credentials from environment variables
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        
        print(f"DEBUG: Sender Email: {sender_email}")
        print(f"DEBUG: SMTP Server: {smtp_server}")
        print(f"DEBUG: SMTP Port: {smtp_port}")
        
        if not sender_email or not sender_password:
            return False, " Email credentials not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Your AI Generated Notes - PDF Attached"
        
        # Email body
        body = """
Dear User,

Here is your AI-generated summary notes from the URL you provided.

This PDF contains detailed and organized notes generated using our Url Notes Generator.

Best Regards,
Url Notes Generator Agent
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        part = MIMEBase('application', 'octet-stream')
        
        # Convert pdf_data to bytes if it's a string
        if isinstance(pdf_data, str):
            pdf_data = pdf_data.encode('latin-1')
        
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename='notes.pdf')
        msg.attach(part)
        
        print(f"DEBUG: Connecting to {smtp_server}:{smtp_port}")
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            print(f"DEBUG: Logging in with {sender_email}")
            server.login(sender_email, sender_password)
            print(f"DEBUG: Sending message to {recipient_email}")
            server.send_message(msg)
        
        print(f"DEBUG: Email sent successfully!")
        return True, f" PDF sent successfully to {recipient_email}"
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"DEBUG: Auth Error: {str(e)}")
        return False, " Email authentication failed. Check your SENDER_EMAIL and SENDER_PASSWORD."
    except smtplib.SMTPException as e:
        print(f"DEBUG: SMTP Error: {str(e)}")
        return False, f" Email sending failed: {str(e)}"
    except Exception as e:
        print(f"DEBUG: General Error: {str(e)}")
        return False, f" Error: {str(e)}"


# ---------------- SESSION STATE ----------------
if "summary" not in st.session_state:
    st.session_state.summary = None

if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None


# ---------------- UI ----------------
st.set_page_config(page_title="All URL Notes Generator", layout="wide")

st.title("All types URL → Detailed Notes Generator")
st.write("Paste any YouTube link OR any Article/Documentation URL to generate AI Notes.")

col1, col2 = st.columns([3, 1])

with col1:
    user_link = st.text_input("Enter Any URL:")

with col2:
    user_email = st.text_input("📧 Email (Optional):", placeholder="your@email.com")


# Show thumbnail if YouTube
if user_link and ("youtube.com" in user_link or "youtu.be" in user_link):
    video_id = get_video_id(user_link)
    if video_id:
        st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", width=450)


# -------- Generate Notes Button --------
if st.button("Get Detailed Notes"):

    if user_link.strip() == "":
        st.warning("Please enter a valid URL.")

    else:
        with st.spinner("Agent is reading and summarizing... ⏳"):
            summary = agent_pipeline(user_link)

            if summary:
                st.session_state.summary = summary
                st.session_state.pdf_data = create_pdf(summary)
            else:
                st.error("Could not extract content from this URL.")


# -------- SHOW SUMMARY IF AVAILABLE --------
if st.session_state.summary:

    st.markdown("## Detailed Notes:")
    st.write(st.session_state.summary)

    st.download_button(
        label="Download Notes as PDF",
        data=st.session_state.pdf_data,
        file_name="notes.pdf",
        mime="application/pdf"
    )

    # -------- EMAIL SEND BUTTON --------
    if user_email:
        if st.button("📧 Send PDF to Email"):
            with st.spinner("Sending email..."):
                success, message = send_pdf_via_email(
                    st.session_state.pdf_data,
                    user_email.strip()
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

                