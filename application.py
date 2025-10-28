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

# Versão da API
VERSION = "1.0.7"

# Criar a aplicação Flask
app = Flask(__name__)
CORS(app, origins=["*"], allow_headers=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

@app.route('/')
def home():
    return jsonify({
        "message": "AutoHunter API is running",
        "version": VERSION,
        "endpoints": {
            "/scan": "POST - Escanear URLs por arquivos",
            "/download": "POST - Download de arquivos (placeholder)",
            "/download-stream": "POST - Download de múltiplos arquivos como ZIP"
        }
    })

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

def scan_directory_recursive(url, file_type, max_depth=3, current_depth=0, include_src=False):
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
        
        print(f"Encontrados {len(links)} links href")
        
        # Se include_src=True, também buscar elementos com atributo src
        if include_src:
            src_pattern = r'<(?:img|script|iframe|video|audio|source|embed)[^>]*src=["\']([^"\']*)["\'][^>]*>'
            src_links = re.findall(src_pattern, html_content, re.IGNORECASE)
            print(f"Encontrados {len(src_links)} elementos com src")
            links.extend(src_links)
        
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
                sub_files = scan_directory_recursive(full_url, file_type, max_depth, current_depth + 1, include_src)
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
        include_src = data.get('include_src', False)
        
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
        print(f"Incluir elementos src: {include_src}")
        
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
        files = scan_directory_recursive(url, file_type, include_src=include_src)
        
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

@app.route('/download-stream', methods=['OPTIONS'])
def download_stream_options():
    """Handle preflight requests for CORS"""
    return '', 200

@app.route('/download-stream', methods=['POST'])
def download_stream():
    """Faz download de múltiplos arquivos e retorna como stream"""
    try:
        from flask import Response, stream_with_context
        import io
        import zipfile
        
        data = request.get_json()
        
        if not data:
            print("Erro: Nenhum dado JSON recebido")
            return jsonify({
                "success": False,
                "error": "Nenhum dado recebido"
            }), 400
        
        # Aceitar tanto 'files' quanto 'selected_files' do frontend
        files = data.get('files', data.get('selected_files', []))
        
        # Se files é uma string JSON, fazer parse
        if isinstance(files, str):
            import json
            try:
                files = json.loads(files)
                print(f"Files era string JSON, convertido para lista")
            except json.JSONDecodeError as e:
                print(f"Erro ao fazer parse de files como JSON: {e}")
                return jsonify({
                    "success": False,
                    "error": "Formato de arquivos inválido (JSON mal formado)"
                }), 400
        
        if not files:
            print(f"Erro: Nenhum arquivo recebido. Dados completos: {data}")
            return jsonify({
                "success": False,
                "error": "Nenhum arquivo para download"
            }), 400
        
        # Validar estrutura dos arquivos
        if not isinstance(files, list):
            print(f"Erro: 'files' não é uma lista. Tipo: {type(files)}")
            return jsonify({
                "success": False,
                "error": "Formato de arquivos inválido"
            }), 400
        
        print(f"Iniciando download de {len(files)} arquivos")
        print(f"Arquivos recebidos: {files}")
        
        # Se é apenas 1 arquivo, baixar direto (sem ZIP)
        if len(files) == 1:
            file_info = files[0]
            
            # Processar file_info
            if isinstance(file_info, str):
                if file_info.startswith('http://') or file_info.startswith('https://'):
                    file_url = file_info
                    parsed = urlparse(file_url)
                    filename = os.path.basename(parsed.path)
                    if filename == 'view':
                        path_parts = parsed.path.rstrip('/view').split('/')
                        filename = path_parts[-1] if path_parts else 'arquivo'
            elif isinstance(file_info, dict):
                file_url = file_info.get('url')
                filename = file_info.get('filename')
                if not filename:
                    parsed = urlparse(file_url)
                    filename = os.path.basename(parsed.path)
                    if filename == 'view':
                        path_parts = parsed.path.rstrip('/view').split('/')
                        filename = path_parts[-1] if path_parts else 'arquivo'
            
            # Converter URL /view para /@@download/file
            original_url = file_url
            if file_url.endswith('/view'):
                file_url = file_url.replace('/view', '/@@download/file')
                print(f"✓ URL convertida de: {original_url}")
                print(f"✓ URL convertida para: {file_url}")
            elif not file_url.endswith('/@@download/file'):
                # Se não termina com /view nem /@@download/file, adicionar /@@download/file
                if '/view' in file_url:
                    file_url = file_url.replace('/view', '/@@download/file')
                else:
                    # Adicionar /@@download/file se parece ser do gov.br/Plone
                    if 'gov.br' in file_url and not file_url.endswith(('.pdf', '.zip', '.7z')):
                        file_url = f"{file_url}/@@download/file"
                print(f"✓ URL ajustada para: {file_url}")
            
            print(f"📥 Iniciando download: {filename}")
            print(f"🔗 URL final: {file_url}")
            
            # Preparar autenticação
            auth = None
            parsed_url = urlparse(file_url)
            if parsed_url.username and parsed_url.password:
                auth = (parsed_url.username, parsed_url.password)
            
            # Baixar arquivo com timeout mais curto para arquivos pequenos
            import time
            start_time = time.time()
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(file_url, timeout=15, auth=auth, headers=headers, allow_redirects=True, stream=False)
            response.raise_for_status()
            
            download_time = time.time() - start_time
            
            # Detectar tipo de conteúdo
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            print(f"✓ Arquivo baixado em {download_time:.2f}s: {len(response.content)} bytes, tipo: {content_type}")
            
            # Retornar arquivo direto (sem ZIP)
            from flask import Response
            return Response(
                response.content,
                mimetype=content_type,
                headers={
                    'Content-Disposition': f'attachment; filename={filename}',
                    'Content-Type': content_type,
                    'Content-Length': str(len(response.content)),
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Expose-Headers': 'Content-Disposition, Content-Length, Content-Type'
                }
            )
        
        # Múltiplos arquivos: criar ZIP
        memory_file = io.BytesIO()
        downloaded_count = 0
        failed_count = 0
        error_messages = []
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, file_info in enumerate(files):
                # Se file_info é string (URL direta)
                if isinstance(file_info, str):
                    # Verificar se é uma URL ou JSON string
                    if file_info.startswith('http://') or file_info.startswith('https://'):
                        # É uma URL direta
                        file_url = file_info
                        # Extrair filename da URL
                        parsed = urlparse(file_url)
                        filename = os.path.basename(parsed.path)
                        # Remover /view se existir
                        if filename == 'view':
                            path_parts = parsed.path.rstrip('/view').split('/')
                            filename = path_parts[-1] if path_parts else f'file_{idx}'
                        print(f"URL direta convertida: {filename} <- {file_url}")
                    else:
                        # Tentar fazer parse como JSON
                        import json
                        try:
                            file_info = json.loads(file_info)
                        except json.JSONDecodeError:
                            print(f"Erro: file_info não é URL nem JSON válido: {file_info}")
                            continue
                
                # Se file_info agora é dict, extrair url e filename
                if isinstance(file_info, dict):
                    file_url = file_info.get('url')
                    filename = file_info.get('filename')
                    
                    if not file_url:
                        print(f"Arquivo sem url: {file_info}")
                        continue
                    
                    if not filename:
                        # Tentar extrair filename da URL
                        parsed = urlparse(file_url)
                        filename = os.path.basename(parsed.path)
                        if filename == 'view':
                            path_parts = parsed.path.rstrip('/view').split('/')
                            filename = path_parts[-1] if path_parts else f'file_{idx}'
                        print(f"Filename extraído da URL: {filename}")
                
                # Validação final
                if not file_url or not filename:
                    print(f"Arquivo inválido após processamento: url={file_url}, filename={filename}")
                    continue
                
                try:
                    # Converter URLs do tipo /view para /@@download/file (Plone/gov.br)
                    if file_url.endswith('/view'):
                        file_url = file_url.replace('/view', '/@@download/file')
                        print(f"URL convertida: {file_url}")
                    
                    print(f"Baixando: {filename} de {file_url}")
                    
                    # Preparar autenticação se necessário
                    auth = None
                    parsed_url = urlparse(file_url)
                    if parsed_url.username and parsed_url.password:
                        auth = (parsed_url.username, parsed_url.password)
                    
                    # Baixar arquivo com headers que simulam browser
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(file_url, timeout=15, auth=auth, headers=headers, allow_redirects=True, stream=False)
                    response.raise_for_status()
                    
                    # Adicionar ao ZIP
                    zipf.writestr(filename, response.content)
                    print(f"✓ Arquivo adicionado: {filename}")
                    downloaded_count += 1
                    
                except Exception as e:
                    error_msg = f"Erro ao baixar {filename}: {str(e)}"
                    print(f"✗ {error_msg}")
                    error_messages.append(error_msg)
                    failed_count += 1
                    # Continuar com próximo arquivo
                    continue
        
        # Verificar se algum arquivo foi baixado com sucesso
        print(f"Resumo: {downloaded_count} baixados, {failed_count} falharam")
        
        if downloaded_count == 0:
            return jsonify({
                "success": False,
                "error": "Nenhum arquivo foi baixado com sucesso",
                "details": {
                    "total": len(files),
                    "downloaded": downloaded_count,
                    "failed": failed_count,
                    "errors": error_messages
                }
            }), 400
        
        # Voltar para o início do arquivo
        memory_file.seek(0)
        
        print(f"✓ ZIP criado com sucesso! Tamanho: {memory_file.getbuffer().nbytes} bytes")
        
        # Retornar ZIP como stream
        zip_data = memory_file.getvalue()
        
        return Response(
            zip_data,
            mimetype='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename=arquivos.zip',
                'Content-Type': 'application/zip',
                'Content-Length': str(len(zip_data)),
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Expose-Headers': 'Content-Disposition, Content-Length'
            }
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro no download stream: {str(e)}")
        print(f"Traceback completo:\n{error_details}")
        return jsonify({
            "success": False,
            "error": f"Erro ao fazer download: {str(e)}",
            "details": error_details if app.debug else None
        }), 500

# Para o Elastic Beanstalk
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
