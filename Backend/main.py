from fastapi import FastAPI, UploadFile, File #UploadFile = tells FastAPI we're receiving an uploaded file.File = tells FastAPI that this parameter comes from a file upload.
from fastapi.middleware.cors import CORSMiddleware

from Backend.vector_db import rag_answer, index_pdf #rag answer= "Go to vector_db.py and give me the rag_answer function."

app = FastAPI()

# Allow the frontend to communicate with FastAPI; Cross-origin" means they are running at different addresses/ports. eg js is port 3000 and fastapi is port 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/") #added as health check, when someone visits the root url of my api, it tells me my api is running
def home():
    return{"message":"RAG API is running"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"Backend/uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    index_pdf(file_path)

    return {"message": "PDF uploaded successfully", "filename": file.filename}

@app.post("/ask")
def ask_question(data:dict): #data is expected to be a Python dictionary."
    query = data.get("question") #Go into the data dictionary(from js) and get the value associated with the key "question"."
    file_name = data.get("file")
    if not query:
        return {"error": "No question provided"}
    answer = rag_answer(query, file_name)

    return {"answer":answer}
