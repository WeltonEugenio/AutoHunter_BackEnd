# 🚀 Deploy no Vercel - Guia Completo

## Como o Backend Obtém a Porta no Vercel

### 📊 Fluxo de Configuração

```
┌─────────────────────────────────────────┐
│  Vercel Environment Variables           │
│  ┌────────────────────────────────┐     │
│  │  PORT = 9001                   │     │
│  └────────────────────────────────┘     │
└─────────────────┬───────────────────────┘
                  │
                  │ (variável de ambiente)
                  ▼
┌─────────────────────────────────────────┐
│  application.py                         │
│                                         │
│  port = int(os.environ.get("PORT"))     │
│                                         │
│  ┌─────────────────────────────┐       │
│  │ os.environ.get("PORT", 8000)│       │
│  │                             │       │
│  │ • Se PORT existe = 9001     │       │
│  │ • Se não existe  = 8000     │       │
│  └─────────────────────────────┘       │
│                                         │
│  app.run(host="0.0.0.0", port=port)     │
└─────────────────────────────────────────┘
                  │
                  ▼
        Servidor roda na porta 9001
```

## 🔧 Configuração Passo a Passo

### 1. **Configurar no Dashboard do Vercel**

```
1. Acesse: https://vercel.com/dashboard
2. Selecione seu projeto
3. Navegue: Settings → Environment Variables
4. Clique em "Add New"
5. Preencha:
   ┌──────────────────────────────┐
   │ Key:   PORT                  │
   │ Value: 9001                  │
   │ Environments:                │
   │ ☑ Production                 │
   │ ☑ Preview                    │
   │ ☑ Development                │
   └──────────────────────────────┘
6. Clique em "Save"
7. Faça um novo deploy ou redeploy
```

### 2. **Ou Usar o arquivo vercel.json**

O arquivo `vercel.json` já está configurado:

```json
{
  "version": 2,
  "env": {
    "PORT": "9001"
  },
  "builds": [
    {
      "src": "application.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "application.py"
    }
  ]
}
```

## 🧪 Testando Localmente

Para simular o comportamento do Vercel localmente:

### Windows PowerShell:
```powershell
$env:PORT=9001
python application.py
```

### Linux/Mac:
```bash
PORT=9001 python application.py
```

### Verificar:
```bash
curl http://localhost:9001
```

**Resposta esperada:**
```json
{"message":"AutoHunter API is running"}
```

## 📝 Código Relevante

### Em `application.py` (linhas 181-183):

```python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # ↑ Obtém a porta da variável de ambiente
    # Se PORT=9001 no Vercel → usa 9001
    # Se PORT não existe → usa 8000 (fallback)
    
    app.run(host="0.0.0.0", port=port)
```

## ✅ Verificação

Após o deploy no Vercel, você verá nos logs:

```
* Serving Flask app 'application'
* Running on all addresses (0.0.0.0)
* Running on http://0.0.0.0:9001
```

## 🔍 Troubleshooting

**Problema**: Porta não está sendo usada corretamente

**Soluções**:
1. Verifique se a variável `PORT` está configurada no Vercel
2. Certifique-se de fazer redeploy após adicionar a variável
3. Verifique os logs do Vercel para confirmar qual porta está sendo usada
4. Teste localmente primeiro com `$env:PORT=9001; python application.py`

## 📚 Referências

- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Python on Vercel](https://vercel.com/docs/frameworks/python)

