from sentence_transformers import SentenceTransformer

# Load the model once and reuse it across the application
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")