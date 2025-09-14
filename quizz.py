import customtkinter as ctk
import random
import csv
from tkinter import messagebox, filedialog

# --- BANCO DE DADOS DE QUESTÕES ---
def carregar_questoes_csv(nome_arquivo):
    """Lê as questões de um arquivo CSV e as retorna como uma lista."""
    questoes_carregadas = []
    try:
        with open(nome_arquivo, mode='r', encoding='utf-8') as arquivo_csv:
            leitor_csv = csv.DictReader(arquivo_csv, delimiter=';')
            for linha in leitor_csv:
                enunciado = linha['enunciado']
                resposta_bool = linha['resposta'].strip().lower() == 'true'
                justificativa = linha['justificativa']
                questoes_carregadas.append((enunciado, resposta_bool, justificativa))
    except FileNotFoundError:
        messagebox.showerror("Erro de Arquivo", f"O arquivo '{nome_arquivo}' não foi encontrado.")
        return None
    except KeyError as e:
        messagebox.showerror("Erro de Formato", f"O arquivo CSV parece estar mal formatado. Coluna esperada não encontrada: {e}.\n\nVerifique se o cabeçalho é 'enunciado;resposta;justificativa'.")
        return None
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao ler o arquivo CSV: {e}")
        return None
    
    if not questoes_carregadas:
        messagebox.showwarning("Arquivo Vazio", "O arquivo de questões foi encontrado, mas está vazio ou mal formatado.")
        return None
        
    return questoes_carregadas


# --- CONFIGURAÇÕES GLOBAIS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# --- VARIÁVEIS ---
indice_atual = 0
pontuacao = 0
erros = 0
questoes = []
questoes_shuffled = []
questoes_erradas = []


# --- FUNÇÕES DO QUIZ ---
def preparar_nova_rodada(lista_de_questoes):
    global indice_atual, pontuacao, erros, questoes_shuffled
    indice_atual = 0
    pontuacao = 0
    erros = 0
    
    label_acertos.configure(text=f"Acertos: {pontuacao}")
    label_erros.configure(text=f"Erros: {erros}")

    questoes_shuffled = random.sample(lista_de_questoes, len(lista_de_questoes))
    
    frame_final.pack_forget()
    frame_questao.pack(pady=20, padx=20, fill="x", expand=True)
    frame_botoes_vf.pack(pady=10)
    frame_feedback.pack(pady=20, padx=20, fill="x", expand=True)
    
    carregar_proxima_questao()

def iniciar_rodada_completa():
    global questoes_erradas
    questoes_erradas.clear()
    preparar_nova_rodada(questoes)
    
def iniciar_rodada_erradas():
    global questoes_erradas
    questoes_para_refazer = list(questoes_erradas)
    questoes_erradas.clear()
    preparar_nova_rodada(questoes_para_refazer)

def carregar_proxima_questao():
    global indice_atual
    
    if indice_atual < len(questoes_shuffled):
        feedback_label.configure(text="")
        frame_feedback.configure(fg_color="transparent")
        
        enunciado = questoes_shuffled[indice_atual][0]
        questao_label.configure(text=f"Q{indice_atual + 1}: {enunciado}")
        
        progresso_label.configure(text=f"Questão {indice_atual + 1} de {len(questoes_shuffled)}")
        progress_bar.set(indice_atual / len(questoes_shuffled))
        
        btn_v.configure(state="normal")
        btn_f.configure(state="normal")
        btn_proxima.pack_forget()
    else:
        mostrar_resultado_final()

def verificar_resposta(resposta_usuario):
    global pontuacao, erros, indice_atual, questoes_erradas
    
    enunciado, correta, justificativa = questoes_shuffled[indice_atual]
    
    btn_v.configure(state="disabled")
    btn_f.configure(state="disabled")
    
    if resposta_usuario == correta:
        pontuacao += 1
        feedback_msg = f"✅ CORRETO!\n\n{justificativa}"
        frame_feedback.configure(fg_color="#0B4008")
    else:
        erros += 1
        questoes_erradas.append(questoes_shuffled[indice_atual])
        feedback_msg = f"❌ ERRADO!\n\nA resposta correta é '{'Verdadeiro' if correta else 'Falso'}'.\n\n{justificativa}"
        frame_feedback.configure(fg_color="#591415")
    
    label_acertos.configure(text=f"Acertos: {pontuacao}")
    label_erros.configure(text=f"Erros: {erros}")
        
    feedback_label.configure(text=feedback_msg)
    
    indice_atual += 1
    progress_bar.set(indice_atual / len(questoes_shuffled))
    btn_proxima.pack(pady=20)
    
def mostrar_resultado_final():
    frame_questao.pack_forget()
    frame_botoes_vf.pack_forget()
    frame_feedback.pack_forget()
    btn_proxima.pack_forget()
    
    resultado_label.configure(text=f"Quiz Finalizado!\n\nAcertos: {pontuacao}\nErros: {erros}")
    
    if questoes_erradas:
        btn_refazer_erradas.pack(pady=10)
    else:
        btn_refazer_erradas.pack_forget()
        
    frame_final.pack(pady=20, padx=20, fill="both", expand=True)


# --- INICIALIZAÇÃO DO PROGRAMA ---
# Abre a janela para escolher o arquivo CSV
caminho_csv = filedialog.askopenfilename(
    title="Selecione o arquivo de questões (CSV)",
    filetypes=[("Arquivos CSV", "*.csv")]
)

if caminho_csv:
    questoes = carregar_questoes_csv(caminho_csv)
else:
    messagebox.showerror("Nenhum arquivo", "Você não selecionou nenhum arquivo CSV.")
    quit()

if questoes:
    app = ctk.CTk()
    app.title("Quizz")
    app.geometry("900x700")
    app.minsize(700, 600)

    # --- INTERFACE ---
    ctk.CTkLabel(app, text="Quizz", font=("Arial", 24, "bold")).pack(pady=(20, 5))

    frame_placar = ctk.CTkFrame(app, fg_color="transparent")
    frame_placar.pack(pady=5)
    
    label_acertos = ctk.CTkLabel(frame_placar, text="Acertos: 0", font=("Arial", 16), text_color="#00C851")
    label_acertos.grid(row=0, column=0, padx=20)
    
    label_erros = ctk.CTkLabel(frame_placar, text="Erros: 0", font=("Arial", 16), text_color="#ff4444")
    label_erros.grid(row=0, column=1, padx=20)
    
    progresso_label = ctk.CTkLabel(app, text="", font=("Arial", 12))
    progresso_label.pack()
    progress_bar = ctk.CTkProgressBar(app, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=(5, 10))

    frame_questao = ctk.CTkFrame(app)
    frame_questao.pack(pady=20, padx=20, fill="x", expand=True)
    questao_label = ctk.CTkLabel(frame_questao, text="", wraplength=750, font=("Arial", 18), justify="left")
    questao_label.pack(pady=20, padx=20)

    frame_botoes_vf = ctk.CTkFrame(app, fg_color="transparent")
    frame_botoes_vf.pack(pady=10)

    btn_v = ctk.CTkButton(frame_botoes_vf, text="Verdadeiro", width=200, height=50, font=("Arial", 16, "bold"),
                          fg_color="#008000", hover_color="#006400",
                          command=lambda: verificar_resposta(True))
    btn_v.grid(row=0, column=0, padx=20)

    btn_f = ctk.CTkButton(frame_botoes_vf, text="Falso", width=200, height=50, font=("Arial", 16, "bold"),
                          fg_color="#D2042D", hover_color="#AC0B1E",
                          command=lambda: verificar_resposta(False))
    btn_f.grid(row=0, column=1, padx=20)

    frame_feedback = ctk.CTkFrame(app, corner_radius=10)
    frame_feedback.pack(pady=20, padx=20, fill="x", expand=True)
    feedback_label = ctk.CTkLabel(frame_feedback, text="", wraplength=750, font=("Arial", 16), justify="left")
    feedback_label.pack(pady=20, padx=20)

    btn_proxima = ctk.CTkButton(app, text="Próxima Questão", command=carregar_proxima_questao, 
                                width=200, height=40, font=("Arial", 14))

    frame_final = ctk.CTkFrame(app, fg_color="transparent")
    resultado_label = ctk.CTkLabel(frame_final, text="", font=("Arial", 22, "bold"))
    resultado_label.pack(pady=20)
    btn_reiniciar = ctk.CTkButton(frame_final, text="Reiniciar Quiz Completo", command=iniciar_rodada_completa, 
                                  width=200, height=50, font=("Arial", 16))
    btn_reiniciar.pack(pady=10)
    
    btn_refazer_erradas = ctk.CTkButton(frame_final, text="Refazer Erradas", command=iniciar_rodada_erradas, 
                                      fg_color="#555", hover_color="#333",
                                      width=200, height=50, font=("Arial", 16))

    # Inicia o quiz
    iniciar_rodada_completa()
    app.mainloop()
