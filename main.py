import os
import io
import google.auth
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.cloud import translate_v3 as translate
from pypdf import PdfReader, PdfWriter

import sys

def get_base_path():
    """Retorna o caminho base correto para desenvolvimento ou executável (PyInstaller)"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

app = FastAPI(title="Servsolda PDF Translator")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_PATH, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_PATH, "templates"))

# Limite máximo de páginas por chamada à API do Google
MAX_PAGES_PER_CHUNK = 20


def get_gcp_project_id():
    """
    Obtém o Project ID. No Render/Cloud, tenta carregar de uma variável de ambiente JSON.
    Localmente, usa as Application Default Credentials (ADC).
    """
    # 1. Tenta carregar de uma variável com o conteúdo do JSON (Útil para Render/Railway)
    service_account_json = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            import json
            from google.oauth2 import service_account
            info = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(info)
            # Define as credenciais globalmente para o cliente usar
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_DATA"] = service_account_json # Para debug/referência interna se necessário
            return info.get("project_id"), credentials
        except Exception as e:
            print(f"Erro ao carregar GCP_SERVICE_ACCOUNT_JSON: {e}")

    # 2. Caso padrão: Application Default Credentials (ADC)
    try:
        credentials, project_id = google.auth.default()
        return project_id, credentials
    except Exception as e:
        print(f"Aviso: Não foi possível carregar as credenciais GCP padrão: {e}")
        return None, None


# Inicializa as credenciais uma vez
PROJECT_ID, GCP_CREDENTIALS = get_gcp_project_id()


def get_translate_client():
    """Retorna o cliente de tradução usando as credenciais carregadas."""
    if GCP_CREDENTIALS:
        return translate.TranslationServiceClient(credentials=GCP_CREDENTIALS)
    return translate.TranslationServiceClient()


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Rota principal que carrega o Front-end."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/translate")
async def translate_pdf_endpoint(file: UploadFile = File(...)):
    """
    Recebe o PDF, divide em chunks de até 20 páginas,
    traduz cada chunk via GCP e une os resultados.
    """
    if not PROJECT_ID:
        raise HTTPException(
            status_code=500,
            detail="Project ID do GCP não encontrado! Rode: gcloud auth application-default login"
        )

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Somente arquivos PDF são aceitos.")

    file_bytes = await file.read()
    if not isinstance(file_bytes, bytes):
        file_bytes = bytes(file_bytes)

    # Limite de 20MB
    if len(file_bytes) > 20971520:
        raise HTTPException(status_code=400, detail="O arquivo excede o tamanho máximo de 20MB.")

    try:
        translated_bytes = translate_pdf_in_chunks(file_bytes, PROJECT_ID)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na API GCP: {str(e)}")

    original_name = file.filename.rsplit('.', 1)[0]
    new_filename = f"{original_name}_ptBR.pdf"

    return Response(
        content=translated_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{new_filename}"'}
    )


def split_pdf_into_chunks(pdf_bytes: bytes, chunk_size: int) -> list[bytes]:
    """
    Divide um PDF em partes de 'chunk_size' páginas máximo.
    Retorna uma lista de bytes, cada um sendo um PDF parcial.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    chunks = []

    for start in range(0, total_pages, chunk_size):
        writer = PdfWriter()
        end = min(start + chunk_size, total_pages)
        for page_num in range(start, end):
            writer.add_page(reader.pages[page_num])

        buf = io.BytesIO()
        writer.write(buf)
        chunks.append(buf.getvalue())
        print(f"  → Chunk criado: páginas {start + 1} a {end} de {total_pages}")

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
    client = get_translate_client()
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
    print(f"⚙ PDF grande ({total_pages} páginas). Dividindo em chunks de {MAX_PAGES_PER_CHUNK} páginas...")
    chunks = split_pdf_into_chunks(pdf_bytes, MAX_PAGES_PER_CHUNK)
    translated_chunks = []

    for i, chunk in enumerate(chunks, 1):
        print(f"🌐 Traduzindo chunk {i}/{len(chunks)}...")
        translated_chunk = call_gcp_translate_document(chunk, project_id)
        translated_chunks.append(translated_chunk)

    print("✅ Todos os chunks traduzidos! Unindo PDF final...")
    return merge_pdf_bytes(translated_chunks)
