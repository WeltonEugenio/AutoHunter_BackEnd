# AutoHunter Backend

Backend em Python usando Flask para escanear URLs e baixar arquivos (ZIP, imagens, PDFs).

## Instalação

1. Criar ambiente virtual:
```bash
python -m venv venv
```

2. Ativar ambiente virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Instalar dependências:
```bash
pip install -r requirements.txt
```

## Configuração

Crie um arquivo `.env` na raiz do projeto (opcional):
```env
PORT=8000
```

Se não configurar a variável `PORT`, o servidor usará a porta **8000** por padrão.

### Deploy (Vercel, Heroku, etc.)

Para plataformas de deploy, configure a variável de ambiente `PORT` nas configurações da plataforma. O servidor automaticamente usará a porta especificada pela plataforma.

## Executar

```bash
python application.py
```

O servidor rodará em `http://0.0.0.0:8000` (ou na porta especificada pela variável `PORT`)

## API Endpoints

### GET /
Health check da API

### POST /scan
Escaneia uma URL em busca de arquivos ZIP e 7z

**Body:**
```json
{
  "url": "https://example.com",
  "save_directory": "C:/downloads"
}
```

**Response:**
```json
{
  "success": true,
  "files_found": 3,
  "files": [
    {
      "filename": "arquivo.zip",
      "url": "https://example.com/arquivo.zip",
      "size": "Unknown"
    }
  ]
}
```

### POST /download
Baixa todos os arquivos ZIP e 7z encontrados na URL

**Body:**
```json
{
  "url": "https://example.com",
  "save_directory": "C:/downloads"
}
```

**Response:**
```json
{
  "success": true,
  "downloaded": 3,
  "failed": 0,
  "files": [...],
  "errors": []
}
```

## Documentação Interativa

Acesse http://localhost:8000/docs para ver a documentação Swagger

