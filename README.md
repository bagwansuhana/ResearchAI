# ResearchAI — Evidence-Grounded Academic Research Assistant

ResearchAI is an AI-powered academic research assistant built with Python and Streamlit. It helps users discover scholarly papers, retrieve relevant evidence, generate research answers, and evaluate claims against the available evidence.

## Features

- **Academic Paper Search:** Search for research papers related to a research question.
- **Paper Selection:** Select relevant papers for further analysis.
- **Text Extraction:** Extract text from accessible research documents.
- **RAG Pipeline:** Retrieve relevant text chunks before generating an answer.
- **Evidence Retrieval:** Use TF-IDF and cosine similarity to identify relevant passages.
- **AI-Powered Analysis:** Use the Google Gemini API to generate answers from retrieved evidence.
- **Claim Assessment:** Evaluate claims as Supported, Partially Supported, Unsupported, or Insufficient Evidence.
- **Structured Research Reports:** Present conclusions, evidence assessments, sources, confidence information, and limitations.
- **Saved Papers:** Save papers within the application.
- **Research History:** Review previous research queries within the application.
- **Authentication:** Email/password sign-up and login using Supabase Auth.

## Technologies Used

- Python
- Streamlit
- Google Gemini API
- Supabase
- scikit-learn
- Requests
- BeautifulSoup
- pypdf
- python-dotenv

## How It Works

1. The user submits a research question.
2. The application searches for relevant scholarly papers.
3. Text is extracted from accessible research documents.
4. Documents are divided into smaller chunks.
5. TF-IDF and cosine similarity identify relevant evidence.
6. Gemini generates an answer using the retrieved evidence.
7. The application extracts and assesses claims against the evidence.
8. A structured research report is displayed.

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd ResearchAI
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your repository URL.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_publishable_key
```

Replace the placeholders with your own credentials. Never commit `.env` or publish API keys.

### 5. Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser.

## Current Limitations

- Full-text access depends on the availability of research documents.
- Evidence retrieval may miss relevant passages.
- AI-generated assessments may contain errors and require human review.
- Persistent cloud storage of research sessions and saved papers requires complete implementation and testing.

## Future Improvements

- Persistent cloud storage for research history and saved papers.
- Google sign-in.
- Improved semantic retrieval using embedding models.
- More extensive evaluation of evidence quality and claim verification.
- Deployment for public access.

## Project Purpose

ResearchAI is an academic project exploring retrieval-augmented generation (RAG), information retrieval, large language models, and evidence-grounded AI systems.
