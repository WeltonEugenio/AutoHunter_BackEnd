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

def has_credentials(url):
    """Verifica se a URL contém credenciais (usuário/senha)"""
    try:
        result = urlparse(url)
        return bool(result.username or result.password)
    except:
        return False

def scan_directory_recursive(url, file_type, max_depth=3, current_depth=0):
    """Escaneia um diretório recursivamente procurando por arquivos"""
    files = []
    
    if current_depth >= max_depth:
        return files
    
    try:
        print(f"Escaneando: {url} (profundidade: {current_depth})")
        
        # Preparar autenticação se necessário
        auth = None
        parsed_url = urlparse(url)
        if parsed_url.username and parsed_url.password:
            auth = (parsed_url.username, parsed_url.password)
        
        # Fazer requisição com timeout e autenticação
        response = requests.get(url, timeout=30, stream=True, auth=auth)
        response.raise_for_status()
        
        # Verificar se é um arquivo direto (não HTML)
        content_type = response.headers.get('content-type', '').lower()
        filename = os.path.basename(parsed_url.path)
        
        # Se não é HTML, verificar se é um arquivo do tipo desejado
        if 'text/html' not in content_type and filename:
            if should_include_file(filename, file_type):
                file_size = int(response.headers.get('content-length', 0))
                files.append({
                    'filename': filename,
                    'url': url,
                    'size': file_size
                })
                print(f"Arquivo direto encontrado: {filename} ({file_size} bytes)")
            return files
        
        # Se é HTML, continuar com o escaneamento de diretório
        if 'text/html' not in content_type:
            return files
        
        # Parse simples do HTML usando regex
        html_content = response.text
        
        # Debug: mostrar parte do conteúdo HTML
        print(f"Content-Type: {content_type}")
        print(f"HTML preview: {html_content[:200]}...")
        
        # Encontrar links usando regex simples
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>'
        links = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        print(f"Encontrados {len(links)} links")
        
        # Se não encontrou links, tentar outros padrões
        if len(links) == 0:
            # Tentar encontrar URLs de arquivos diretamente no HTML
            file_patterns = {
                'pdf': r'[^"\'>\s]+\.pdf(?:\?[^"\'>\s]*)?',
                'zip': r'[^"\'>\s]+\.(?:zip|7z|rar|tar|gz|bz2)(?:\?[^"\'>\s]*)?',
                'images': r'[^"\'>\s]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg)(?:\?[^"\'>\s]*)?'
            }
            
            if file_type in file_patterns:
                file_links = re.findall(file_patterns[file_type], html_content, re.IGNORECASE)
                print(f"Encontrados {len(file_links)} arquivos {file_type} via regex direto")
                links.extend(file_links)
        
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
                    head_response = requests.head(full_url, timeout=10, auth=auth)
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
        
        # Verificar se é URL interna (apenas aviso, não bloqueia)
        is_internal = '172.17.' in url or '192.168.' in url or '10.' in url
        if is_internal:
            print(f"AVISO: URL interna detectada: {url}")
            print("Nota: URLs internas podem não ser acessíveis em produção (Vercel/AWS)")
        
        # Verificar se contém credenciais (apenas aviso)
        if has_credentials(url):
            print(f"AVISO: URL contém credenciais (usuário/senha)")
            print("Nota: Tenha cuidado com URLs que contêm senhas em logs")
        
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
