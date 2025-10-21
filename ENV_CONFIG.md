# Configuração de Variáveis de Ambiente

## Variáveis Disponíveis

### PORT
- **Descrição**: Porta em que o servidor Flask será executado
- **Padrão**: 8000
- **Obrigatório**: Não
- **Exemplo**: `PORT=3000`

## Como Configurar

### Desenvolvimento Local

Crie um arquivo `.env` na raiz do projeto:

```env
PORT=8000
```

### Deploy no Vercel

No Vercel, configure a variável de ambiente no painel de configurações do projeto:

**Método 1: Via Dashboard**
1. Acesse o projeto no dashboard do Vercel
2. Vá em **Settings** → **Environment Variables**
3. Adicione:
   - **Name**: `PORT`
   - **Value**: `9001` (ou a porta que desejar)
   - **Environment**: Selecione Production, Preview e Development
4. Salve e faça redeploy

**Método 2: Via vercel.json**
O arquivo `vercel.json` na raiz do projeto já está configurado com `PORT=9001`.

**Como o Backend Obtém a Porta:**
```python
port = int(os.environ.get("PORT", 8000))
# Busca a variável PORT do ambiente
# Se PORT=9001 no Vercel, usa 9001
# Se não estiver definida, usa 8000 (padrão)
```

### Deploy no Heroku

No Heroku, a variável `PORT` é configurada automaticamente pela plataforma. Não é necessário configurar manualmente.

### Deploy no AWS Elastic Beanstalk

Configure no arquivo `.ebextensions/environment.config` ou no painel de configurações do AWS:

```yaml
option_settings:
  - option_name: PORT
    value: 8000
```

## Testando

Para testar com uma porta diferente:

```bash
# Windows PowerShell
$env:PORT=3000
python application.py

# Linux/Mac
PORT=3000 python application.py
```

