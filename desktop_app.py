import multiprocessing
import uvicorn
import webview
import time
import sys
from main import app

import base64
import os

class Api:
    def save_and_open_pdf(self, b64_data, filename):
        """Salva a string Base64 como PDF e abre no visualizador padrão (Acrobat, etc)"""
        try:
            # Garante que a pasta 'traducoes' existe
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", "Servsolda_Traducoes")
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            full_path = os.path.join(save_path, filename)
            
            # Decodifica Base64
            pdf_bytes = base64.b64decode(b64_data)
            
            with open(full_path, "wb") as f:
                f.write(pdf_bytes)
            
            # Abre o arquivo no Windows (Acrobat/Navegador/etc)
            os.startfile(full_path)
            return True
        except Exception as e:
            print(f"Erro ao salvar/abrir PDF: {e}")
            return False

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
        resizable=True,
        js_api=Api()
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
