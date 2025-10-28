# Changelog - AutoHunter Backend

Todas as mudanças notáveis neste projeto serão documentadas aqui.

## [1.0.5] - 2025-10-28

### Corrigido
- ✅ Aceita `selected_files` como array de URLs (strings)
- ✅ Aceita `selected_files` como array de objetos {url, filename}
- ✅ Extração automática de filename da URL quando não fornecido
- ✅ Tratamento especial para URLs terminadas em /view

### Adicionado
- ✅ Suporte a 3 formatos diferentes de entrada de arquivos
- ✅ Extração inteligente de filename considerando /view no path
- ✅ Logs detalhados do processamento de cada tipo de entrada

## [1.0.3] - 2025-10-28

### Corrigido
- ✅ Retorna erro 400 com detalhes quando nenhum arquivo é baixado com sucesso
- ✅ Contador de arquivos baixados vs falhados
- ✅ Lista de erros individuais por arquivo

### Adicionado
- ✅ Estatísticas de download (total, baixados, falhados)
- ✅ Log do tamanho do ZIP criado
- ✅ Retorno detalhado de erros quando todos os downloads falham

## [1.0.2] - 2025-10-28

### Corrigido
- ✅ Parse de `selected_files` quando vem como string JSON
- ✅ Parse de cada `file_info` quando vem como string
- ✅ Validação robusta de tipos de dados
- ✅ Logs detalhados com traceback completo em erros 500

### Adicionado
- ✅ Tratamento de erro para JSON mal formado
- ✅ Validação de estrutura de dados em múltiplos níveis
- ✅ Logs informativos para cada etapa do processo

## [1.0.1] - 2025-10-28

### Adicionado
- ✅ Endpoint `/download-stream` com suporte completo a CORS
- ✅ Download de múltiplos arquivos como ZIP em memória
- ✅ Conversão automática de URLs `/view` para `/@@download/file` (gov.br/Plone)
- ✅ User-Agent simulando browser
- ✅ Suporte a redirects
- ✅ Tratamento individual de erros por arquivo

### Melhorado
- ✅ Logs mais detalhados no processo de download
- ✅ Continua o processo mesmo se um arquivo falhar

## [1.0.0] - 2025-10-28

### Adicionado
- ✅ Parâmetro `include_src` para detectar elementos com atributo `src`
- ✅ Detecção de `<img>`, `<script>`, `<iframe>`, `<video>`, `<audio>`, `<source>`, `<embed>`
- ✅ Porta configurável via variável de ambiente `PORT`
- ✅ Suporte a `python-dotenv` para configuração local
- ✅ Documentação completa para deploy no Vercel
- ✅ Versão da API no endpoint raiz
- ✅ Lista de endpoints disponíveis

### Corrigido
- ✅ URLs internas (172.17.x.x, 192.168.x.x, 10.x.x.x) agora funcionam
- ✅ URLs com credenciais HTTP funcionam
- ✅ Autenticação HTTP automática em todas as requisições
- ✅ Detecção melhorada de arquivos diretos (não HTML)
- ✅ Regex melhorado para encontrar arquivos quando não há links `<a>`

### Recursos
- ✅ Escaneamento recursivo de diretórios (profundidade: 3)
- ✅ Suporte a ZIP, 7z, RAR, TAR, GZ, BZ2
- ✅ Suporte a imagens (PNG, JPG, JPEG, GIF, BMP, WEBP, SVG)
- ✅ Suporte a PDFs
- ✅ CORS habilitado para todas as origens
- ✅ Autenticação HTTP com username/password na URL

