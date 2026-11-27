from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
from pipeline_runner import executar_pipeline
from core.cutter import get_video_metadata

app = FastAPI(title="Bellatrix Pipeline API", version="1.3")

# Pasta dedicada para arquivos gerados (segurança: não expõe código fonte)
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

@app.get("/")
def read_root():
    # Serve o frontend de teste
    return FileResponse("frontend_teste.html")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/processar")
async def processar_video(
    file: UploadFile = File(...),
    duracao_alvo: int = Form(180),
    plataforma: str = Form("web"),
    texto_materia: str = Form(""),
    prompt_customizado: str = Form(""),
    programa: str = Form(""),
    editoria: str = Form(""),
    perfil: str = Form("")
):
    # Validação básica de upload
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um vídeo")

    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)

    contexto = f"Programa: {programa}, Editoria: {editoria}, Perfil: {perfil}"

    try:
        resultados = executar_pipeline(temp_path, duracao_alvo, plataforma, texto_materia, prompt_customizado, contexto)
        # Move arquivos para pasta de output e retorna URLs relativas
        urls = []
        for r in resultados:
            if os.path.exists(r):
                dest = os.path.join(OUTPUT_DIR, os.path.basename(r))
                shutil.move(r, dest)
                urls.append(f"/output/{os.path.basename(r)}")
        return JSONResponse(status_code=200, content={"status": "success", "arquivos": urls})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
