from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
from pipeline_runner import executar_pipeline
from core.cutter import get_video_metadata

app = FastAPI(title="Bellatrix Pipeline API", version="1.1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/metadata")
async def obter_metadados(file: UploadFile = File(...)):
    """Retorna metadados do vídeo para interface de edição manual (Integração Nano)."""
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        metadata = get_video_metadata(temp_path)
        return JSONResponse(status_code=200, content=metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/processar")
async def processar_video(file: UploadFile = File(...), duracao_alvo: int = 180, formato: str = "mp4"):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        resultado = executar_pipeline(temp_path, duracao_alvo, formato)
        return JSONResponse(status_code=200, content={"status": "success", "arquivo": resultado})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
