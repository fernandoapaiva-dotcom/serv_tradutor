import multiprocessing
import uvicorn
import webview
import time
import sys
from main import app

def run_server():
    """Função para rodar o servidor FastAPI"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def main():
    # Inicia o servidor em um processo separado (necessário para Windows e PyInstaller)
    server_process = multiprocessing.Process(target=run_server)
    server_process.daemon = True
    server_process.start()

    # Aguarda um momento para o servidor subir
    time.sleep(2)

    # Cria a janela do aplicativo Desktop
    window = webview.create_window(
        'Servsolda - Tradutor de Documentos',
        'http://127.0.0.1:8000',
        width=1000,
        height=800,
        resizable=True
    )

    # Inicia a interface gráfica
    webview.start()

    # Quando a janela fechar, mata o processo do servidor
    server_process.terminate()
    sys.exit()

if __name__ == '__main__':
    # Necessário para o PyInstaller funcionar com multiprocessing no Windows
    multiprocessing.freeze_support()
    main()
