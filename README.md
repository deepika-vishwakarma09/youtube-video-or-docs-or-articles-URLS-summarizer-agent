# Universal URL → AI Notes Generator

> An AI-powered application that automatically generates structured notes from YouTube videos, articles, or documentation URLs.

---

##  Features

-  Generate AI-powered notes from **YouTube videos**
-  Summarize **articles and documentation** URLs
-  Extract **YouTube transcripts** automatically
-  Perform **OCR** on images within articles
-  Download generated notes as **PDF**
-  Send notes via **Email**
-  **MLflow** integration for experiment tracking
-  Fully **Dockerized** application
-  Automated **CI/CD pipeline** with GitHub Actions

---

##  System Architecture

```
User URL
   │
   ▼
Streamlit UI
   │
   ▼
Agent Pipeline
   │
   ├── YouTube Transcript Extraction
   ├── Article & Documentation Scraper
   ├── OCR Processing
   │
   ▼
Groq LLM (Llama 3.1)
   │
   ▼
Structured Notes
   │
   ├── PDF Download
   └── Email Delivery
```

---

##  Tech Stack

| Category             | Tools                          |
|----------------------|--------------------------------|
| Language             | Python                         |
| UI                   | Streamlit                      |
| LLM                  | Groq (Llama-3.1-8B)            |
| Web Scraping         | BeautifulSoup, Newspaper       |
| OCR                  | Tesseract                      |
| Experiment Tracking  | MLflow                         |
| Containerization     | Docker                         |
| CI/CD                | GitHub Actions                 |
| Image Registry       | Docker Hub                     |

---

##  Project Structure

```
youtube-video-or-docs-or-articles-URLS-summarizer-agent/
│
├── practical.py              # Main Streamlit application
├── main.py                   # FastAPI integration (optional)
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container setup
├── docker-compose.yml        # Docker Compose configuration
├── .env.example              # Example environment variables
├── test_email.py             # Email test script
├── EMAIL_SETUP.md            # Email configuration guide
├── mlflow.db                 # MLflow database
├── mlruns/                   # MLflow experiment logs
│
├── .github/
│   └── workflows/
│       └── docker.yml        # CI/CD pipeline
│
├── README.md
└── .gitignore
```

---

##  Environment Variables

Create a `.env` file in the project root directory:

```env
GROQ_API_KEY=your_groq_api_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_email_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

>  **Important:** Never push your `.env` file to GitHub. Make sure it's listed in `.gitignore`.

---

##  Docker Setup

### Build the Image

```bash
docker build -t url-agent .
```

### Run the Container

```bash
docker run -p 8501:8501 --env-file .env url-agent
```

Then open the app in your browser:

```
http://localhost:8501
```

### Pull from Docker Hub

```bash
docker pull deepikavishwakarma09/url-agent
```

```bash
docker run -p 8501:8501 deepikavishwakarma09/url-agent
```

 Docker Hub: [deepikavishwakarma09/url-agent](https://hub.docker.com/r/deepikavishwakarma09/url-agent)

---

##  CI/CD Pipeline (GitHub Actions)

This project includes an automated CI/CD pipeline using **GitHub Actions**.

**Workflow file:** `.github/workflows/docker.yml`

**Trigger:** Automatically runs on every push to the `main` branch.

**Pipeline Steps:**

1.  Checkout repository
2.  Login to Docker Hub
3.  Build Docker image using Dockerfile
4.  Push Docker image to Docker Hub

###  Required GitHub Secrets

| Secret            | Description                        |
|-------------------|------------------------------------|
| `DOCKER_USERNAME` | Your Docker Hub username           |
| `DOCKER_PASSWORD` | Your Docker Hub password or token  |

---

##  MLflow Experiment Tracking

MLflow is integrated to track experiments and application logs.

**Start MLflow UI:**

```bash
mlflow ui
```

**Open in browser:**

```
http://localhost:5000
```

---

##  Application Workflow

1. User enters a **YouTube or Article URL**
2. System **identifies the input type**
3. Content is **extracted** from the source
4. Extracted text is sent to the **Groq LLM**
5. LLM generates **structured notes**
6. User can:
   -  Download notes as **PDF**
   -  Send notes via **Email**

---

##  Future Improvements

-  Multi-language support
-  RAG-based document retrieval
-  User authentication system
-  Database storage for generated notes
-  Cloud deployment (AWS / GCP / Azure)

---

##  Author

**Deepika Vishwakarma**  
MSc Artificial Intelligence & Machine Learning — IIIT Lucknow

[![GitHub](https://img.shields.io/badge/GitHub-deepika--vishwakarma09-181717?logo=github)](https://github.com/deepika-vishwakarma09)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-deepikavishwakarma09-2496ED?logo=docker)](https://hub.docker.com/r/deepikavishwakarma09/url-agent)
