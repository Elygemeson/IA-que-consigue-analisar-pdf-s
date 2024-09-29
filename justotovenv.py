import pdfplumber
import google.generativeai as genai
from pymongo import MongoClient
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

# Inicializando o FastAPI
app = FastAPI()

# Conexão com o MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['pdf_database']
collection = db['pdf_data']

# Função para extrair texto de um PDF
def extract_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Configurando a API do Google Generative AI
genai.configure(api_key='AIzaSyCRKSFElXQsOIy43J45WLK0C9QAfmxObTM')

generation_config = {
    "temperature": 0.5,
    "top_k": 0,
    "top_p": 0.95,
    "max_output_tokens": 1000,
}

# Rota para upload de PDF e análise
@app.post("/analyze_pdf/")
async def analyze_pdf(file: UploadFile = File(...)):

    # Salvando o PDF temporariamente e lendo o conteúdo
    pdf_bytes = await file.read()
    with open(f"temp_{file.filename}", "wb") as f:
        f.write(pdf_bytes)

    # Extraindo o texto do PDF
    extracted_text = extract_pdf(f"temp_{file.filename}")

    # Salvando o texto extraído no MongoDB
    data = {
        "filename": file.filename,
        "content": extracted_text,
    }
    collection.insert_one(data)

    # Iniciando o chat com o modelo da Google
    history = [
        {
            "role": "user",
            "parts": [
                {"text": extracted_text},
                {"text": "Você é um especialista em análise de contratos."}
            ]
        }
    ]

    # Enviando o texto para a IA do Google para análise
    gemini_response = genai.chat(model="gemini-1.5-flash", history=history, **generation_config)

    # Retornando a resposta gerada pela IA
    return JSONResponse(content={"response": gemini_response["messages"][0]["text"]})

# Fechar a conexão com o MongoDB quando o FastAPI for encerrado
@app.on_event("shutdown")
def shutdown_db_client():
    client.close()

# Rota inicial para testar a API
@app.get("/")
def root():
    return {"message": "API de análise de contratos está rodando. Acesse /analyze_pdf para fazer o upload de um PDF."}
