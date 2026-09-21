# 🎥 Videxa – AI Video Assistant with RAG

Videxa is an AI-powered Video Intelligence platform that transforms YouTube videos, meetings, lectures, podcasts, and local media files into actionable insights.

It combines Speech-to-Text, AI Summarization, Vector Search, and Retrieval-Augmented Generation (RAG) to help users understand and interact with video content efficiently.

## ✨ Features

### 🎙️ Audio & Video Processing

* Process YouTube URLs directly
* Upload and analyze local audio/video files
* Automatic audio extraction and conversion
* Long audio chunking for efficient transcription

### 📝 AI Transcription

* Powered by OpenAI Whisper
* Multi-language support
* Accurate speech-to-text conversion
* Handles long recordings automatically

### 📄 Smart Summarization

* Generate concise meeting summaries
* Extract key insights and highlights
* Create AI-generated titles
* Reduce hours of content into readable notes

### 🔍 RAG-Powered Chat

* Ask questions about the video content
* Context-aware answers using vector search
* ChromaDB-powered document retrieval
* Conversational interaction with transcripts

### 🎨 Modern UI

* Built with Streamlit
* Dark futuristic interface
* Interactive workflow
* Real-time processing feedback

---

## 🏗️ Tech Stack

### AI & LLM

* OpenAI Whisper
* LangChain
* Sentence Transformers

### Vector Database

* ChromaDB

### Backend

* Python
* yt-dlp
* pydub

### Frontend

* Streamlit

---

## 📂 Project Structure

```text
VIDEXA/
├── core/
│   ├── exporters/       # Reusable TXT, Markdown, JSON, and PDF exports
│   ├── extractor.py
│   ├── transcriber.py
│   ├── summarizer.py
│   ├── vector_store.py
│   └── rag_engine.py
│
├── utils/
│   └── audio_processor.py
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/videxa.git
cd videxa
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Environment

#### Windows

```bash
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r Requirements.txt
```

---

## ⚙️ Setup

Create a `.env` file in the root directory:

```env
MISTRAL_API_KEY=your_api_key_here
# SARVAM_API_KEY=your_api_key_here  # only needed for Hinglish transcription
```

---

## ▶️ Run Application

```bash
python -m streamlit run app.py
```

Application will be available at:

```text
http://localhost:8501
```

---

## 🔄 Workflow

1. Paste a YouTube URL or provide a local file path.
2. Select the desired language.
3. Click **Analyse**.
4. Videxa will:

   * Extract audio
   * Transcribe speech
   * Generate summaries
   * Build vector embeddings
   * Enable RAG chat

---

## 🎯 Future Improvements

* Speaker diarization
* Meeting action items extraction
* Multi-video knowledge base
* Cloud deployment
* Team collaboration features

---

## 📦 Export services

Videxa provides frontend-agnostic, in-memory export functions for use by a
future API or web frontend. They do not import Streamlit or write export files.

```python
from core.exporters import export_analysis, export_transcript, generate_pdf_report

transcript_txt = export_transcript("Meeting transcript")
analysis_md = export_analysis({"summary": "...", "action_items": ["..."]})
analysis_json = export_analysis({"summary": "..."}, format="json")
report_pdf = generate_pdf_report({"title": "Weekly Sync", "transcript": "..."})
```

Supported formats are UTF-8 TXT (transcripts), UTF-8 Markdown or JSON
(analysis), and PDF reports. PDF reports use ReportLab's standard built-in font;
unsupported glyphs are replaced in the PDF so generation remains reliable. Use
TXT, Markdown, or JSON when complete Unicode fidelity is required.

---

## 👨‍💻 Author

**Suraj Kumar Ray**

B.Tech Information Technology
AI & Full Stack Developer

---

## 📜 License

This project is licensed under the MIT License.
