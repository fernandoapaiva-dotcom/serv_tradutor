# Guia de Deploy Isolado na Oracle Cloud (OCI) - Tradutor PDF

Este guia explica como subir o Tradutor PDF de forma isolada na OCI, garantindo que ele não entre em conflito com outros sistemas (como o CREDOS ou SS_GAS_CONTROL).

## 1. Criar a Instância na OCI (Isolamento)

Para garantir o isolamento total, você deve criar uma **Instância Compute** (Máquina Virtual) separada para este serviço, ou pelo menos usar uma porta diferente e um diretório separado se for rodar na mesma máquina.

Se for criar uma nova instância:
1. Vá no painel da Oracle Cloud > **Compute** > **Instances** > **Create Instance**.
2. Nomeie-a como `tradutor-pdf-server`.
3. Escolha a imagem (ex: Ubuntu 22.04) e o *shape* (ex: ARM Ampere A1, que é gratuito e suporta Docker).
4. Faça o download da chave SSH privada (`.key` ou `.pem`) para poder acessar a máquina depois.
5. Em **Networking**, certifique-se de liberar a porta `8000` (ou a porta que você vai usar) e a porta `4040` (se for usar o ngrok para túnel) nas *Security Lists* (Regras de Entrada / Ingress Rules).

## 2. Instalar o Docker na Instância (se for nova)

Acesse a instância por SSH e instale o Docker e o Git:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```
> *Desconecte e conecte novamente do SSH para que as permissões do grupo docker entrem em vigor.*

## 3. Configurar as Credenciais do Google Cloud (Passo Crítico)

Como não temos o `%APPDATA%` do Windows no Linux, você precisa da Chave JSON da sua Service Account:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Vá em **IAM e Administração** > **Contas de Serviço**.
3. Crie uma Conta de Serviço (ex: `tradutor-pdf-service`).
4. Dê a ela o papel (Role) de **Usuário da API Cloud Translation**.
5. Clique na conta criada, vá na aba **Chaves** > **Adicionar Chave** > **Criar nova chave**.
6. Escolha o formato **JSON** e baixe o arquivo.
7. Abra o arquivo JSON em um bloco de notas no seu computador e remova todas as quebras de linha (deixe tudo em uma única linha).

## 4. Subir o Projeto na OCI

Acesse a máquina OCI via SSH e execute os seguintes comandos:

```bash
# 1. Clone o repositório (substitua pela URL do seu git se necessário)
# Se não estiver no github, você pode copiar os arquivos via SFTP ou scp
git clone <SUA_URL_DO_REPOSITORIO> tradutor_pdf
cd tradutor_pdf

# 2. Crie o arquivo .env
cp .env.example .env
nano .env
```

Dentro do `nano`, preencha as variáveis:
- `NGROK_AUTHTOKEN`: Seu token do ngrok (opcional se não for usar o ngrok na OCI).
- `GCP_PROJECT_ID`: O ID do seu projeto no GCP.
- `GCP_SERVICE_ACCOUNT_JSON`: Cole aqui o conteúdo do JSON que você baixou no Passo 3, **tudo em uma linha só**.
- *(Se usar Supabase, adicione `SUPABASE_URL` e `SUPABASE_ANON_KEY` também)*.

Salve o arquivo (`Ctrl+O`, `Enter`, `Ctrl+X`).

```bash
# 3. Construa e suba os contêineres Docker em background
docker-compose up -d --build
```

## 5. Validação

Verifique se os contêineres estão rodando corretamente:

```bash
docker ps
```

Você deve ver os contêineres `tradutor_servsolda` e `tradutor_ngrok` rodando.

Para ver os logs do tradutor e garantir que ele identificou as credenciais do Google Cloud:

```bash
docker logs -f tradutor_servsolda
```

O sistema agora está isolado, usando uma autenticação definitiva (Service Account JSON) e rodando 100% via Docker em Linux!
