from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# --- 1. THE BLUEPRINT (Structured Output) ---
# We define exactly what we want back. LangChain handles forcing the LLM to output this exact JSON format.
class JobMatchReport(BaseModel):
    job_title: str = Field(description="The official job title extracted from the job description or link.")
    company_name: str = Field(description="The company name extracted from the job description or link.")
    fit_analysis: str = Field(description="A 2-sentence summary of why they are a good fit or what they are missing.")
    cover_letter: str = Field(description="A short, 3-paragraph cover letter tailored specifically to this company and role.")
    

def analyze_job_fit(resume_text, job_desc, gemini_key):
    # --- 2. INITIALIZE THE LLM ---
    # We set temperature to 0.2 so the AI is highly factual and doesn't hallucinate skills.
    # llm = ChatGoogleGenerativeAI(
    #     model="gemini-2.5-flash",
    #     google_api_key=gemini_key,
    #     temperature=0.2 
    # )
    llm = ChatGroq(
       model="llama-3.1-8b-instant", # Extremely fast, smart open-source model
       groq_api_key=groq_api_key,   # Pass your new Groq key here
       temperature=0.2
   )

    # --- 3. SET UP THE PARSER ---
    # We tell LangChain to use our blueprint from Step 1
    parser = JsonOutputParser(pydantic_object=JobMatchReport)

    # --- 4. CREATE THE PROMPT TEMPLATE ---
    prompt = PromptTemplate(
        template="""You are an expert AI Career Coach and Recruiter. 
        Analyze the candidate's Resume against the Target Job Description.
        
        Resume KNOWLEDGE BASE:
        {resume}
        
        TARGET JOB DESCRIPTION:
        {job}
        
        {format_instructions}
        """,
        input_variables=["resume", "job"],
        # This magically injects the JSON rules into the prompt so the LLM knows what to do
        partial_variables={"format_instructions": parser.get_format_instructions()} 
    )

    # --- 5. BUILD THE CHAIN ---
    # This is the magic of LangChain. Data flows left to right:
    # Prompt is filled -> sent to LLM -> output is parsed into our JSON Blueprint
    chain = prompt | llm | parser

    # --- 6. EXECUTE ---
    try:
        # We pass in our variables and trigger the chain
        result = chain.invoke({"resume": resume_text, "job": job_desc})
        
        
        # We wrap the dictionary in a simple class so it works seamlessly 
        # with your existing app.py code (report.match_percentage, etc.)
        print("GROQ Model Result :- ",result)
        class Report:
            def __init__(self, data):
                self.job_title = data.get("job_title")
                self.company_name = data.get("company_name")
                self.fit_analysis = data.get("fit_analysis")
                self.cover_letter = data.get("cover_letter")
                
                
        return Report(result)   
    except Exception as e:
        print(f"LangChain Error: {e}")
        # Return empty/fallback values if something goes wrong
        class ErrorReport:
            match_percentage = 0
            fit_analysis = "Error analyzing fit."
            cover_letter = "Error generating letter."
            job_title = "Unknown Title"
            company_name = "Unknown Company"
        return ErrorReport()