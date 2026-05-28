# Guia de Deploy no Fly.io - Tradutor PDF

Este guia explica como fazer o deploy da nossa aplicação de tradução de PDF no **Fly.io**. A vantagem do Fly é que tudo é feito direto do seu computador, sem precisar entrar em SSH em servidores, e ele já cria um link seguro `https://...` automaticamente!

---

## 1. Instalar o Flyctl no Windows
Se você ainda não tem o painel de comando do Fly, abra seu PowerShell e instale com o comando:
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

## 2. Autenticação e Configuração
Abra seu terminal na pasta do projeto (`c:\Antigravity\tradutor_pdf`) e rode:

```bash
# Faz login na sua conta do Fly.io pelo navegador
fly auth login

# Inicializa o app na nuvem baseado no nosso fly.toml. 
# Quando perguntar se você quer alterar configurações ou usar banco de dados postgres/redis, diga **NÃO (N)**.
fly launch --name tradutor-pdf-servsolda --region gru --no-deploy
```
> **Aviso:** Se o nome `tradutor-pdf-servsolda` já estiver em uso por alguém, ele vai pedir para você escolher outro ou gerar um automático. Fique à vontade para usar o que preferir!

## 3. Configurar as Chaves Secretas (O mais importante!)
O Fly não usa o arquivo `.env`. Para chaves sensíveis como a do Google e do Supabase, nós usamos os "Secrets" dele.

No terminal, copie a sua chave JSON da Service Account que fizemos no passo anterior (aquela toda em uma linha reta) e adicione usando o comando:

```bash
fly secrets set GCP_PROJECT_ID="seu-nome-do-projeto" GCP_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":...}' SUPABASE_URL="https://sua-url.supabase.co" SUPABASE_ANON_KEY="sua_chave_do_supabase"
```

*(Obs: Substitua pelo conteúdo correto e pressione Enter. Ele subirá de forma criptografada)*.

## 4. Subir tudo para o Ar!
Finalmente, basta mandar ele construir o Docker lá nos servidores deles e rodar:

```bash
fly deploy
```

Quando o processo finalizar, ele mostrará uma mensagem verde de sucesso. Para ver o site rodando, basta digitar:

```bash
fly open
```

E pronto! Ele já abrirá no seu navegador algo como `https://tradutor-pdf-servsolda.fly.dev` com certificado SSL bonitinho funcionando perfeito e isolado.
