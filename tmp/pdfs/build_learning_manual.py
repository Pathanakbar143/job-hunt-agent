from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path("/Users/akbar/job-hunt-agent")
OUT = ROOT / "output" / "pdf"
PDF_PATH = OUT / "job_hunt_agent_learning_guide.pdf"
MD_PATH = OUT / "job_hunt_agent_learning_guide.md"


def read_source(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        return f"[Missing file in current workspace: {path}]"
    lines = full.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(f"{i + 1:>4}  {line}" for i, line in enumerate(lines))


def safe(text: str) -> str:
    return escape(text)


def code(text: str) -> str:
    return f"<font name='Courier'>{safe(text)}</font>"


def pdf_text(text: str) -> str:
    replacements = {
        "🤖": "[robot]",
        "🚀": "[launch]",
        "📥": "[download]",
        "🔄": "[retry]",
        "🕵️": "[search]",
        "🕵": "[search]",
        "🎯": "[score]",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "→": "->",
        "←": "<-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return "".join(ch if ord(ch) < 128 else " " for ch in text)


def bullets(items):
    return "\n".join(f"- {item}" for item in items)


def section(title, body="", subsections=None, exercises=None, interview=None, mistakes=None):
    return {
        "title": title,
        "body": body.strip(),
        "subsections": subsections or [],
        "exercises": exercises or [],
        "interview": interview or [],
        "mistakes": mistakes or [],
    }


def sub(title, body="", code_block=None):
    return {
        "title": title,
        "body": body.strip(),
        "code": code_block,
    }


ARCHITECTURE_DIAGRAM = r"""
User
 |
 | upload resume + choose target role/location
 v
Streamlit UI (app.py)
 |
 | stores cleaned resume text in st.session_state
 v
LangGraph Agent (agents/agent.py)
 |
 +--> Search Node
 |     |
 |     v
 |   Apify Google Search Scraper (searcher.py)
 |     |
 |     v
 |   raw job snippets + links
 |
 +--> Optional Query Expansion Node
 |
 +--> Score Node
       |
       +--> Local Embedding Score (local_scorer.py)
       |
       +--> Gemini/LangChain Fit Summary + Cover Letter (matcher.py)
       |
       v
    scored_jobs
       |
       v
Streamlit table + CSV download
"""


DATA_FLOW_DIAGRAM = r"""
PDF resume
  -> extract text with pypdf
  -> clean whitespace
  -> keep resume text in Streamlit session state
  -> user enters target job title and location
  -> Apify search returns job links and snippets
  -> each snippet becomes the temporary job description
  -> SentenceTransformer converts resume and snippet into vectors
  -> cosine similarity creates Match Score
  -> Gemini generates Fit Summary and Cover Letter Draft
  -> Pandas converts scored jobs into a CSV table
  -> Streamlit displays and downloads results
"""


AGENT_GRAPH_DIAGRAM = r"""
               +----------------+
               |  search_jobs   |
               +----------------+
                    |       |
        jobs found  |       | no jobs and attempts < 3
                    v       v
              +-----------+ +--------------+
              | score_jobs| | expand_query |
              +-----------+ +--------------+
                    |              |
                    v              |
                  END <------------+
"""


MODEL_FLOW_DIAGRAM = r"""
resume text + job description/snippet
        |
        +--> local_scorer.py
        |       text -> embedding vectors -> cosine similarity -> numeric score
        |
        +--> matcher.py
                prompt template -> Gemini model -> JSON parser -> fit summary + cover letter
"""


CURRENT_SOURCE = {
    "app.py": read_source("app.py"),
    "agents/agent.py": read_source("agents/agent.py"),
    "matcher.py": read_source("matcher.py"),
    "searcher.py": read_source("searcher.py"),
    "local_scorer.py": read_source("local_scorer.py"),
    "utils/extractor.py": read_source("utils/extractor.py"),
    "utils/pdf_reader.py": read_source("utils/pdf_reader.py"),
    ".vscode/settings.json": read_source(".vscode/settings.json"),
}


sections = [
    section(
        "1. Project Overview",
        """
This manual explains your AI Job Hunt Agent project as if you are learning it from zero. The goal is not only to run the app, but to understand why each technology exists, how the files connect, and how to improve the project into a strong portfolio piece.

The product idea is simple: upload a resume, search jobs, compare each job against the resume, score the fit, explain the gaps, and produce application help such as a cover letter draft.

Current project name: AI Job Search Agent.
Recommended portfolio name: AI Job Hunt Copilot.
        """,
        [
            sub(
                "What problem does it solve?",
                """
Job seekers often do not know which jobs are worth applying to. Job descriptions are long, resumes are hard to tailor, and matching skills manually is slow. This project automates the first pass: it reads a resume, searches roles, scores matches, and explains why a job is or is not a good fit.
                """,
            ),
            sub(
                "What makes it portfolio-worthy?",
                bullets(
                    [
                        "It combines frontend, APIs, AI, embeddings, workflow orchestration, and data export.",
                        "It solves a real user problem that recruiters and job seekers understand.",
                        "It shows practical AI engineering instead of only calling an LLM once.",
                        "It can grow into RAG, vector search, tracking, analytics, and deployment.",
                    ]
                ),
            ),
            sub(
                "Current high-level architecture",
                code_block=ARCHITECTURE_DIAGRAM,
            ),
        ],
        exercises=[
            "Explain the product in 30 seconds as if you are talking to an interviewer.",
            "Write three user stories: one for a student, one for an experienced developer, and one for a recruiter.",
            "Draw the architecture from memory and compare it with the diagram.",
        ],
        interview=[
            "What problem does your app solve?",
            "Why did you use both embeddings and an LLM?",
            "What is the difference between a demo app and a production-ready app?",
        ],
        mistakes=[
            "Building only a script and not a clear user workflow.",
            "Showing an AI answer without explaining the reasoning or evidence.",
            "Ignoring current code gaps when presenting the project.",
        ],
    ),
    section(
        "2. Final Product Flow",
        """
The best final flow for the portfolio is:

Upload Resume -> Extract Resume Profile -> Confirm Search Target -> Search Jobs -> Fetch or collect Job Descriptions -> Score Each Job -> Rank Jobs -> Show Gap Report -> Generate Cover Letter.

Your current project already has parts of this, but some parts are not yet fully connected.
        """,
        [
            sub("Ideal user flow", code_block=DATA_FLOW_DIAGRAM),
            sub(
                "Current implemented flow",
                bullets(
                    [
                        "User uploads a PDF resume in Streamlit.",
                        "App stores cleaned resume text in Streamlit session state.",
                        "User manually enters target role and location.",
                        "LangGraph agent searches jobs through Apify.",
                        "Agent scores each job using local embeddings.",
                        "Agent asks Gemini through LangChain for fit summary and cover letter.",
                        "Streamlit displays scored jobs and offers a CSV download.",
                    ]
                ),
            ),
            sub(
                "Missing or incomplete flow pieces",
                bullets(
                    [
                        "The app imports utils/pdf_reader.py, but that file is missing in the current workspace. The compiled pycache exists, but source should be restored.",
                        "extract_resume_details() exists but is not connected to app.py, so the resume profile is not shown or used to infer target roles.",
                        "The app still asks the user to type a role instead of suggesting roles from the resume.",
                        "Job search currently uses search result snippets, not full job descriptions. This limits scoring accuracy.",
                        "There is no real database yet. jobs_database.csv acts as simple file storage.",
                        "The agent checks only the exact string API_ERROR, while searcher.py returns strings beginning with ERROR:. This can cause incorrect state handling.",
                        "There is no deployed URL, README, screenshots, or tests yet.",
                    ]
                ),
            ),
        ],
        exercises=[
            "Write the ideal flow as a numbered list in your own words.",
            "Identify which current file owns each step in the flow.",
            "Create a checklist of the next five implementation tasks.",
        ],
        interview=[
            "What is the main bottleneck in your current job matching quality?",
            "Why is fetching full job descriptions better than using snippets?",
            "How would you handle invalid or scanned PDF resumes?",
        ],
    ),
    section(
        "3. Architecture, Data Flow, API Flow, Model Flow, Database Flow, Deployment Flow",
        """
Architecture means how the parts are arranged. Data flow means how information moves. API flow means what external services are called. Model flow means how the AI models receive input and return output. Database flow means how records are stored and retrieved. Deployment flow means how the app becomes usable outside your laptop.
        """,
        [
            sub(
                "Architecture flow",
                """
Streamlit is the user interface. app.py collects inputs and starts the graph. agents/agent.py controls the multi-step workflow. searcher.py talks to Apify. local_scorer.py computes embedding similarity. matcher.py calls Gemini through LangChain. searcher.py also saves final results into CSV.
                """,
            ),
            sub(
                "API flow",
                """
The app reads API keys from .env using python-dotenv. The Apify key is used by ApifyClient to call the google-search-scraper actor. The Gemini key is used by LangChain's ChatGoogleGenerativeAI wrapper. Data leaves your app as search queries, resume text, and job snippets, then returns as search results and AI-generated JSON.
                """,
            ),
            sub("Model inference flow", code_block=MODEL_FLOW_DIAGRAM),
            sub(
                "Database flow",
                """
The current app does not use a true database. It uses Pandas to write jobs_database.csv. CSV is good for learning and demos, but a real app should use SQLite, PostgreSQL, or Supabase so jobs, users, statuses, and match reports can be queried safely.
                """,
            ),
            sub(
                "Deployment flow",
                """
A simple deployment path is Streamlit Community Cloud or Render. A stronger portfolio path is: create requirements.txt, restore missing source files, add tests, hide secrets in environment variables, deploy Streamlit, add screenshots and demo video, and write a README. If you later move to a full-stack app, Next.js plus FastAPI is also a good architecture.
                """,
            ),
            sub("Agent graph flow", code_block=AGENT_GRAPH_DIAGRAM),
        ],
        exercises=[
            "Explain the difference between data flow and API flow.",
            "Replace CSV storage in a design diagram with SQLite tables.",
            "Write a deployment checklist for Streamlit Cloud.",
        ],
        interview=[
            "Where do secrets live in this project?",
            "What data is sent to Gemini?",
            "How would you add persistent job tracking?",
        ],
        mistakes=[
            "Committing .env files to GitHub.",
            "Assuming CSV is enough for multi-user production storage.",
            "Sending too much private resume data to APIs without user consent.",
        ],
    ),
    section(
        "4. File-by-File Guide",
        """
This section explains each project file: what it is, why it exists, real-world use cases, key functions/classes, important line explanations, alternatives, exercises, and interview angles.
        """,
        [
            sub(
                "app.py - Streamlit user interface and workflow launcher",
                """
What it is: app.py is the main entry point. Streamlit runs this file and turns Python statements into a web interface.

Why used here: It lets you build a data/AI app quickly without writing HTML, CSS, and JavaScript.

Real-world use cases: AI demos, dashboards, internal tools, ML model prototypes, data analysis apps.

Key components:
- load_dotenv() loads keys from .env.
- st.file_uploader() accepts the PDF resume.
- st.session_state stores resume text between interactions.
- st.text_input() collects target role and location.
- job_agent_app.invoke(initial_state) starts the LangGraph workflow.
- st.dataframe() displays scored jobs.
- st.download_button() returns the CSV.

Important lines:
- Lines 1-6 import environment, UI, Pandas, OS, time, and the compiled agent.
- Lines 13-15 read GOOGLE_API_KEY and APIFY_API_KEY from .env.
- Lines 25-27 initialize session memory for cleaned resume text.
- Lines 34-42 save uploaded PDF, extract text, clean it, and keep it in memory.
- Lines 59-67 validate keys, role, and resume before starting the agent.
- Lines 71-80 build the agent state dictionary.
- Line 84 invokes the graph.
- Lines 91-113 display and download final results.

Current gap: app.py imports utils.pdf_reader, but utils/pdf_reader.py is missing in the current source tree.

Alternative UI tools:
- Gradio: faster for ML demos with simple input/output.
- Flask/FastAPI plus React: more flexible, more work.
- Dash: good for analytics dashboards.
                """,
                code_block='''# Minimal Streamlit pattern
import streamlit as st

st.title("AI Job Hunt Copilot")
resume = st.file_uploader("Upload resume", type=["pdf"])
role = st.text_input("Target role")

if st.button("Analyze"):
    st.write("Start the workflow here")''',
            ),
            sub(
                "agents/agent.py - LangGraph workflow controller",
                """
What it is: agents/agent.py defines a stateful graph. The graph decides what step runs next.

Why used here: A job hunt workflow has multiple steps: search, maybe retry with a broader query, score jobs, then finish. LangGraph is useful when AI apps need controlled multi-step behavior instead of one function call.

Real-world use cases: research agents, customer support workflows, multi-step data pipelines, tool-using AI assistants.

Key components:
- JobAgentState: the memory schema for the graph.
- search_for_jobs(): calls the search API.
- expand_search_query(): broadens the role when no jobs are found.
- score_found_jobs(): adds match score, fit summary, and cover letter.
- route_after_search(): decides the next node.
- StateGraph: builds the graph.
- END: marks graph completion.

Important lines:
- Lines 10-19 define the state fields carried through the workflow.
- Lines 23-41 search jobs and update raw_jobs.
- Lines 43-52 expand the search query.
- Lines 54-90 score each job.
- Lines 93-106 route based on results and attempts.
- Lines 108-137 build and compile the graph.

Current gap: search_for_jobs checks jobs != "API_ERROR", but searcher.py returns "ERROR: ...". Use a consistent error type in future code.

Alternative workflow tools:
- Plain Python functions: enough for simple linear flows.
- CrewAI: useful for multi-agent demos, sometimes heavier.
- AutoGen: good for conversation-style agents.
- Airflow/Prefect: better for scheduled production data pipelines.
                """,
                code_block='''from langgraph.graph import StateGraph, END

workflow = StateGraph(dict)
workflow.add_node("step_one", lambda state: state)
workflow.set_entry_point("step_one")
workflow.add_edge("step_one", END)
app = workflow.compile()''',
            ),
            sub(
                "searcher.py - Apify job search and CSV export",
                """
What it is: searcher.py handles job search through Apify and exports job data to CSV.

Why used here: Job boards are hard to scrape directly. Apify gives hosted scraping actors, so your app can request search results without maintaining a custom scraper.

Real-world use cases: web scraping, competitor monitoring, job listing collection, market research.

Key functions:
- find_live_jobs(job_title, location, apify_api_key, max_results): calls Apify.
- save_to_spreadsheet(jobs_data, filename): stores results as CSV and returns downloadable bytes.

Important lines:
- Lines 12-16 build the Google search query.
- Line 18 creates an ApifyClient.
- Lines 20-24 define actor input.
- Line 30 runs apify/google-search-scraper.
- Lines 33-37 safely read defaultDatasetId.
- Lines 45-59 collect organic search result links and snippets.
- Lines 67-97 save and deduplicate CSV rows.

Current gap: search results are snippets, not full job descriptions. For better matching, add a job detail fetcher that opens each job link and extracts the real description.

Alternative search/data tools:
- SerpAPI: paid search API with structured results.
- Tavily: search API designed for AI apps.
- Bright Data: enterprise scraping.
- Direct job APIs: best when available, but many job boards restrict access.
                """,
                code_block='''from apify_client import ApifyClient

client = ApifyClient("APIFY_TOKEN")
run = client.actor("apify/google-search-scraper").call(
    run_input={"queries": "Python developer remote", "resultsPerPage": 5}
)''',
            ),
            sub(
                "matcher.py - LLM fit summary and cover letter generator",
                """
What it is: matcher.py sends resume text and job text to Gemini through LangChain and parses the result as JSON.

Why used here: Numeric similarity alone cannot explain why a job fits. The LLM creates human-readable reasoning and a cover letter draft.

Real-world use cases: resume feedback, sales email generation, customer support summaries, document comparison.

Key components:
- ChatGoogleGenerativeAI: LangChain wrapper for Gemini.
- PromptTemplate: reusable prompt with variables.
- JsonOutputParser: asks model output to follow a JSON schema.
- JobMatchReport: Pydantic schema for fit_analysis and cover_letter.
- chain = prompt | llm | parser: LangChain expression language pipeline.

Important lines:
- Lines 8-10 define the output fields.
- Lines 15-19 initialize Gemini.
- Line 23 creates the JSON parser.
- Lines 26-41 define prompt text and formatting instructions.
- Line 46 chains prompt, LLM, and parser.
- Line 51 invokes the chain.
- Lines 55-60 wrap returned data in a small Report class.

Alternative model libraries:
- Direct google-genai SDK: less abstraction, more direct control.
- OpenAI SDK: alternative LLM provider.
- Instructor: great for structured outputs with Pydantic.
- Haystack: strong for retrieval pipelines.
                """,
                code_block='''from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    template="Compare resume {resume} with job {job}. {format_instructions}",
    input_variables=["resume", "job"],
)''',
            ),
            sub(
                "local_scorer.py - Embeddings and cosine similarity",
                """
What it is: local_scorer.py computes a local mathematical match score using sentence embeddings.

Why used here: It gives a fast, cheap score without calling an LLM for the numeric part. This is useful because scoring many jobs with an LLM can be slow and costly.

Real-world use cases: semantic search, recommendation systems, duplicate detection, resume-to-job matching, FAQ matching.

Key components:
- SentenceTransformer('all-MiniLM-L6-v2'): converts text to vectors.
- model.encode(): creates embeddings.
- cosine_similarity(): compares vector direction.
- final_score: percentage-like score shown to user.

Important lines:
- Lines 1-3 import embedding and math libraries.
- Line 7 loads the embedding model.
- Lines 17-22 encode resume and job text, then reshape vectors.
- Lines 26-27 compute similarity.
- Lines 30-34 convert to a percentage and add a small boost.

Current gap: import numpy as np is unused. Also, adding a fixed +15 boost can make scores feel nicer, but it reduces scientific purity. For portfolio clarity, explain it or replace with calibrated scoring.

Alternative embedding models:
- all-mpnet-base-v2: better quality, slower.
- OpenAI text-embedding models: strong hosted embeddings.
- BGE models: popular open-source retrieval embeddings.
- TF-IDF: simpler, keyword-based, weaker for semantic meaning.
                """,
                code_block='''from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(["Python APIs", "Backend Python REST API"])
score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]''',
            ),
            sub(
                "utils/extractor.py - structured resume extraction and URL title parsing",
                """
What it is: utils/extractor.py has two responsibilities. First, it defines ResumeData and extract_resume_details() for structured resume extraction. Second, it defines extract_real_title() to infer a job title from a job URL.

Why used here: Resume extraction turns raw resume text into fields such as skills, job titles, and years of experience. URL title extraction makes search result rows look more readable.

Real-world use cases: candidate profile parsing, HR automation, CRM data extraction, document information extraction.

Key components:
- ResumeData: Pydantic schema.
- extract_resume_details(): Gemini call with JSON schema.
- extract_real_title(): simple URL parsing for Naukri and LinkedIn.

Important lines:
- Lines 7-11 define expected resume fields.
- Lines 21-24 configure the Gemini model and system instruction.
- Lines 27-31 request JSON output matching ResumeData.
- Lines 34-40 call Gemini and validate JSON.
- Lines 42-71 parse job titles from known URL patterns.

Current gap: extract_resume_details() is not currently called by app.py. Connecting it is a strong next portfolio step.

Alternative extraction approaches:
- Regex: good for emails/phone numbers, weak for skills/experience.
- spaCy: good for named entity recognition.
- LLM structured output: flexible and strong, but needs validation.
- Dedicated resume parsing APIs: accurate, but paid and less educational.
                """,
                code_block='''from pydantic import BaseModel
from typing import List

class ResumeData(BaseModel):
    name: str
    skills: List[str]
    job_titles: List[str]
    total_years_experience: int''',
            ),
            sub(
                "utils/pdf_reader.py - expected PDF reader module",
                """
What it is: app.py expects this file to provide extract_text_from_pdf() and clean_text().

Current status: the source file is missing in the current workspace, although pycache files suggest it existed before. This is a critical gap because app.py imports it.

Expected purpose:
- extract_text_from_pdf(path): open PDF and extract text from each page.
- clean_text(text): normalize whitespace before sending text to scoring functions.

Alternative PDF tools:
- pypdf: simple PDF text extraction.
- pdfplumber: better for tables and layout.
- PyMuPDF: fast and strong for rendering/extraction.
- OCR with Tesseract: needed for scanned/image-only resumes.
                """,
                code_block='''from pypdf import PdfReader
import re

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\\n"
    return text

def clean_text(text):
    return re.sub(r"\\s+", " ", text).strip()''',
            ),
            sub(
                ".env and .vscode/settings.json - environment and editor config",
                """
.env stores secrets such as GOOGLE_API_KEY and APIFY_API_KEY. Do not commit .env to GitHub.

.vscode/settings.json tells VS Code/Pylance to use the project virtual environment. This helps imports resolve correctly.

Important lines in settings.json:
- Line 2 points Pylance to ${workspaceFolder}/venv/bin/python.
- Line 3 activates the environment in terminals.
- Lines 4-6 add the workspace root as an analysis path.

Alternative environment management:
- requirements.txt: simple dependency list.
- pyproject.toml: modern Python project config.
- Poetry/uv: stronger dependency locking.
- Conda: good for data science packages and system libraries.
                """,
                code_block='''# .env example, never commit real values
GOOGLE_API_KEY=your_key_here
APIFY_API_KEY=your_key_here''',
            ),
        ],
        exercises=[
            "Open each file and write one sentence explaining its responsibility.",
            "Find one current code smell and explain why it matters.",
            "Restore or create utils/pdf_reader.py in a future coding step and test app.py import.",
        ],
        interview=[
            "Why did you split the app into modules?",
            "What does LangGraph add beyond a normal function call?",
            "Why combine local embedding scoring with LLM text generation?",
        ],
    ),
    section(
        "5. Library, API, and Component Guide",
        """
This section explains the main libraries and APIs in beginner-friendly language.
        """,
        [
            sub(
                "Streamlit",
                """
What it is: a Python library for building web apps quickly.
Why used: it lets you create upload fields, buttons, tables, and downloads with Python.
Key functions: st.title, st.file_uploader, st.text_input, st.button, st.spinner, st.session_state, st.dataframe, st.download_button.
Real-world use cases: ML demos, dashboards, analytics tools.
Alternatives: Gradio for ML demos, Dash for dashboards, React/FastAPI for production flexibility.
                """,
            ),
            sub(
                "Pandas",
                """
What it is: a data table library.
Why used: job records are converted to DataFrames and saved to CSV.
Key functions: pd.DataFrame, pd.read_csv, pd.concat, drop_duplicates, to_csv.
Real-world use cases: data cleaning, analytics, exports.
Alternatives: Polars for speed, SQLite/PostgreSQL for persistence, Spark for big data.
                """,
            ),
            sub(
                "python-dotenv and os",
                """
What they are: python-dotenv loads variables from .env, and os reads them with os.getenv().
Why used: secrets should not be hard-coded in source files.
Key functions: load_dotenv(), os.getenv().
Real-world use cases: API keys, database URLs, feature flags.
Alternatives: cloud environment variables, secret managers, Docker secrets.
                """,
            ),
            sub(
                "Pydantic",
                """
What it is: a data validation library.
Why used: it defines expected shapes such as ResumeData and JobMatchReport.
Key classes: BaseModel, Field.
Real-world use cases: API schemas, LLM structured output, config validation.
Alternatives: dataclasses for simple structures, Marshmallow for serialization, TypedDict for static hints only.
                """,
            ),
            sub(
                "Google Gemini API",
                """
What it is: Google's LLM API.
Why used: it extracts resume details and generates fit summaries/cover letters.
Key classes/functions: genai.configure, genai.GenerativeModel, ChatGoogleGenerativeAI.
Real-world use cases: summarization, extraction, reasoning, content generation.
Alternatives: OpenAI, Anthropic, Mistral, local LLMs with Ollama.
Important note: google.generativeai is deprecated. The newer package is google-genai, which is already installed in the environment.
                """,
            ),
            sub(
                "LangChain",
                """
What it is: a framework for composing prompts, models, parsers, and tools.
Why used: matcher.py builds a clear prompt -> LLM -> JSON parser chain.
Key components: PromptTemplate, JsonOutputParser, LCEL pipe operator.
Real-world use cases: AI chains, document Q&A, structured output, tool calling.
Alternatives: direct SDK calls, LlamaIndex, Haystack, Instructor.
                """,
            ),
            sub(
                "LangGraph",
                """
What it is: a framework for stateful AI workflows.
Why used: agents/agent.py needs controlled steps and retry logic.
Key components: TypedDict state, StateGraph, nodes, conditional edges, END.
Real-world use cases: research agents, multi-step assistants, approval workflows.
Alternatives: plain Python, CrewAI, AutoGen, Prefect.
                """,
            ),
            sub(
                "Apify Client",
                """
What it is: a Python client for Apify scraping actors.
Why used: searcher.py uses Apify's Google Search Scraper to collect job links/snippets.
Key functions/classes: ApifyClient, client.actor(...).call(), client.dataset(...).iterate_items().
Real-world use cases: scraping, market research, search result collection.
Alternatives: SerpAPI, Tavily, Bright Data, custom scrapers.
                """,
            ),
            sub(
                "Sentence Transformers",
                """
What it is: a library for embedding text into numeric vectors.
Why used: local_scorer.py computes resume-job semantic similarity locally.
Key class/function: SentenceTransformer, model.encode().
Real-world use cases: semantic search, recommendations, clustering.
Alternatives: OpenAI embeddings, BGE embeddings, E5 embeddings, TF-IDF.
                """,
            ),
            sub(
                "scikit-learn and NumPy",
                """
What they are: machine learning and numerical computing libraries.
Why used: cosine_similarity compares vectors. NumPy supports vector shapes and arrays.
Key function: sklearn.metrics.pairwise.cosine_similarity.
Real-world use cases: classification, clustering, similarity, metrics.
Alternatives: PyTorch, TensorFlow, SciPy, pure NumPy math.
                """,
            ),
            sub(
                "pypdf",
                """
What it is: a PDF extraction library.
Why used: the expected pdf_reader.py module should extract resume text from uploaded PDF files.
Key class: PdfReader.
Real-world use cases: PDF parsing, document ingestion, text extraction.
Alternatives: pdfplumber, PyMuPDF, OCR tools.
                """,
            ),
        ],
        exercises=[
            "For each library, write whether it is UI, data, API, AI, or storage related.",
            "Replace one library in theory and explain the tradeoff.",
            "Create a requirements.txt from the packages actually needed by the project.",
        ],
        interview=[
            "Why did you choose Streamlit for this stage?",
            "Why not use only an LLM for scoring?",
            "What is the risk of scraping job websites?",
        ],
    ),
    section(
        "6. AI and ML Concepts",
        """
This project uses several practical AI concepts. Some are already implemented. Others are planned improvements that you should understand because they are common in AI interviews and real projects.
        """,
        [
            sub(
                "LLMs",
                """
What it is: A Large Language Model predicts and generates text based on patterns learned from huge datasets.
Why needed: The project needs natural language reasoning to summarize fit and write cover letters.
How it works internally: Text is split into tokens, converted into vectors, passed through transformer layers, and the model predicts likely next tokens.
Analogy: Like a highly trained autocomplete system that also learned patterns of reasoning and writing.
Practical example: Give it a resume and job snippet, ask it to produce a JSON summary.
                """,
            ),
            sub(
                "Tokenization",
                """
What it is: The process of splitting text into small pieces called tokens.
Why needed: LLMs do not read raw characters the way humans do. They process token IDs.
How it works internally: Words, word parts, punctuation, and spaces are mapped to integer IDs.
Analogy: Breaking a paragraph into puzzle pieces before sending it to the model.
Practical example: A long resume plus job description may use many tokens, which affects cost and context limit.
                """,
            ),
            sub(
                "Prompt Engineering",
                """
What it is: Designing instructions and context so an LLM returns useful output.
Why needed: A vague prompt gives vague answers. A structured prompt gives consistent fit summaries and cover letters.
How it works internally: The prompt becomes part of the token sequence that guides next-token prediction.
Analogy: Giving a junior assistant a clear task checklist instead of saying 'do something useful'.
Practical example: matcher.py tells the model it is an expert AI Career Coach and provides resume, job text, and JSON format instructions.
                """,
            ),
            sub(
                "Structured Output",
                """
What it is: Asking the model to return data in a predictable format such as JSON.
Why needed: Apps need reliable fields, not random paragraphs.
How it works internally: The prompt/parser/schema constrains or validates model output.
Analogy: Asking someone to fill a form instead of writing a free-form essay.
Practical example: JobMatchReport requires fit_analysis and cover_letter.
                """,
            ),
            sub(
                "Embeddings",
                """
What it is: Numeric vector representations of text.
Why needed: They let software compare meaning mathematically.
How it works internally: An embedding model maps text into a point in high-dimensional space. Similar meanings land near each other.
Analogy: Placing sentences on a map where similar sentences are close.
Practical example: 'Python backend APIs' and 'REST API developer using Python' should have nearby vectors.
                """,
            ),
            sub(
                "Cosine Similarity",
                """
What it is: A math formula that compares the angle between two vectors.
Why needed: local_scorer.py uses it to compare resume and job embeddings.
How it works internally: If vectors point in similar directions, similarity is high. If unrelated, it is low.
Analogy: Two arrows pointing the same way mean the texts are aligned.
Practical example: Resume vector and job vector produce a decimal that becomes a match percentage.
                """,
            ),
            sub(
                "Retrieval",
                """
What it is: Finding the most relevant information before answering.
Why needed: If the app stores many jobs, retrieval can find jobs most similar to a resume.
How it works internally: Query text becomes an embedding, then the system searches stored embeddings for nearest neighbors.
Analogy: Before answering a question, first pull the right pages from a book.
Practical example: Retrieve top 10 jobs from a job database that match the resume.
                """,
            ),
            sub(
                "Vector Database",
                """
What it is: A database optimized to store and search embeddings.
Why needed: For many resumes/jobs, normal CSV search is not enough.
How it works internally: It indexes vectors using approximate nearest neighbor algorithms.
Analogy: A library catalog organized by meaning, not alphabet.
Practical example: Store job description embeddings in Chroma, Pinecone, Weaviate, Qdrant, or FAISS.
                """,
            ),
            sub(
                "RAG",
                """
What it is: Retrieval-Augmented Generation. Retrieve relevant context, then ask an LLM to generate an answer using that context.
Why needed: It reduces hallucination and lets the model answer using your actual resume/job data.
How it works internally: User query -> retrieve relevant chunks -> insert chunks into prompt -> LLM generates answer.
Analogy: Open-book exam. The model answers after seeing the relevant notes.
Practical example: Retrieve the most relevant resume bullets and job requirements, then ask Gemini to explain gaps.
                """,
            ),
            sub(
                "Agents",
                """
What it is: An AI workflow that can choose steps, call tools, and maintain state.
Why needed: Job hunting is not one step. It needs search, retry, score, summarize, and export.
How it works internally: A state object moves through nodes. Routing logic decides next node.
Analogy: A project manager moving a task through stages.
Practical example: LangGraph retries search with a broader role when the first search finds no jobs.
                """,
            ),
            sub(
                "Temperature",
                """
What it is: A generation setting that controls randomness.
Why needed: Resume/job analysis should be consistent and factual.
How it works internally: Lower temperature makes the model choose more likely tokens. Higher temperature allows more variety.
Analogy: Low temperature is a careful checklist answer. High temperature is brainstorming.
Practical example: matcher.py uses temperature=0.2.
                """,
            ),
        ],
        exercises=[
            "Explain embeddings to a non-technical friend.",
            "Create a tiny RAG design for storing 100 job descriptions.",
            "Compare cosine similarity and LLM reasoning in one paragraph.",
        ],
        interview=[
            "What is the difference between embeddings and LLMs?",
            "What problem does RAG solve?",
            "Why does token length matter?",
            "How does a vector database differ from a normal relational database?",
        ],
        mistakes=[
            "Using the word RAG when no retrieval step exists.",
            "Treating embedding similarity as perfect truth.",
            "Letting the LLM invent missing skills without evidence.",
        ],
    ),
    section(
        "7. Important Code Walkthroughs",
        """
This section gives line-by-line explanations for the most important code paths.
        """,
        [
            sub(
                "app.py startup and environment",
                """
Lines 1-6 import libraries and the compiled agent. Lines 13-15 load secrets from .env. This is good because API keys stay outside code. Lines 17-18 configure the Streamlit page and title.
                """,
                code_block='''load_dotenv()
gemini_key = os.getenv("GOOGLE_API_KEY")
serper_key = os.getenv("APIFY_API_KEY")''',
            ),
            sub(
                "app.py resume upload",
                """
Line 32 creates the PDF uploader. Lines 34-37 save the uploaded PDF as temp_resume.pdf. Line 39 extracts text. Line 40 cleans the text. The cleaned text becomes the resume knowledge base for later scoring.
                """,
                code_block='''uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=["pdf"])
if uploaded_file is not None:
    with open("temp_resume.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())''',
            ),
            sub(
                "app.py agent invocation",
                """
Lines 71-80 create initial_state. This dictionary is the agent memory. It contains target role, location, resume text, keys, attempts, raw jobs, and scored jobs. Line 84 sends that state into LangGraph. The graph returns final_state.
                """,
                code_block='''initial_state = {
    "target_role": target_role,
    "location": search_location,
    "resume_text": st.session_state.cleaned_text,
    "gemini_key": gemini_key,
    "apify_key": serper_key,
    "search_attempts": 0,
    "raw_jobs": [],
    "scored_jobs": []
}
final_state = job_agent_app.invoke(initial_state)''',
            ),
            sub(
                "agents/agent.py search node",
                """
search_for_jobs receives state, calls find_live_jobs, stores jobs in state['raw_jobs'], increments attempts, and returns state. In graph-based programming, every node receives and returns state.
                """,
                code_block='''jobs = find_live_jobs(
    state["target_role"],
    state["location"],
    state["apify_key"],
    max_results=5
)''',
            ),
            sub(
                "agents/agent.py scoring node",
                """
score_found_jobs loops through every raw job. It uses the snippet as job_desc. It standardizes keys such as link, title, and company. It computes a local Match Score, then asks Gemini for Fit Summary and Cover Letter Draft.
                """,
                code_block='''math_score = calculate_local_match_score(state["resume_text"], job_desc)
job["Match Score"] = f"{math_score}%"
report = analyze_job_fit(state["resume_text"], job_desc, state["gemini_key"])
job["Fit Summary"] = report.fit_analysis
job["Cover Letter Draft"] = report.cover_letter''',
            ),
            sub(
                "matcher.py chain",
                """
The chain is prompt | llm | parser. That means the input fills the prompt, the prompt goes to Gemini, and the Gemini output is parsed into JSON. This pattern is clean because every stage has one job.
                """,
                code_block='''parser = JsonOutputParser(pydantic_object=JobMatchReport)
chain = prompt | llm | parser
result = chain.invoke({"resume": resume_text, "job": job_desc})''',
            ),
            sub(
                "local_scorer.py vector score",
                """
model.encode() turns text into vectors. reshape(1, -1) makes each vector a 2D array because cosine_similarity expects rows of vectors. raw_score is multiplied by 100 and rounded.
                """,
                code_block='''embeddings = model.encode([resume_text, job_desc])
resume_vector = embeddings[0].reshape(1, -1)
job_vector = embeddings[1].reshape(1, -1)
raw_score = cosine_similarity(resume_vector, job_vector)[0][0]''',
            ),
            sub(
                "searcher.py CSV save",
                """
The function converts jobs into a DataFrame. If jobs_database.csv already exists, it reads existing rows, concatenates old and new, removes duplicates by link, saves the final table, and returns CSV bytes for the Streamlit download button.
                """,
                code_block='''new_df = pd.DataFrame(jobs_data)
combined_df = pd.concat([existing_df, new_df])
final_df = combined_df.drop_duplicates(subset=["link"], keep="first")
csv_for_download = final_df.to_csv(index=False).encode("utf-8")''',
            ),
        ],
        exercises=[
            "Trace one resume upload from app.py to final DataFrame.",
            "Write comments for the scoring node in your own words.",
            "Change the mental model from 'functions' to 'state moving through graph nodes'.",
        ],
        interview=[
            "What does chain = prompt | llm | parser mean?",
            "Why does the graph return final_state?",
            "Why do we reshape vectors before cosine similarity?",
        ],
    ),
    section(
        "8. Best Practices and Common Mistakes",
        """
These are the engineering practices that make the project stronger and safer.
        """,
        [
            sub(
                "Best practices",
                bullets(
                    [
                        "Keep secrets in .env locally and deployment environment variables in production.",
                        "Create requirements.txt or pyproject.toml so others can install dependencies.",
                        "Restore missing source files instead of relying on pycache.",
                        "Use structured output schemas for LLM responses.",
                        "Validate all API responses before looping over them.",
                        "Separate UI, search, scoring, model calls, and storage into modules.",
                        "Use full job descriptions when possible, not only snippets.",
                        "Add tests for title extraction, PDF cleaning, score function, and error routing.",
                        "Show evidence for match score: matched skills, missing skills, weak evidence, and resume wording gaps.",
                        "Respect website terms and user privacy when scraping and sending resume data to APIs.",
                    ]
                ),
            ),
            sub(
                "Common mistakes in this project type",
                bullets(
                    [
                        "Calling every AI app a RAG app even when there is no retrieval pipeline.",
                        "Using only keyword overlap and missing semantic matches.",
                        "Using only LLM judgment and getting inconsistent scores.",
                        "Not handling scanned PDFs.",
                        "Letting the app crash when an API returns an error string.",
                        "Hard-coding API keys.",
                        "Not explaining why a score was given.",
                        "Forgetting that job snippets are incomplete job descriptions.",
                    ]
                ),
            ),
            sub(
                "Recommended next implementation roadmap",
                """
Phase 1: Restore utils/pdf_reader.py and add requirements.txt.
Phase 2: Connect extract_resume_details() and show extracted profile.
Phase 3: Suggest target roles from extracted resume data.
Phase 4: Fetch full job descriptions from links.
Phase 5: Expand match report schema to include matched_skills, missing_skills, weak_evidence, missing_keywords, experience_gap, and resume_improvements.
Phase 6: Replace CSV with SQLite.
Phase 7: Add tests and README.
Phase 8: Deploy and record a demo video.
                """,
            ),
        ],
        exercises=[
            "Turn the roadmap into GitHub issues.",
            "Write a test case for extract_real_title().",
            "Design a better MatchReport schema.",
        ],
        interview=[
            "What did you do to reduce hallucination?",
            "How do you validate LLM output?",
            "What would you improve first if given one week?",
        ],
    ),
    section(
        "9. Portfolio Presentation Guide",
        """
A portfolio project should tell a story: problem, solution, architecture, demo, technical depth, limitations, and next steps.
        """,
        [
            sub(
                "README structure",
                """
Recommended README sections:
1. Project title and one-line summary.
2. Demo GIF or screenshots.
3. Problem statement.
4. Features.
5. Architecture diagram.
6. Tech stack.
7. How it works.
8. Setup instructions.
9. Environment variables.
10. Current limitations.
11. Future roadmap.
12. What I learned.
                """,
            ),
            sub(
                "Features to highlight",
                bullets(
                    [
                        "Resume upload and parsing.",
                        "Autonomous job search workflow.",
                        "Local semantic match scoring with embeddings.",
                        "LLM-generated fit summaries and cover letters.",
                        "CSV export and duplicate prevention.",
                        "Planned structured gap analysis and role inference.",
                    ]
                ),
            ),
            sub(
                "How to explain it in interviews",
                """
Use this short explanation:

I built an AI Job Hunt Copilot that accepts a resume, searches job listings, ranks them using local embedding similarity, and uses Gemini to explain fit and generate a cover letter. The app uses Streamlit for UI, Apify for search, LangGraph for workflow control, Sentence Transformers for local semantic scoring, LangChain for prompt/model/parser composition, and Pandas for CSV export. The next step is to fetch full job descriptions and store reports in SQLite.
                """,
            ),
        ],
        exercises=[
            "Write your 30-second, 2-minute, and 5-minute project explanation.",
            "Create a screenshot checklist for the final README.",
            "Prepare one slide explaining the architecture.",
        ],
        interview=[
            "What tradeoffs did you make?",
            "How would you scale this app?",
            "What would you change for production?",
        ],
    ),
    section(
        "10. Interview Questions and Practice Answers",
        """
Use these to prepare for portfolio discussions.
        """,
        [
            sub(
                "Beginner questions",
                """
Q: What is Streamlit?
A: Streamlit is a Python framework that turns Python scripts into interactive web apps.

Q: What is an embedding?
A: An embedding is a numeric vector that represents the meaning of text.

Q: Why use cosine similarity?
A: It measures how similar two embedding vectors are by comparing their direction.
                """,
            ),
            sub(
                "Intermediate questions",
                """
Q: Why combine embeddings with an LLM?
A: Embeddings give fast, cheap similarity scores. The LLM gives human-readable reasoning and cover letters. Together they are more useful than either alone.

Q: What is LangGraph doing?
A: It controls a stateful workflow: search jobs, retry if needed, score jobs, then end.

Q: How do you avoid unreliable LLM output?
A: Use clear prompts, low temperature, structured output schemas, validation, and evidence from retrieved data.
                """,
            ),
            sub(
                "Advanced questions",
                """
Q: How would you add RAG?
A: Store resume chunks and job description chunks as embeddings in a vector database. Retrieve the most relevant chunks for each job, then pass only those chunks to the LLM for gap analysis.

Q: How would you add a real database?
A: Start with SQLite tables for resumes, jobs, match_reports, and applications. For deployment and multi-user access, move to PostgreSQL or Supabase.

Q: How would you evaluate match score quality?
A: Create a small labeled dataset of resume/job pairs, compare model scores with human labels, measure rank correlation, and tune scoring weights.
                """,
            ),
        ],
        exercises=[
            "Record yourself answering five questions.",
            "Write one technical deep dive about embeddings.",
            "Write one limitation and one improvement for each module.",
        ],
    ),
    section(
        "11. Full Source Snapshot",
        """
This snapshot captures the current source files that the manual was based on. Keep this section as a learning reference.
        """,
        [
            sub("app.py", code_block=CURRENT_SOURCE["app.py"]),
            sub("agents/agent.py", code_block=CURRENT_SOURCE["agents/agent.py"]),
            sub("matcher.py", code_block=CURRENT_SOURCE["matcher.py"]),
            sub("searcher.py", code_block=CURRENT_SOURCE["searcher.py"]),
            sub("local_scorer.py", code_block=CURRENT_SOURCE["local_scorer.py"]),
            sub("utils/extractor.py", code_block=CURRENT_SOURCE["utils/extractor.py"]),
            sub("utils/pdf_reader.py", code_block=CURRENT_SOURCE["utils/pdf_reader.py"]),
            sub(".vscode/settings.json", code_block=CURRENT_SOURCE[".vscode/settings.json"]),
        ],
    ),
]


def make_markdown() -> str:
    parts = [
        "# AI Job Hunt Agent Learning Guide",
        "",
        "Generated for `/Users/akbar/job-hunt-agent`.",
        "",
        "This manual explains concepts, implementation, architecture, project gaps, best practices, interview questions, and exercises.",
        "",
    ]
    for sec in sections:
        parts.append(f"## {sec['title']}")
        if sec["body"]:
            parts.append(sec["body"])
        for item in sec["subsections"]:
            parts.append(f"### {item['title']}")
            if item["body"]:
                parts.append(item["body"])
            if item["code"]:
                parts.append("```")
                parts.append(item["code"])
                parts.append("```")
        if sec["mistakes"]:
            parts.append("### Common mistakes")
            parts.extend(f"- {x}" for x in sec["mistakes"])
        if sec["exercises"]:
            parts.append("### Exercises")
            parts.extend(f"- {x}" for x in sec["exercises"])
        if sec["interview"]:
            parts.append("### Interview questions")
            parts.extend(f"- {x}" for x in sec["interview"])
        parts.append("")
    return "\n".join(parts)


class NumberedCanvas:
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc

    def __call__(self, canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(0.65 * inch, 0.45 * inch, "AI Job Hunt Agent Learning Guide")
        canvas.drawRightString(width - 0.65 * inch, 0.45 * inch, f"Page {doc.page}")
        canvas.restoreState()


def build_pdf():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            "SmallCenter",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#111827"),
            spaceBefore=12,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "SubTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1F2937"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyText2",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#111827"),
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "Note",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#374151"),
            backColor=colors.HexColor("#F3F4F6"),
            borderColor=colors.HexColor("#D1D5DB"),
            borderWidth=0.5,
            borderPadding=7,
            spaceBefore=6,
            spaceAfter=8,
        )
    )

    story = []
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("AI Job Hunt Agent", styles["CoverTitle"]))
    story.append(Paragraph("Complete Beginner Learning Guide and Technical Manual", styles["CoverTitle"]))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("Project path: /Users/akbar/job-hunt-agent", styles["SmallCenter"]))
    story.append(Paragraph("Focus: concepts, architecture, implementation, APIs, AI/ML, best practices, interviews, and exercises", styles["SmallCenter"]))
    story.append(PageBreak())

    toc_rows = [["Section", "Focus"]]
    for sec in sections:
        toc_rows.append([sec["title"], "Concepts, implementation, exercises, and interview prep"])
    table = Table(toc_rows, colWidths=[2.3 * inch, 4.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ]
        )
    )
    story.append(Paragraph("Table of Contents", styles["SectionTitle"]))
    story.append(table)
    story.append(PageBreak())

    for sec in sections:
        story.append(Paragraph(safe(pdf_text(sec["title"])), styles["SectionTitle"]))
        if sec["body"]:
            for para in sec["body"].split("\n\n"):
                if para.strip():
                    story.append(Paragraph(safe(pdf_text(para.strip())).replace("\n", "<br/>"), styles["BodyText2"]))
        for item in sec["subsections"]:
            story.append(Paragraph(safe(pdf_text(item["title"])), styles["SubTitle"]))
            if item["body"]:
                for para in item["body"].split("\n\n"):
                    if para.strip():
                        story.append(Paragraph(safe(pdf_text(para.strip())).replace("\n", "<br/>"), styles["BodyText2"]))
            if item["code"]:
                story.append(
                    Preformatted(
                        pdf_text(item["code"]),
                        ParagraphStyle(
                            "Code",
                            fontName="Courier",
                            fontSize=6.5 if len(item["code"].splitlines()) > 30 else 8,
                            leading=8 if len(item["code"].splitlines()) > 30 else 10,
                            textColor=colors.HexColor("#111827"),
                            backColor=colors.HexColor("#F9FAFB"),
                            borderColor=colors.HexColor("#E5E7EB"),
                            borderWidth=0.5,
                            borderPadding=6,
                            spaceBefore=4,
                            spaceAfter=8,
                        ),
                        maxLineLength=100,
                    )
                )
        if sec["mistakes"]:
            story.append(Paragraph("Common mistakes", styles["SubTitle"]))
            story.append(Paragraph(safe(pdf_text(bullets(sec["mistakes"]))).replace("\n", "<br/>"), styles["Note"]))
        if sec["exercises"]:
            story.append(Paragraph("Exercises", styles["SubTitle"]))
            story.append(Paragraph(safe(pdf_text(bullets(sec["exercises"]))).replace("\n", "<br/>"), styles["Note"]))
        if sec["interview"]:
            story.append(Paragraph("Interview questions", styles["SubTitle"]))
            story.append(Paragraph(safe(pdf_text(bullets(sec["interview"]))).replace("\n", "<br/>"), styles["Note"]))
        story.append(PageBreak())

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.7 * inch,
    )
    footer = NumberedCanvas(None, None)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MD_PATH.write_text(make_markdown(), encoding="utf-8")
    build_pdf()
    print(PDF_PATH)
    print(MD_PATH)


if __name__ == "__main__":
    main()
