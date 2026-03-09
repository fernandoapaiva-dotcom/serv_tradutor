# 📱 Guia de Deploy para Celular (Android & iOS)

Para que o sistema funcione no celular como um aplicativo, ele precisa estar "na internet" (hospedado) em vez de rodar localmente no seu PC. Aqui está como fazer:

## 1. Hospedagem (Onde o App vai morar)
Sugiro usar a **Railway.app** ou **Render.com** (que têm planos gratuitos/baratos para desenvolvedores).

1.  Crie uma conta na [Railway.app](https://railway.app).
2.  Conecte seu repositório do GitHub: `serv_tradutor`.
3.  A Railway vai detectar o `requirements.txt` e o comando de inicialização automaticamente.
4.  No campo **Startup Command**, use:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port $PORT
    ```
5.  Pronto! Você terá um link público (ex: `serv-tradutor.up.railway.app`).

---

## 2. Instalação no Celular (PWA)
Com o link criado, você transforma o site em um App sem precisar da Google Play/App Store (técnica PWA):

### No Android (Google Chrome)
1.  Abra o link do seu app no Chrome.
2.  Um aviso escrito **"Instalar Aplicativo"** aparecerá na parte de baixo.
3.  Clique nele. O ícone da Servsolda será adicionado ao seu menu de apps.

### No iPhone (Safari)
1.  Abra o link no Safari.
2.  Clique no botão de **Compartilhar** (quadrado com uma seta pra cima).
3.  Role para baixo e clique em **"Adicionar à Tela de Início"**.
4.  O ícone aparecerá junto com seus outros aplicativos.

---

## 3. Para as Lojas (Google Play / App Store)
Se você **realmente** precisar dele nas lojas para download público:
1.  Precisamos usar uma ferramenta chamada **Capacitor**.
2.  Ela "envelopa" o link que criamos na etapa 1 dentro de um arquivo `.apk` (Android) ou binário de iOS.
3.  Isso exige contas de desenvolvedor (Google cobra taxa única de $25, Apple cobra $99/ano).

> [!TIP]
> **Recomendação:** Comece com a etapa **PWA (Item 2)**. É instantâneo, gratuito e o usuário nem percebe que não é um app de "loja" – ele abre em tela cheia e tem o ícone da sua loja.

---
🚀 Seu sistema já está 100% preparado (com Manifest e Service Worker) para essas etapas!
