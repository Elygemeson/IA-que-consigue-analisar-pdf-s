import pdfplumber
import google.generativeai as genai
from pymongo import MongoClient                                              #Blibliotecas desejadas
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Inicializa o FastAPI
app = FastAPI()

# Middleware para permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos os origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações do MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client['elibas']
collection = db['respostas']

# Função para extrair texto do PDF
def extract_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

# Configurações do Google Generative AI
genai.configure(api_key='YOUR_API_KEY')  # Substitua 'YOUR_API_KEY' pela sua chave de API

# Variável para armazenar o conteúdo do PDF processado
pdf_content = {}

# Endpoint raiz
@app.get("/")
async def root():
    return {"message": "Bem-vindo à API de Análise de Contratos!"}

# 1. Endpoint para upload do PDF e processamento pela IA
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Extrai o texto do PDF enviado pelo usuário
    text = extract_pdf(file.file)

    # Armazena o conteúdo do PDF no MongoDB
    data = {
        "filename": file.filename,
        "content": text,
    }
    collection.insert_one(data)

    # Armazena o conteúdo do PDF em uma variável global para ser acessada posteriormente
    pdf_content[file.filename] = text

    # Retorna uma mensagem informando que o PDF foi processado
    return JSONResponse(content={"message": "PDF processado com sucesso. Agora, faça uma pergunta sobre o conteúdo."})

# 2. Função para gerar a resposta da IA
def gerar_resposta(texto_pdf, pergunta):
    try:
        # Formata o prompt para a IA
        prompt = f"Texto do contrato:\n{texto_pdf}\n\nPergunta: {pergunta}"

        # Gera a resposta usando o modelo
        response = genai.generate_text(
            model="text-bison-001",  # Modelo compatível
            prompt=prompt,
            temperature=0.5,
            max_output_tokens=1000
        )

        # Verifica se há uma resposta válida
        if response and "candidates" in response:
            return response['candidates'][0]['output']
        else:
            return "Não foi possível gerar uma resposta."
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

# 3. Endpoint para o usuário enviar uma pergunta sobre o PDF já processado
@app.post("/perguntar/")
async def perguntar(filename: str, pergunta: str = Form(...)):
    # Verifica se o PDF foi processado
    if filename not in pdf_content:
        return JSONResponse(content={"error": "O PDF não foi processado ou o nome do arquivo está incorreto."}, status_code=400)

    # Obtém o conteúdo do PDF processado
    text = pdf_content[filename]

    # Gera a resposta da IA
    resposta_ia = gerar_resposta(text, pergunta)

    # Armazena a resposta da IA no MongoDB
    resposta_armazenada = {
        "filename": filename,
        "pergunta": pergunta,
        "ia_response": resposta_ia
    }
    collection.insert_one(resposta_armazenada)

    # Retorna a resposta da IA como JSON
    return JSONResponse(content={"resposta": resposta_ia})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)


