# Arquivo completo para Elastic Beanstalk
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Criar a aplicação Flask
app = Flask(__name__)
CORS(app, origins=["*"], allow_headers=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

@app.route('/')
def home():
    return jsonify({"message": "AutoHunter API is running"})

@app.route('/scan', methods=['OPTIONS'])
def scan_options():
    """Handle preflight requests for CORS"""
    return '', 200

def get_file_extension(filename):
    """Extrai a extensão do arquivo"""
    return os.path.splitext(filename)[1].lower()

def should_include_file(filename, file_type):
    """Verifica se o arquivo deve ser incluído baseado no tipo"""
    ext = get_file_extension(filename)
    
    if file_type == 'zip':
        return ext in ['.zip', '.7z', '.rar', '.tar', '.gz', '.bz2']
    elif file_type == 'images':
        return ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']
    elif file_type == 'pdf':
        return ext == '.pdf'
    return False

def is_valid_url(url):
    """Verifica se a URL é válida"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def scan_directory_recursive(url, file_type, max_depth=3, current_depth=0):
    """Escaneia um diretório recursivamente procurando por arquivos"""
    files = []
    
    if current_depth >= max_depth:
        return files
    
    try:
        print(f"Escaneando: {url} (profundidade: {current_depth})")
        
        # Fazer requisição com timeout
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Verificar se é HTML (diretório)
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            return files
        
        # Parse simples do HTML usando regex
        html_content = response.text
        
        # Encontrar links usando regex simples
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>'
        links = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        print(f"Encontrados {len(links)} links")
        
        for href in links:
            if not href or href in ['../', './', '/']:
                continue
            
            # Construir URL completa
            full_url = urljoin(url, href)
            
            # Verificar se é um arquivo
            filename = os.path.basename(href.rstrip('/'))
            
            if not filename:
                continue
            
            # Verificar se deve ser incluído
            if should_include_file(filename, file_type):
                file_size = 0
                try:
                    # Tentar obter o tamanho do arquivo
                    head_response = requests.head(full_url, timeout=10)
                    if head_response.status_code == 200:
                        file_size = int(head_response.headers.get('content-length', 0))
                except:
                    pass
                
                files.append({
                    'filename': filename,
                    'url': full_url,
                    'size': file_size
                })
                
                print(f"Arquivo encontrado: {filename} ({file_size} bytes)")
            
            # Se for um diretório, escanear recursivamente
            elif href.endswith('/') and current_depth < max_depth - 1:
                sub_files = scan_directory_recursive(full_url, file_type, max_depth, current_depth + 1)
                files.extend(sub_files)
        
    except Exception as e:
        print(f"Erro ao escanear {url}: {str(e)}")
    
    return files

@app.route('/scan', methods=['POST'])
def scan_url():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        file_type = data.get('file_type', 'zip')
        
        if not url:
            return jsonify({
                "success": False,
                "error": "URL é obrigatória"
            }), 400
        
        if not is_valid_url(url):
            return jsonify({
                "success": False,
                "error": "URL inválida"
            }), 400
        
        print(f"Iniciando escaneamento de: {url}")
        print(f"Tipo de arquivo: {file_type}")
        
        # TESTE: Verificar se é URL interna
        if '172.17.' in url or '192.168.' in url or '10.' in url:
            return jsonify({
                "success": False,
                "error": "URL interna detectada. O servidor AWS não consegue acessar redes privadas (172.17.x.x, 192.168.x.x, 10.x.x.x). Use uma URL pública ou configure VPN."
            }), 400
        
        # Escanear o diretório
        files = scan_directory_recursive(url, file_type)
        
        print(f"Encontrados {len(files)} arquivos")
        
        return jsonify({
            "success": True,
            "files_found": len(files),
            "files": files,
            "message": f"Encontrados {len(files)} arquivos do tipo {file_type}"
        })
        
    except Exception as e:
        print(f"Erro no escaneamento: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500

@app.route('/download', methods=['POST'])
def download_files():
    return jsonify({
        "success": True,
        "downloaded": 0,
        "failed": 0,
        "files": [],
        "errors": []
    })

# Para o Elastic Beanstalk
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
