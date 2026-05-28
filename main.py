import os
import io
import google.auth
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import translate_v3 as translate
from pypdf import PdfReader, PdfWriter
import datetime
from supabase import create_client, Client
from typing import Optional

import sys
import subprocess
import uuid
import asyncio

translation_jobs = {}


def get_base_path():
    """Retorna o caminho base correto para desenvolvimento ou executável (PyInstaller)"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

app = FastAPI(title="Servsolda PDF Translator")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_PATH, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_PATH, "templates"))

# --- Supabase SSO ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None

# Limite máximo de páginas por chamada à API do Google
MAX_PAGES_PER_CHUNK = 20


def get_gcp_project_id():
    """
    Obtém o Project ID e as credenciais GCP.

    Ordem de prioridade (ID):
    1. Variável de ambiente GCP_PROJECT_ID
    2. Arquivo JSON de Service Account
    3. ADC (fallback)
    """
    import json
    from google.oauth2 import service_account

    env_project_id = os.environ.get("GCP_PROJECT_ID")

    # 1. Arquivo local de Service Account (pasta segura fora do projeto)
    appdata = os.environ.get("APPDATA", "")
    local_key_path = os.path.join(appdata, "ServsoldaTradutor", "gcp-service-account.json")
    if os.path.exists(local_key_path):
        try:
            with open(local_key_path, "r", encoding="utf-8") as f:
                info = json.load(f)
            scopes = ["https://www.googleapis.com/auth/cloud-translation"]
            credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
            print(f"✓ Credenciais carregadas do arquivo local: {local_key_path}")
            return info.get("project_id"), credentials
        except Exception as e:
            print(f"Erro ao carregar Service Account local ({local_key_path}): {e}")

    # 2. Variável de ambiente com conteúdo JSON (útil para Render/Railway)
    service_account_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            # Remover UTF-8 BOM se existir (comum no Windows/PowerShell)
            if service_account_json.startswith('\ufeff'):
                service_account_json = service_account_json[1:]
            
            info = json.loads(service_account_json)
            scopes = ["https://www.googleapis.com/auth/cloud-translation"]
            credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
            print("✓ Credenciais carregadas da variável de ambiente GCP_SERVICE_ACCOUNT_JSON")
            return info.get("project_id"), credentials
        except Exception as e:
            print(f"Erro ao carregar GCP_SERVICE_ACCOUNT_JSON: {e}")

    # 3. Application Default Credentials (ADC) — fallback
    try:
        credentials, project_id = google.auth.default()
        print(f"✓ Credenciais carregadas via Application Default Credentials (ADC). Projeto: {project_id}")
        return project_id, credentials
    except Exception as e:
        print(f"✗ Não foi possível carregar as credenciais GCP: {e}")
        return None, None


@app.post("/reauth")
async def reauthenticate():
    """
    Executa o comando de reautenticação do gcloud.
    No Windows (Desktop), abre o navegador. No Docker, orienta o usuário.
    """
    is_docker = os.path.exists('/.dockerenv')
    
    if is_docker:
        # Se estiver no Docker, não conseguimos abrir o navegador do host
        return {
            "status": "docker", 
            "message": "Para reconectar rodando no Docker, você deve rodar o comando: 'gcloud auth application-default login' no terminal do seu Windows (fora do Docker)."
        }

    try:
        # Tenta rodar o login ADC
        subprocess.Popen(["gcloud", "auth", "application-default", "login"], shell=True)
        return {"status": "success", "message": "Janela de login aberta no navegador."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar reautenticação: {str(e)}")


def get_translate_client():
    """Retorna (cliente, project_id) usando Credenciais (Service Account ou ADC)."""
    project_id, credentials = get_gcp_project_id()
    if credentials:
        try:
            from google.api_core.client_options import ClientOptions
            options = ClientOptions(quota_project_id=project_id)
            client = translate.TranslationServiceClient(credentials=credentials, client_options=options)
            return client, project_id
        except Exception as e:
            print(f"Erro ao criar cliente com credenciais: {e}")
    
    return None, None


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, sso_token: Optional[str] = None):
    """Rota principal que carrega o Front-end com suporte a SSO."""
    
    # Lógica de SSO: Se vier um token, validamos no Supabase
    if sso_token and supabase:
        try:
            # Verifica se o ticket existe, é válido e não foi usado
            now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            
            res = supabase.table("sso_tokens") \
                .select("user_email") \
                .eq("id", sso_token) \
                .gt("expires_at", now_utc) \
                .is_("used_at", "null") \
                .execute()
            
            if res.data:
                user_email = res.data[0]["user_email"]
                # Marca como usado
                used_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
                supabase.table("sso_tokens").update({"used_at": used_at}).eq("id", sso_token).execute()
                
                # Gera a resposta com um cookie de sessão simples
                response = templates.TemplateResponse(request=request, name="index.html", context={"user_email": user_email})
                response.set_cookie(key="sso_session", value=user_email, max_age=3600*24) # 24 horas
                return response
        except Exception as e:
            print(f"Erro no SSO Tradutor: {e}")

    # Fallback padrão
    user_email = request.cookies.get("sso_session")
    return templates.TemplateResponse(request=request, name="index.html", context={"user_email": user_email})


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(BASE_PATH, "static", "pwa-icon.png"))


@app.post("/translate")
async def translate_pdf_endpoint(file: UploadFile = File(...)):
    """
    Recebe o PDF, divide em chunks de até 20 páginas,
    traduz cada chunk via GCP e une os resultados.
    """
    # Recarrega credenciais a cada requisição para não ficar preso em estado expirado
    project_id, _ = get_gcp_project_id()

    if not project_id:
        raise HTTPException(
            status_code=401,
            detail="AUTH_REQUIRED"
        )

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Somente arquivos PDF são aceitos.")

    file_bytes = await file.read()
    if not isinstance(file_bytes, bytes):
        file_bytes = bytes(file_bytes)

    # Limite de 100MB
    if len(file_bytes) > 104857600:
        raise HTTPException(status_code=400, detail="O arquivo excede o tamanho máximo de 100MB.")

    try:
        job_id = str(uuid.uuid4())
        original_name = file.filename.rsplit('.', 1)[0]
        translation_jobs[job_id] = {"status": "processing", "result": None, "error": None, "original_name": original_name}
        
        asyncio.create_task(background_translate(job_id, file_bytes, project_id))
        
        return {"job_id": job_id, "machine_id": os.environ.get("FLY_MACHINE_ID", "")}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

async def background_translate(job_id: str, file_bytes: bytes, project_id: str):
    try:
        from starlette.concurrency import run_in_threadpool
        translated_bytes = await run_in_threadpool(translate_pdf_in_chunks, file_bytes, project_id)
        translation_jobs[job_id]["result"] = translated_bytes
        translation_jobs[job_id]["status"] = "done"
    except Exception as e:
        import traceback
        traceback.print_exc()
        translation_jobs[job_id]["status"] = "error"
        translation_jobs[job_id]["error"] = str(e)

@app.get("/translate/status/{job_id}")
async def get_translate_status(job_id: str):
    job = translation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado nesta máquina.")
    return {"status": job["status"], "error": job.get("error")}

@app.get("/translate/download/{job_id}")
async def download_translated_pdf(job_id: str):
    job = translation_jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=400, detail="Job não concluído ou não encontrado.")
    
    new_filename = f"{job['original_name']}_ptBR.pdf"
    
    return Response(
        content=job["result"],
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{new_filename}"'}
    )


def split_pdf_by_size_and_pages(pdf_bytes: bytes) -> list[bytes]:
    """
    Divide um PDF dinamicamente garantindo que cada parte tenha no máximo
    MAX_PAGES_PER_CHUNK (20) páginas E no máximo ~19MB de tamanho real.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    chunks = []
    
    current_pages = []
    max_bytes = 19 * 1024 * 1024  # 19 MB seguro
    
    print(f"⚙ Iniciando particionamento dinâmico otimizado do PDF ({total_pages} páginas)...")
    
    for idx in range(total_pages):
        current_pages.append(idx)
        
        # Cria um writer temporário usando 'append' para manter referências cruzadas otimizadas
        temp_writer = PdfWriter()
        temp_writer.append(fileobj=io.BytesIO(pdf_bytes), pages=current_pages)
        
        buf = io.BytesIO()
        temp_writer.write(buf)
        current_size = len(buf.getvalue())
        
        # Se ultrapassou o limite de MB OR o limite de páginas AND já existe mais de 1 página
        if (current_size > max_bytes or len(current_pages) > MAX_PAGES_PER_CHUNK) and len(current_pages) > 1:
            # Reconstrói e salva o writer SEM a página atual (idx)
            chunk_writer = PdfWriter()
            chunk_pages = current_pages[:-1]
            chunk_writer.append(fileobj=io.BytesIO(pdf_bytes), pages=chunk_pages)
                
            chunk_buf = io.BytesIO()
            chunk_writer.write(chunk_buf)
            chunks.append(chunk_buf.getvalue())
            print(f"  → Chunk finalizado: {len(chunk_pages)} páginas, {len(chunk_buf.getvalue()) / 1024 / 1024:.2f} MB")
            
            # Começa um novo chunk DE FATO com a página atual
            current_pages = [idx]
            
    # Adicionar o último chunk que sobrou
    if current_pages:
        last_writer = PdfWriter()
        last_writer.append(fileobj=io.BytesIO(pdf_bytes), pages=current_pages)
        buf = io.BytesIO()
        last_writer.write(buf)
        chunks.append(buf.getvalue())
        print(f"  → Último chunk finalizado: {len(current_pages)} páginas, {len(buf.getvalue()) / 1024 / 1024:.2f} MB")

    return chunks


def merge_pdf_bytes(pdf_chunks: list[bytes]) -> bytes:
    """
    Une uma lista de PDFs (bytes) em um único PDF.
    """
    writer = PdfWriter()
    for chunk_bytes in pdf_chunks:
        reader = PdfReader(io.BytesIO(chunk_bytes))
        for page in reader.pages:
            writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def call_gcp_translate_document(file_bytes: bytes, project_id: str) -> bytes:
    """
    Faz uma chamada à API v3 de Document Translation do Google Cloud.
    Passa os bytes diretamente (sem precisar de GCS bucket).
    """
    client, _ = get_translate_client()
    if not client:
        raise Exception("Cliente de tradução GCP não inicializado. Verifique a API Key ou Credenciais.")
        
    parent = f"projects/{project_id}/locations/global"

    document_input_config = translate.DocumentInputConfig(
        content=file_bytes,
        mime_type="application/pdf",
    )

    request = translate.TranslateDocumentRequest(
        parent=parent,
        source_language_code=None,  # None ativa a detecção automática de idioma do Google
        target_language_code="pt-BR",
        document_input_config=document_input_config,
    )

    response = client.translate_document(request=request)
    return response.document_translation.byte_stream_outputs[0]


def translate_pdf_in_chunks(pdf_bytes: bytes, project_id: str) -> bytes:
    """
    Orquestra: divide o PDF em chunks de até 20 páginas,
    traduz cada um e une os resultados num PDF final.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    print(f"📄 Total de páginas do PDF: {total_pages}")

    if total_pages <= MAX_PAGES_PER_CHUNK:
        # PDF pequeno: traduz de uma vez
        print("✓ PDF pequeno, traduzindo em uma chamada única...")
        return call_gcp_translate_document(pdf_bytes, project_id)

    # PDF grande: divide, traduz e une
    # PDF grande (em páginas ou potencialmente em bytes): divide dinamicamente
    print(f"⚙ Verificando limites. Dividindo dinamicamente...")
    chunks = split_pdf_by_size_and_pages(pdf_bytes)
    print(f"⚙ Dividido dinamicamente em {len(chunks)} chunks...")
    
    import concurrent.futures
    translated_chunks = []
    
    print(f"🚀 Iniciando tradução paralela (max 5 chunks simultâneos)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Envia todas as tarefas para a thread pool e mantém a ordem
        futures = [executor.submit(call_gcp_translate_document, chunk, project_id) for chunk in chunks]
        
        for i, future in enumerate(futures, 1):
            translated_chunks.append(future.result())
            print(f"✅ Chunk {i}/{len(chunks)} concluído!")

    print("🎉 Todos os chunks traduzidos! Unindo PDF final...")
    return merge_pdf_bytes(translated_chunks)
