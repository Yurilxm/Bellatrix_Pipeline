from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
from pipeline_runner import executar_pipeline
from core.cutter import get_video_metadata

app = FastAPI(title="Bellatrix Pipeline API", version="1.3")

# Monta a pasta atual para servir os vídeos para o frontend
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/processar")
async def processar_video(
    file: UploadFile = File(...), 
    duracao_alvo: int = Form(180), 
    plataforma: str = Form("web"), # Mudamos o padrão para WEB para facilitar o teste no navegador
    texto_materia: str = Form(""),
    prompt_customizado: str = Form(""),
    programa: str = Form(""),
    editoria: str = Form(""),
    perfil: str = Form("")
):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    
    contexto = f"Programa: {programa}, Editoria: {editoria}, Perfil: {perfil}"
    
    try:
        resultados = executar_pipeline(temp_path, duracao_alvo, plataforma, texto_materia, prompt_customizado, contexto)
        # Converte os caminhos absolutos para URLs acessíveis pelo frontend
        urls = [f"/static/{os.path.basename(r)}" for r in resultados]
        return JSONResponse(status_code=200, content={"status": "success", "arquivos": urls})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
