# 🧠 AI Log Analyzer

This project is a **Flask-based web application** that uses **Google Gemini AI** and **spaCy** to automatically analyze Android log files.  
It detects common issues, finds similarities between reports, and generates readable summaries to support developers in debugging.

---

## 🚀 Features
- Upload and analyze Android log files through a web interface  
- AI-powered text analysis using Gemini  
- Automatic summarization and similarity detection  
- Clean, modular Flask architecture  
- Simple HTML/CSS frontend (ready for further development)

---

## 📦 What to Install

Before running the application, make sure these tools and Python packages are installed:

### 🧰 System Requirements
| Tool | Recommended Version | Description | Download |
|------|---------------------|-------------|-----------|
| **Python** | 3.10 or higher (tested on 3.13) | Required to run the app | [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Latest | Python package manager | Comes with Python |
| **Git** | Latest | For cloning and version control | [git-scm.com/downloads](https://git-scm.com/downloads) |

---

### 🐍 Python Dependencies

All required Python packages are listed in `requirements.txt`.  
To install everything automatically:

```bash
pip install -r requirements.txt

python -m spacy download en_core_web_sm
