import streamlit as st
from dotenv import load_dotenv
import os
import re

# ✅ Groq LLM
from groq import Groq

# ✅ YouTube Transcript API
from youtube_transcript_api import YouTubeTranscriptApi

# ✅ Article + Documentation Tools
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urljoin

# ✅ OCR Tools (Images inside Docs)
from PIL import Image
import pytesseract
from io import BytesIO
from fpdf import FPDF

# -------------------------------
# ✅ Load Environment Variables
# -------------------------------
load_dotenv()

# ✅ Groq Client Setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------
# ✅ Prompt
# -------------------------------
SYSTEM_PROMPT = """
You are an expert AI Notes Generator.

Summarize the given content into important structured bullet points.
Cover all key concepts properly.
Limit the summary to 250–300 words.
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
            transcript = transcript_list.find_manually_created_transcript(["en","hi"])
        except:
            transcript = transcript_list.find_generated_transcript(["en","hi"])

        fetched = transcript.fetch()
        transcript_text = " ".join([snippet.text for snippet in fetched])

        return transcript_text

    except Exception as e:
        st.error(f"❌ Transcript Error: {e}")
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

# -------------------------------
# ✅ PDF Creation Function
# -------------------------------
def create_pdf(summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Split summary into lines and add to PDF
    for line in summary.split('\n'):
        pdf.cell(200, 10, txt=line, ln=True)
    
    # Return PDF as bytes for download
    return pdf.output(dest='S').encode('latin-1')



# -------------------------------
# ✅ Streamlit UI
# -------------------------------
st.set_page_config(page_title="Universal Notes Generator", layout="wide")

st.title("🤖 Universal URL → Detailed Notes Generator")
st.write("Paste any YouTube link OR any Article/Documentation URL to generate AI Notes.")

user_link = st.text_input("🔗 Enter Any URL:")

# ✅ Show Thumbnail ONLY if YouTube link
if user_link and ("youtube.com" in user_link or "youtu.be" in user_link):
    video_id = get_video_id(user_link)
    if video_id:
        st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", width=450)

# ✅ Button
if st.button("📌 Get Detailed Notes"):

    if user_link.strip() == "":
        st.warning("⚠️ Please enter a valid URL.")

    else:
        with st.spinner("Agent is reading and summarizing... ⏳"):

            summary = agent_pipeline(user_link)

            if summary:
                st.markdown("## ✅ Detailed Notes:")
                st.write(summary)
                # ✅ PDF Download Button
                pdf_data = create_pdf(summary)
                st.download_button(
                    label="📄 Download Notes as PDF",
                    data=pdf_data,
                    file_name="notes.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ Could not extract content from this URL.")
                