# AI StudyMate 🎓
### AI-Powered PDF to Mock Test & Interview Preparation Platform

**AI StudyMate** is a production-quality educational web application designed for students and professionals preparing for university examinations, viva, and technical interviews. It allows users to upload any subject PDF, extracts and cleans syllabus content page by page using PyMuPDF, analyzes core examinable concepts via AI (Google Gemini, NVIDIA NIM, or academic heuristic parsing), synthesizes grounded multiple-choice questions (MCQs), and delivers a randomized, timed mock test with a strict 60-second timer per question followed by an in-depth study and revision dashboard.

---

## 🌟 Key Features

* **Strict Light Theme Design**: Modern, clean, accessible UI built with crisp typography, card elevation, soft borders, and generous spacing.
* **Strict Syllabus Grounding**: Questions and explanations are generated exclusively from the uploaded PDF text without external hallucinations.
* **Zero Database Architecture**: Operates cleanly using JSON persistence (`data/*.json`) and browser `localStorage`/`sessionStorage`. Completely deployable on GitHub-based hosts without setting up SQL/NoSQL databases.
* **Modular Multi-Provider AI Service**:
  * Google Gemini API (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-pro`)
  * NVIDIA NIM API (`meta/llama-3.1-70b-instruct`, etc.)
  * Built-in Grounded Academic Fallback Engine (runs offline or during rate-limits out of the box)
* **High-Performance PyMuPDF Extraction**: Extracts page-by-page text, cleans whitespace noise, detects chapter/section headers, and builds semantic academic chunks.
* **Timed Mock Test with Anti-Exploitation Rules**:
  * Exactly 60 seconds (`01:00`) per question.
  * Visual alert animation when remaining time reaches $\le 10$ seconds.
  * Automatic progression and marking on timer expiry (`00:00`).
  * Locked questions prevent users from exploiting the timer.
  * Automatic test submission on final question timeout.
* **Study-First Results Dashboard**:
  * Radial circular score percentage indicator.
  * Performance tiers (*Excellent*, *Very Good*, *Good*, *Needs Improvement*, *Keep Practicing*).
  * Topic-wise mastery progress bars.
  * Filterable review interface (*All*, *Incorrect*, *Correct*, *Unanswered*).
  * Concise 2–4 sentence explanations with source page references (e.g., `📄 Source: Page 4`).
  * **Strictly No Retries**: Test is finished upon submission to prioritize studying mistakes.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.10+, Flask 3.0+
* **PDF Processing**: PyMuPDF (`fitz` / `pymupdf`)
* **AI Integration**: Google Generative AI SDK, NVIDIA NIM REST API, `requests`
* **Frontend**: Vanilla HTML5, Modern CSS3 (Custom Design System, CSS Variables, Flexbox/Grid), Vanilla ES6+ JavaScript
* **Data Storage**: Pure JSON file storage (`data/`) and browser storage

---

## 📁 Project Structure

```text
ai-studymate/
│
├── app.py                          # Flask application factory and route controller
├── sample_pdf_creator.py           # Academic sample PDF generator (ML/AI primer)
├── test_app.py                     # Comprehensive backend integration test suite
├── requirements.txt                # Python dependencies
├── .env                            # Active environment variables
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git exclusion rules
├── README.md                       # Complete documentation
│
├── services/
│   ├── __init__.py
│   ├── pdf_extractor.py            # PyMuPDF extraction, cleaning, heading detection & chunking
│   ├── ai_processor.py             # Modular AI client (Gemini, NVIDIA, Fallback Engine)
│   ├── question_generator.py       # Question bank generation, validation & persistence
│   └── test_manager.py             # Randomized test session manager & evaluation
│
├── data/
│   ├── question_bank.json          # Active generated MCQ question bank
│   ├── extracted_content.json      # Structured extracted text & topics
│   └── test_results.json           # Evaluated test session history
│
├── templates/
│   ├── index.html                  # Educational SaaS landing page
│   ├── upload.html                 # Drag-and-drop PDF upload interface
│   ├── processing.html             # Multi-step extraction & generation checklist
│   ├── setup_test.html             # Test volume and difficulty configuration
│   ├── test.html                   # Timed mock test interface (60s countdown)
│   └── result.html                 # Result & Study dashboard
│
├── static/
│   ├── css/
│   │   └── style.css               # Clean Light Theme CSS design system
│   │
│   └── js/
│       ├── main.js                 # Toast notifications & shared UI helpers
│       ├── upload.js               # File drag-and-drop & upload handlers
│       ├── test.js                 # 60s question timer, anti-cheat & test flow
│       └── result.js               # Score animations & study card filtering
│
└── uploads/
    ├── .gitkeep
    └── sample_machine_learning_primer.pdf
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-studymate.git
cd ai-studymate
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# AI Provider: gemini (default), nvidia, or openai_compatible
AI_PROVIDER=gemini

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# NVIDIA NIM API (Alternative)
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=meta/llama-3.1-70b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Flask Configuration
FLASK_SECRET_KEY=your_secure_random_key
PORT=5000
```

> **Note:** If no API key is provided, the application automatically uses its built-in Grounded Academic NLP Engine to generate syllabus-grounded MCQs offline!

---

## ▶️ How to Run

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## 🔍 How PDF Processing & AI Generation Work

1. **Extraction**: PyMuPDF reads the PDF page-by-page, strips header/footer noise, cleans whitespace, and tags chapter headings.
2. **Chunking**: The document is segmented into semantic academic units (600–800 words) while preserving source page ranges.
3. **AI Concept Analysis**: The AI assistant identifies:
   * Core definitions and key terminology
   * Algorithmic steps and procedures
   * Classifications and comparisons
   * Formulas and examinable facts
4. **MCQ Generation**:
   * Exactly 4 distinct options per question.
   * Single ground-truth correct answer.
   * Shuffled answer positions across A, B, C, D.
   * Grounded 2–4 sentence explanation and source page citation.
5. **Persistence**: The full question bank is saved in `data/question_bank.json` for reuse across multiple test configurations without calling the LLM API repeatedly.

---

## ⏱️ How the 60-Second Timer Works

* **Individual Question Timer**: Each question provides a dedicated 60-second countdown (`01:00` $\to$ `00:00`).
* **Visual Warning**: At $\le 10$ seconds remaining, the badge pulses with an amber/red alert.
* **Auto-Advance**: When the timer reaches `00:00`, the current question locks, the student's answer is recorded (or marked as *Unanswered*), and the test advances to the next question.
* **Anti-Exploitation Rule**: Expired questions cannot be revisited.
* **Auto-Submit**: When the timer expires on the last question, the entire test is submitted automatically.

---

## 🧪 Automated Testing

Run the integration test suite:
```bash
python test_app.py
```

---

## 🌐 GitHub & Deployment Guidelines

1. **Version Control**: `.env` and `uploads/*.pdf` are excluded via `.gitignore`.
2. **Production Server**: For production environments, run with Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

---

## 🔮 Future Enhancements

* **Multi-PDF Course Bundles**: Merging multiple course slides into a comprehensive semester question bank.
* **LaTeX Formula Rendering**: Enhanced KaTeX rendering for advanced mathematics and physics equations.
* **Export to Anki Flashcards**: One-click export of incorrect questions into Anki `.apkg` decks.
