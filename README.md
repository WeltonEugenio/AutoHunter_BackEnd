# AutoZipHunter Backend

Backend em Python usando FastAPI para escanear URLs e baixar arquivos ZIP e 7z.

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

## Executar

```bash
python main.py
```

Ou usando uvicorn diretamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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

