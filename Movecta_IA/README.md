# Movecta.IA

Protótipo de assistente interno de Recursos Humanos da Movecta, desenvolvido em Streamlit.

## Executar localmente

1. Crie um ambiente virtual Python 3.11.
2. Instale as dependências:
   `pip install -r requirements.txt`
3. Configure `GEMINI_API_KEY` em variável de ambiente ou em `.streamlit/secrets.toml`.
4. Execute:
   `streamlit run app.py`

## Estrutura

- `app.py`: interface, sessão e integração de IA.
- `knowledge_base/common`: documentos disponíveis para todos.
- `knowledge_base/employee`: documentos específicos de colaboradores.
- `knowledge_base/manager`: documentos específicos de gestão.
- `.streamlit/config.toml`: tema visual.

## Observações do protótipo

- O histórico é mantido apenas durante a sessão ativa do Streamlit.
- Uploads feitos pela interface são gravados no filesystem da instância. Em hospedagens efêmeras, esses arquivos podem não persistir após reinício ou redeploy.
- A base atual contém conteúdo de teste e deve ser validada pelo RH antes de uso em produção.
- Informações conflitantes entre documentos não devem ser resolvidas automaticamente pelo assistente.
- Não versionar chaves de API ou `secrets.toml`.
