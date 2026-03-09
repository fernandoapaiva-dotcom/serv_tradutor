# 🌐 Servsolda - Tradutor de Documentos (PDF)

Sistema web premium desenvolvido para a **Servsolda Comercial LTDA**, capaz de traduzir documentos PDF de qualquer idioma para o Português (pt-BR), mantendo integralmente o layout, figuras e formatação originais.

![Screenshot da Interface](https://raw.githubusercontent.com/fernandoapaiva-dotcom/serv_tradutor/main/static/logo.png)

## 🚀 Funcionalidades

- **Detecção Automática:** Identifica o idioma de origem (Inglês, Alemão, etc.) sem configuração manual.
- **Suporte a PDFs Grandes:** Sistema de *chunking* automático que divide PDFs longos em partes de 20 páginas para contornar limites de API.
- **Layout Original:** Utiliza a poderosa API v3 do Google Cloud Document Translation para garantir que imagens e tabelas fiquem no lugar certo.
- **Interface Premium:** Design baseado na identidade visual da Servsolda (Verde/Preto) com suporte a Drag & Drop.

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python + FastAPI (Antigravity Engine)
- **Frontend:** HTML5, CSS3 Moderno (Flexbox/Gradients), JavaScript Puro (Fetch/Blobs)
- **Document Processing:** `pypdf` para divisão e união de documentos.
- **IA/Nuvem:** Google Cloud Translation API v3.

## 📦 Como Rodar o Projeto

### 1. Requisitos Prévios
- Python 3.10+ instalado.
- Google Cloud CLI instalado e configurado.

### 2. Instalação das Dependências
Abra o terminal na pasta do projeto e execute:
```bash
pip install -r requirements.txt
```

### 3. Autenticação com Google Cloud
Este projeto utiliza **Application Default Credentials (ADC)**. Para autenticar sua máquina com segurança:
```bash
gcloud auth application-default login
```
Em seguida, configure o projeto padrão e o projeto de quota:
```bash
gcloud config set project sistema-tradutor-pdf
gcloud auth application-default set-quota-project sistema-tradutor-pdf
```

### 4. Inicialização do Servidor
```bash
uvicorn main:app --reload
```
Acesse no navegador: `http://localhost:8000`

## 📁 Estrutura de Pastas
```text
/
├── main.py              # Lógica principal e integração GCP
├── requirements.txt     # Dependências do Python
├── static/              # Ativos estáticos (Logo)
├── templates/           # Arquivos HTML/Jinja2
└── README.md            # Este arquivo
```

---
Desenvolvido por **Fernando_M_Aragao** & Google Cloud Platform.
