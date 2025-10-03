import google.generativeai as genai
import os

def generate_quiz_from_topic(topic: str, num_questions: int, file_paths: list = None,api_key=""):
    if not api_key:

        raise ValueError("A chave de API não foi fornecida.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    if file_paths:
        uploaded_files = []
        print(f"Iniciando upload de {len(file_paths)} arquivo(s) para a API Gemini...")
        try:
            for file_path in file_paths:
                print(f"  -> Fazendo upload de: {os.path.basename(file_path)}")

                file_object = genai.upload_file(path=file_path)
                uploaded_files.append(file_object)
            print("Upload concluído.")
       
        except Exception as e:
            print(f"Ocorreu um erro durante o upload dos arquivos: {e}")
            return None
        prompt_final = f"""
            ## Papel
            Atue como um especialista em design instrucional.

            ## Tarefa Principal
            Sua tarefa é criar um quiz de {num_questions} questões com base nos documentos fornecidos, utilizando o tópico "{topic}" como um guia temático.

            ## Requisitos
            1.  **Fonte de Conhecimento:** Use os documentos fornecidos como a **fonte primária** de informação. Você deve enriquecer as questões, conectando os fatos dos documentos com seu conhecimento geral sobre o tópico para criar perguntas que exijam raciocínio.
            2.  **Foco no Tema:** Use o tópico "{topic}" como um guia para selecionar as informações mais relevantes dos documentos e contextualizá-las.
            3.  **Tipo de Questão:** As perguntas devem avaliar a capacidade de aplicar e contextualizar a informação, e não apenas a memorização do que está nos arquivos.
            4.  **Formato de Saída:** Retorne uma lista de objetos JSON válida, contendo as chaves "question", "answer" deve SOMENTE ("Verdadeiro" ou "Falso"), e "explanation". A explicação deve justificar a resposta, idealmente conectando o fato do documento com o contexto mais amplo.Certifique-se de que cada objeto, exceto o último, é seguido por uma vírgula.
            """
        full_prompt = uploaded_files + [prompt_final]
        print(f"Iniciando chamada à API com arquivos para o tema: '{topic}'...")
       

    else:
        full_prompt = f"""
## Papel
Atue como um especialista em design instrucional.

## Tarefa Principal
Com base no seu conhecimento geral sobre o tema "{topic}", sua tarefa é gerar uma lista de {num_questions} questões.

## Requisitos
1.  **Profundidade Cognitiva:** As questões devem avaliar o raciocínio crítico sobre o impacto e contexto do tema, não a memorização.
2.  **Formato de Saída:** Retorne uma lista de objetos JSON válida, contendo as chaves "question", "answer" deve SOMENTE ("Verdadeiro" ou "Falso"), e "explanation". Certifique-se de que cada objeto, exceto o último, é seguido por uma vírgula.
"""
        print(f"Iniciando chamada à API para o tema: '{topic}'...")

    try:
        response = model.generate_content(full_prompt)

        if file_paths and 'uploaded_files' in locals():
            for file in uploaded_files:
                genai.delete_file(file.name)
            print("Arquivos de contexto foram limpos do servidor.")

        return response.text
    except Exception as e:
        print(f"Ocorreu um erro na chamada da API: {e}")
        return None
# --- Bloco de teste ---
if __name__ == '__main__':
#  # Teste 1: Gerar quiz apenas com tema
#     print("--- INICIANDO TESTE 1: TEMA GERAL ---")
#     resultado_tema = generate_quiz_from_topic(topic="Inteligência Artificial", num_questions=3)
#     if resultado_tema:
#         print(resultado_tema)
#     else:
#         print("Falha no teste de tema.")

#     # Teste 2: Gerar quiz com arquivos
#     print("\n--- INICIANDO TESTE 2: COM ARQUIVOS ---")
#     caminhos_teste = ["teste.pdf", "teste2.pdf"]
#     for path in caminhos_teste:
#         if not os.path.exists(path):
#             with open(path, "w", encoding="utf-8") as f:
#                 f.write(f"O conteúdo deste arquivo ({path}) é apenas para teste.")
    
#     resultado_arquivos = generate_quiz_from_topic(topic="Resumo dos documentos", num_questions=2, file_paths=caminhos_teste)
#     if resultado_arquivos:
#         print(resultado_arquivos)
#     else:
#         print("Falha no teste com arquivos.")
    pass