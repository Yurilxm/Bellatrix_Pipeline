from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import shutil
import os
from pipeline_runner import executar_pipeline
from core.cutter import get_video_metadata

app = FastAPI(title="Bellatrix Pipeline API", version="1.2")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/metadata")
async def obter_metadados(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    try:
        return JSONResponse(status_code=200, content=get_video_metadata(temp_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.post("/processar")
async def processar_video(
    file: UploadFile = File(...), 
    duracao_alvo: int = Form(180), 
    formato: str = Form("mxf"),
    texto_materia: str = Form(""),
    prompt_customizado: str = Form("")
):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
    try:
        # Retorna uma lista com os caminhos dos 3 vídeos gerados
        resultados = executar_pipeline(temp_path, duracao_alvo, formato, texto_materia, prompt_customizado)
        return JSONResponse(status_code=200, content={"status": "success", "arquivos": resultados})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
