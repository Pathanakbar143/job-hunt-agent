from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1. Load a lightweight, super-fast embedding model directly to your machine
# This model converts sentences into 384-dimensional math vectors
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_local_match_score(resume_text: str, job_desc: str) -> int:
    """
    Converts text to vectors and calculates the mathematical Cosine Similarity.
    Returns a score out of 100.
    """
    try:
        # 2. Convert the texts into numbers (Embeddings)
        # We put them in a list so the model processes them together
        embeddings = model.encode([resume_text, job_desc])
        
        # embeddings[0] is the resume vector
        # embeddings[1] is the job description vector
        resume_vector = embeddings[0].reshape(1, -1)
        job_vector = embeddings[1].reshape(1, -1)
        
        # 3. Calculate the Cosine Similarity (The Dot Product math!)
        # This returns a decimal between 0 and 1 (e.g., 0.85)
        similarity_matrix = cosine_similarity(resume_vector, job_vector)
        raw_score = similarity_matrix[0][0]
        
        # 4. Convert the decimal to a nice clean percentage (e.g., 85)
        percentage_score = int(round(raw_score * 100))
        
        # A little buffer: vector matching can be harsh, so we can boost it slightly
        # just to make the scores feel more human-readable.
        final_score = min(100, percentage_score + 15) 
        
        return final_score
        
    except Exception as e:
        print(f"Vector Math Error: {e}")
        return 0