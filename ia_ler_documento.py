

import pdfplumber
import google.generativeai as genai
from pymongo import MongoClient
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse



app = FastAPI()


client = MongoClient("mongodb://localhost:27017/")
db = client['pdf_database']
collection = db['pdf_data']

def extract_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text


extracted_text = extract_pdf("contratoex1.pdf")


genai.configure(api_key='AIzaSyCRKSFElXQsOIy43J45WLK0C9QAfmxObTM')

from google.generativeai.types import HarmCategory, HarmBlockThreshold

generation_config = {
    "temperature": 0.5,
    "top_k": 0,
    "top_p": 0.95,
    "max_output_tokens": 1000,
}

safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }

model_name = "gemini-1.5-flash"

model = genai.GenerativeModel(
    model_name = model_name,
    safety_settings=safety_settings,
    generation_config=generation_config
)

@app.post("/contratoex1.pdf/")
async def upload_pdf(file: UploadFile = File(...)):

    text = extract_pdf(file.file)


    data = {
        "filename": file.filename,
        "content": text,
    }
    collection.insert_one(data)



   


text = extract_pdf("contratoex1.pdf") # Make sure 'contratoex1.pdf' is in the correct directory
gemini = model.start_chat(history=[
    {
        "role": "user",
        "parts": [
            {"text": text}, # Now 'text' is defined and accessible in this scope
            {"text": "Você é um especialista em análise de contratos"}
        ]
    }
])


messagem = input("Digite sua mensagem: ")

gemini.send_message(messagem)

print(gemini.last.text)


