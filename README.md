
# Ideator – Gerador de Ideias por Tendências

Este app roda no navegador (desktop e celular) e usa sua base de tendências (CSV) + um LLM (OpenAI) para gerar ideias e um roadmap 30/60/90 para qualquer briefing de cliente.

## 🚀 Como rodar localmente
1) Instale as dependências:
```bash
pip install -r requirements.txt
```
2) Configure sua chave:
- Crie um arquivo `.env` na mesma pasta e adicione:
```
OPENAI_API_KEY=coloque_sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
```
3) Execute:
```bash
streamlit run app.py
```
4) Abra o link que aparece no terminal (ex.: http://localhost:8501).

## 🌐 Como compartilhar com participantes do workshop
- **Streamlit Cloud** (mais simples): faça login, crie um app e suba estes arquivos (app.py, requirements.txt, tendencias_estruturadas.csv). Compartilhe o link/QR code.
- **Hugging Face Spaces**: crie um Space do tipo “Streamlit”, envie os arquivos e compartilhe o link.
- **Servidor próprio**: rode `streamlit run app.py` em uma VM e exponha a porta 8501 via HTTPS.

## 📄 Base de tendências
- O app já carrega um CSV padrão (`tendencias_estruturadas.csv`). Você pode subir outro CSV via UI.
- Colunas esperadas: `trend_nome, descricao, porque_agora, oportunidades, exemplos`.

## 🔒 Privacidade
- O CSV fica no servidor onde você hospedar o app.
- A geração de ideias chama a API do provedor LLM que você configurou (no exemplo, OpenAI).

## ❓ Dúvidas rápidas
- **Erro de API**: verifique se `OPENAI_API_KEY` está definido e se o modelo existe.
- **Celular**: funciona como PWA (adicione à tela inicial via menu do navegador).
