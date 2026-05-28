from fastapi import FastAPI, UploadFile, File
import uvicorn
import shutil
import os
from fastapi.middleware.cors import CORSMiddleware

# Importamos a sua função Mestra blindada do motor6
from motor7 import extrair_boletos_em_lote

app = FastAPI(title="Motor de Extração")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"], # Permite POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

@app.post("/api/extrair")
async def extrair_fatura_endpoint(arquivo: UploadFile = File(...)):
    # 1. Cria um arquivo temporário seguro na máquina virtual
    caminho_temporario = f"temp_{arquivo.filename}"
    
    try:
        # 2. Salva o PDF recebido via internet no disco local
        with open(caminho_temporario, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
            
        # 3. Dispara o seu motor procedural
        resultado = extrair_boletos_em_lote(caminho_temporario)
        
        # 4. Limpa o arquivo temporário do servidor (Segurança e Espaço)
        os.remove(caminho_temporario)
        
        # 5. Devolve o JSON final para o frontend
        return resultado
        
    except Exception as e:
        # Garante que o arquivo seja deletado mesmo se o servidor colapsar
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)
        return {"status": "erro", "mensagem": "Erro interno no servidor da API."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)