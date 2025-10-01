# Gerador Automático de Questões

## Descrição do Raciocínio

### 1. Contexto
O projeto foi desenvolvido como um MVP para validar a ideia de um **gerador automático de questões de múltipla escolha**.  
O público-alvo são professores que necessitam de praticidade e rapidez na criação de avaliações.  
Por se tratar de um protótipo, algumas perguntas de negócio foram respondidas previamente de forma deliberada para guiar o escopo.

### 2. Perguntas de Negócio
- **Usuário final:** professores, com interação simples e intuitiva.  
- **Resultado esperado:** geração ágil de questões de qualidade, integradas ao portal do professor.  
- **Produto:** gerador automático que recebe conteúdo textual (upload ou colagem), gera questões de diferentes níveis de dificuldade e permite revisão antes do download.  
- **Dados disponíveis:** apenas texto escrito.  
- **Essencial no MVP:**  
  - Qualidade das questões (via API do Groq, modelo *Llama 3.3 Versatile*).  
  - Experiência do professor (usabilidade simples com Streamlit).  

### 3. Observações Técnicas
- Uso de roles `system` e `user` no prompt para guiar a geração.  
- Temperatura baixa no modelo, reduzindo alucinações e garantindo aderência ao material.  
- API Key definida diretamente no código para simplificação de testes.  

### 4. Possíveis Melhorias
**De negócio:**  
- Aceitar conteúdos em áudio e vídeo.  
- Permitir substituição ou exclusão de questões específicas.  
- Dar maior controle sobre os temas priorizados.  
- Disponibilizar questões direto no banco de produção.  
- Incluir outros formatos (V/F, quiz interativo, jogos etc).  

**Técnicas:**  
- Otimizar tratamento de arquivos muito grandes.  
- Migrar para stack mais robusta (FastAPI + React + Tailwind).  
- Implementar filas assíncronas para cenários de alto tráfego.  

---

## Funcionalidades
- Upload de arquivos (.docx, .pdf, .txt, .xlsx) ou entrada de texto.  
- Definição da quantidade de questões por nível (fácil, médio, difícil).  
- Geração de prévia com enunciado, alternativas, gabarito e explicação.  
- Download em TXT com todas as questões e gabarito final.  

---

## Como Executar
1. Instalar dependências:  
   ```bash
   pip install -r requirements.txt
   ```

2. Definir a chave de API do Groq no código (`CHAVE_API_GROQ`).  

3. Rodar a aplicação:  
   ```bash
   streamlit run app.py
   ```

---

## Tecnologias Utilizadas
- **Python 3.10+**  
- **Streamlit** para interface.  
- **Groq API** com modelo *Llama 3.3 Versatile*.  
- **Pandas**, **PyPDF2**, **python-docx**, **openpyxl** para leitura de arquivos.  
- **httpx** para transporte customizado.  

---

## Estrutura Simplificada
- `app.py` → código principal da aplicação (interface + lógica).  
- `questoes.txt` → arquivo de saída gerado pelo sistema.  
- `.gitignore` → exclusões do versionamento.  
- `README.md` → este arquivo.  

