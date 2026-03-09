from PIL import Image
import os

def convert_to_ico():
    img_path = r"c:\Antigravity\tradutor_pdf\static\logo.png"
    ico_path = r"c:\Antigravity\tradutor_pdf\icon.ico"
    
    if os.path.exists(img_path):
        img = Image.open(img_path)
        # Salva como ICO com os tamanhos padrão
        img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        print(f"Ícone criado em: {ico_path}")
    else:
        print("Logo não encontrada!")

if __name__ == "__main__":
    convert_to_ico()
