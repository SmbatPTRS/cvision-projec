from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from services.matching import find_best_match
from services.cv_extract import extract_cv_text
from models.model_loader import model


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/find-match")
async def find_match(file: UploadFile = File(...)):
    # Check file type
    if file.content_type != "application/pdf":
        return JSONResponse({"error": "File must be a PDF"}, status_code=400)

    # Read file bytes
    pdf_bytes = await file.read()

    cv_text = extract_cv_text(pdf_bytes)

    cv_embedding = model.encode(cv_text, convert_to_tensor=False)

    matches = find_best_match(cv_embedding)
    print(matches)
    return {"matches": matches}









