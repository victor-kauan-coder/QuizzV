import customtkinter as ctk
import random
import json
from tkinter import messagebox, filedialog
from PIL import Image,ImageOps
from loading import *
import os
import sys
import shutil
import tkinter as tk
import threading
from chat import generate_quiz_from_topic
import re

#configurações salvas

modo_default, theme_default = None,None

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


API_KEY = ""

def carregar_configs():
    # Adicione a variável global no início da função
    global modo_default, theme_default, API_KEY
    try:
        with open(resource_path("settings.json"), mode='r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            modo_default, theme_default = data['mode'], data['theme']
            
            # Use .get() para não dar erro se a chave não existir no arquivo
            API_KEY = data.get("api_key", "") 
            
            ctk.set_appearance_mode(modo_default)
            ctk.set_default_color_theme(theme_default)
    except (FileNotFoundError, KeyError):
        # Se o arquivo não existir ou for inválido, cria um padrão
        API_KEY = ""
        salvar_configs("dark", "themes/blue.json", "")

# A função agora aceita o parâmetro 'api_key'
def salvar_configs(mode, theme, api_key):
    with open(resource_path("settings.json"), mode='w', encoding='utf-8') as json_file:
        # Adiciona a chave ao dicionário que será salvo
        data = {"mode": mode, "theme": theme, "api_key": api_key}
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    
    # Atualiza a variável global após salvar
    global API_KEY
    API_KEY = api_key

    messagebox.showinfo("Salvo", "Modificações feitas com sucesso")
    if config_frame: config_frame.pack_forget()
    show_home_page()

QUIZ_DIR = resource_path("quizzes")

# --- VARIÁVEIS GLOBAIS ---
home_widgets = []
loading_frame = None
themes_folder = resource_path("themes")
if not os.path.exists(themes_folder):
    os.makedirs(themes_folder)
theme_options = [f.replace(".json", "") for f in os.listdir(themes_folder) if f.endswith(".json")]


quiz_logo = Image.open(resource_path("image/quiz.ico"))
quiz_logo_ctk = ctk.CTkImage(light_image=quiz_logo, size=(40, 40))
icone = ctk.CTkImage(
    light_image=Image.open(resource_path("image/config.png")),
    dark_image=Image.open(resource_path("image/config_dark.png")),
    size=(24, 24)
)

# Widgets da Interface
app = None
home_frame, quiz_frame, config_frame = None,None,None
scrollable_quiz_frame = None
app_color = None
color_feedback_correct = "#0D5009"
color_feedback_wrong = "#611214" 
color_btn_true = "#008000"
color_btn_false = "#D2042D"
# Estado do Quiz
questions = []
shuffled_questions = []
respostas_questões = {}
wrong_questions = []
current_index = 0
score = 0
errors = 0

def mudar_modo():
    global color_feedback_correct, color_feedback_wrong, color_btn_true, color_btn_false
    current_mode = ctk.get_appearance_mode()
    new_mode = "dark" if current_mode.lower() == "light" else "light"
    ctk.set_appearance_mode(new_mode)
    match new_mode:
        case "dark":
            color_feedback_correct = "#0D5009"
            color_feedback_wrong = "#611214"
            color_btn_true = "#008000"
            color_btn_false = "#D2042D"
        case "light":
            print("oi")
            color_btn_true = "#00D700"
            color_btn_false = "#E8002E"
            color_feedback_correct = "#54DA4D"
            color_feedback_wrong = "#E22F35"

def selecionar_opcao_tema(valor):
    global app_color, home_frame, quiz_frame, config_frame
    caminho_tema = resource_path(os.path.join("themes", f"{valor}.json"))
    if os.path.exists(caminho_tema):
        print("Carregando tema:", caminho_tema)
        app_color = caminho_tema
        ctk.set_default_color_theme(caminho_tema)
        if config_frame:
            config_frame.destroy()
            home_frame.destroy()
            if quiz_frame:
                quiz_frame.destroy()
            show_config_page()
            return
        if home_frame:
            home_frame.destroy()
            show_home_page()
            
        if quiz_frame:
            quiz_frame.destroy()
            show_quiz_page()
            

def carregar_questoes_json(filename):
    loaded_questions = []
    try:
        with open(filename, mode='r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            if not isinstance(data, list):
                messagebox.showerror("Erro de Formato", "O arquivo JSON deve conter uma lista de questões.")
                return None
            for questao in data:
                statement = questao['question']
                answer_str = questao['answer']
                justification = questao['explanation']
                if answer_str.strip().lower() == 'verdadeiro':
                    answer_bool = True
                elif answer_str.strip().lower() == 'falso':
                    answer_bool = False
                else:
                    messagebox.showerror("Erro de Valor", f"A 'answer' para a questão '{statement[:30]}...' deve ser 'Verdadeiro' ou 'Falso'.")
                    return None
                loaded_questions.append((statement, answer_bool, justification))
    except FileNotFoundError:
        messagebox.showerror("Erro de Arquivo", f"O arquivo '{filename}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        messagebox.showerror("Erro de JSON", f"O arquivo '{filename}' não contém um JSON válido ou está malformado.")
        return None
    except KeyError as e:
        messagebox.showerror("Erro de Chave", f"O arquivo JSON está com uma chave faltando: {e}.\n\nVerifique se cada questão tem 'question', 'answer' e 'explanation'.")
        return None
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao ler o arquivo JSON: {e}")
        return None
    if not loaded_questions and data is not None:
        messagebox.showwarning("Arquivo Vazio", "O arquivo de questões foi encontrado, mas não contém nenhuma questão.")
        return None
    return loaded_questions

def enviar_arquivo(arquivos_lista):
    arquivos_lista.append(filedialog.askopenfilename(title="Selecione o arquivo de questões (.pdf)", filetypes=[("Arquivos PDF", "*.pdf")]))

def questoes_geradas(texto_tema_completo,qtd_quest,lista_arquivos):
    global loading_frame
    # --- NOVA VERIFICAÇÃO ---
    if not API_KEY or API_KEY.strip() == "":
        messagebox.showwarning("Chave de API Ausente", 
                               "Por favor, vá em 'Configurações' e insira sua chave de API para usar a geração por IA.")
        return

    if not texto_tema_completo or texto_tema_completo.isspace():
        messagebox.showwarning("Tema Inválido", "Por favor, digite um tema.")
        return
    if not texto_tema_completo or texto_tema_completo.isspace():
        messagebox.showwarning("Tema Inválido", "Por favor, digite um tema.")
        return
    for widget, config in home_widgets:
        widget.pack_forget()
    loading_frame = LoadingAnimation(home_frame)
    loading_frame.pack(pady=100, fill="both", expand=True)
    thread = threading.Thread(target=thread_gerar_quiz, args=(texto_tema_completo,qtd_quest,lista_arquivos,API_KEY))
    thread.start()

def thread_gerar_quiz(texto_tema_completo,qtd_quest,lista_arquivos,api_key):

    partes = texto_tema_completo.split(';')
    tema = partes[0].strip()
    try:
        num_questoes = int(qtd_quest)
    except (ValueError):
        num_questoes = 5
    try:
        resposta_bruta_da_ia = generate_quiz_from_topic(tema,num_questoes,file_paths=lista_arquivos,api_key=api_key)
        app.after(100, lambda: finalizar_geracao(resposta_bruta_da_ia, tema))
    except Exception as e:
        print(f"Erro na thread da IA: {e}")
        app.after(100, lambda: finalizar_geracao(None, tema))

def finalizar_geracao(resposta_bruta_da_ia, tema):
    global loading_frame
    if loading_frame:
        loading_frame.stop()
        loading_frame = None
    for widget, config in home_widgets:
        widget.pack(**config)
    if not resposta_bruta_da_ia:
        messagebox.showerror("Erro na Geração", "A IA não retornou uma resposta.")
        return
    match = re.search(r'\[.*\]', resposta_bruta_da_ia, re.DOTALL)
    if not match:
        messagebox.showerror("Erro de Formato", "Não foi possível encontrar um JSON na resposta da IA.")
        return
    json_limpo_texto = match.group(0)
    try:
        questoes_objeto_python = json.loads(json_limpo_texto)
    except json.JSONDecodeError:
        messagebox.showerror("Erro de JSON", "A IA retornou um JSON malformado.")
        return
    filepath = filedialog.asksaveasfilename(
        initialdir=QUIZ_DIR, title="Salvar Novo Quiz",
        defaultextension=".json", filetypes=[("Arquivos JSON", "*.json")]
    )
    if not filepath: return
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(questoes_objeto_python, f, indent=2, ensure_ascii=False)
    messagebox.showinfo("Sucesso", f"Quiz sobre '{tema}' salvo com sucesso!")
    carregar_quizzes_salvos()

def deletar_quiz(filepath):

    quiz_name = os.path.basename(filepath)
    confirm = messagebox.askyesno("Confirmar Deleção", f"Você tem certeza que deseja deletar o quiz '{quiz_name}'?")
    if confirm:
        try:
            os.remove(filepath)
            carregar_quizzes_salvos()
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível deletar o arquivo: {e}")

def carregar_quizzes_salvos():

    global scrollable_quiz_frame
    if not scrollable_quiz_frame: return
    if not os.path.exists(QUIZ_DIR): os.makedirs(QUIZ_DIR)
    for widget in scrollable_quiz_frame.winfo_children(): widget.destroy()
    quiz_files = sorted([f for f in os.listdir(QUIZ_DIR) if f.endswith('.json')])
    if not quiz_files:
        ctk.CTkLabel(scrollable_quiz_frame, text="Nenhum quiz salvo encontrado.", font=("Arial", 16)).pack(pady=20)
    else:
        for quiz_file in quiz_files:
            quiz_name = os.path.splitext(quiz_file)[0]
            filepath = os.path.join(QUIZ_DIR, quiz_file)
            row_frame = ctk.CTkFrame(scrollable_quiz_frame)
            row_frame.pack(pady=5, padx=10, fill="x")
            row_frame.grid_columnconfigure(0, weight=1)
            ctk.CTkButton(row_frame, text=quiz_name, font=("Arial", 16),corner_radius=32, command=lambda p=filepath: jogar_quiz(p), height=40).grid(row=0, column=0, padx=(0, 5), sticky="ew")
            ctk.CTkButton(row_frame, text="X", font=("Arial", 12), command=lambda p=filepath: deletar_quiz(p), width=40, height=40, fg_color="transparent", hover_color="#AC0B1E").grid(row=0, column=1)

def jogar_quiz(filepath):

    global questions, quiz_frame
    questions = carregar_questoes_json(filepath)
    if questions:
        home_frame.pack_forget()
        show_quiz_page()
        quiz_frame.pack(pady=20, padx=20, fill="both", expand=True)
        start_full_round()

def abrir_selecionar_quiz():

    caminho_json = filedialog.askopenfilename(title="Selecione o arquivo de questões (.json)", filetypes=[("Arquivos JSON", "*.json")])
    if caminho_json:
        if not os.path.exists(QUIZ_DIR): os.makedirs(QUIZ_DIR)
        nome_arquivo = os.path.basename(caminho_json)
        caminho_destino = os.path.join(QUIZ_DIR, nome_arquivo)
        try:
            shutil.copy2(caminho_json, caminho_destino)
            messagebox.showinfo("Sucesso", f"O quiz '{nome_arquivo}' foi importado com sucesso!")
            carregar_quizzes_salvos()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao importar o arquivo: {e}")



def show_home_page():
    global icone, home_frame, scrollable_quiz_frame, valor_selecionado, home_widgets, arquivos, arquivos_frame
    arquivos = []
    home_widgets.clear()
    home_frame = ctk.CTkFrame(app, fg_color="transparent")
    home_frame.pack(pady=20, padx=20, fill="both", expand=True)
    bnt_config = ctk.CTkButton(home_frame,text="", image=icone, command=show_config_page,fg_color="transparent", font=("Arial", 24, "bold"), width=40, height=40)
    bnt_config.place(x=20, y=20)
    def add_widget(widget, **kwargs):
        widget.pack(**kwargs)
        home_widgets.append((widget, kwargs))

    def atualizar_lista_arquivos():
        for widget in arquivos_frame.winfo_children():
            widget.destroy()

        if not arquivos:
            ctk.CTkLabel(arquivos_frame, text="Nenhum arquivo selecionado.",
                        font=("Arial", 12)).pack(anchor="c")
        else:
            for i, a in enumerate(arquivos):
                nome = a.split("/")[-1]
                item_frame = ctk.CTkFrame(arquivos_frame, fg_color="transparent")
                item_frame.pack(fill="x", pady=2)

                ctk.CTkLabel(item_frame, text=f"- {nome}", font=("Arial", 12), anchor="w").pack(side="left", padx=5)

                def remover_arquivo(idx=i):
                    arquivos.pop(idx)
                    atualizar_lista_arquivos()

                ctk.CTkButton(item_frame, text="x", width=30, height=20, fg_color="red",
                            hover_color="#aa0000", command=remover_arquivo).pack(side="right", padx=5)

    def selecionar_arquivos():
        global arquivos
        arquivos = list(filedialog.askopenfilenames(
            title="Selecione os arquivos do quiz",
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
        ))
        atualizar_lista_arquivos()

    title_label = ctk.CTkLabel(home_frame,image=quiz_logo_ctk,
        compound="left",padx=10, text="QuizzV", font=("Arial", 28, "bold"))
    add_widget(title_label, pady=(20, 20))

    frame_opcoes_principais = ctk.CTkFrame(home_frame, fg_color="transparent")
    add_widget(frame_opcoes_principais, pady=10)

    ctk.CTkButton(frame_opcoes_principais,corner_radius=32, text="Importar Quiz", font=("Arial", 16),
                  command=abrir_selecionar_quiz, width=200, height=50).pack(side="left", padx=10)

    

    frame_gerador = ctk.CTkScrollableFrame(home_frame, width=600, height=300) 
    add_widget(frame_gerador, pady=20, padx=10, fill="none")

    frame_gerador.grid_columnconfigure((0, 1), weight=1)


    ctk.CTkLabel(frame_gerador, text="Gerar novo Quiz com IA", font=("Arial", 18, "bold"))\
        .grid(row=0, column=0, columnspan=2, pady=(10,5))
    ctk.CTkLabel(frame_gerador, text="Digite um tema (ex: 'História do Brasil;5'):", font=("Arial", 12))\
        .grid(row=1, column=0, columnspan=2)

    texto_topico = ctk.CTkTextbox(frame_gerador,corner_radius=10, width=250, height=50, border_width=1)
    texto_qtd_quest = ctk.CTkTextbox(frame_gerador,corner_radius=10, width=50, height=50,  border_width=1, wrap="word")

    texto_topico.grid(row=2, column=0, padx=(0,10), pady=5,columnspan=3)
    texto_qtd_quest.grid(row=2, column=1, padx=(0,0), pady=5,columnspan=3)

    # Botão para selecionar arquivos
    ctk.CTkButton(frame_gerador,corner_radius=32, text="Selecionar Arquivos",
                  font=("Arial", 12), command=selecionar_arquivos,
                  width=150, height=30).grid(row=3, column=0,columnspan=2, padx=5, pady=5)

    arquivos_frame = ctk.CTkFrame(frame_gerador, fg_color="transparent",width=600, height=50)
    arquivos_frame.grid(row=4, column=0, columnspan=2)


    ctk.CTkButton(frame_gerador,corner_radius=32, text="Gerar Quiz", font=("Arial", 16),
                  command=lambda: questoes_geradas(texto_topico.get("1.0", "end").strip(),texto_qtd_quest.get("1.0","end").strip(), arquivos),
                  width=200, height=40).grid(row=5, column=0, columnspan=2,pady=(0,30))

    quizzes_label = ctk.CTkLabel(home_frame, text="Quizzes Salvos:", font=("Arial", 18, "bold"))
    add_widget(quizzes_label, pady=(20, 10))

    scrollable_quiz_frame = ctk.CTkScrollableFrame(home_frame,height=600,width=800)
    add_widget(scrollable_quiz_frame, pady=10, padx=20, fill="both", expand=True)

    carregar_quizzes_salvos()

def show_config_page():
    global home_frame, config_frame
    print("Entrando nas configurações")

    if home_frame:
        home_frame.pack_forget()


    config_frame = ctk.CTkFrame(app, fg_color="transparent")
    config_frame.pack(fill="both", expand=True, padx=20, pady=20)

    config_frame.grid_columnconfigure(0, weight=1)
    config_frame.grid_rowconfigure(1, weight=1)    


    header_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
    header_frame.grid_columnconfigure(1, weight=1) 

    back_button = ctk.CTkButton(config_frame, text="←", command=back_home, font=("Arial", 24, "bold"), width=40, height=40)
    back_button.place(x=20, y=20)
    # back_button.grid(row=0, column=0, sticky="w")

    page_title = ctk.CTkLabel(header_frame, text="Configurações", font=("Arial", 28, "bold"))
    page_title.grid(row=0, column=1, sticky="ew")

    options_frame = ctk.CTkFrame(config_frame,width=200)
    options_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    options_frame.grid_columnconfigure(1, weight=1)

    label_api_key = ctk.CTkLabel(options_frame, text="Chave de API (IA):", font=("Arial", 16))
    label_api_key.grid(row=0, column=0, padx=20, pady=20, sticky="w")

    global api_key_var
    api_key_var = tk.StringVar(value=API_KEY) 

    api_key_entry = ctk.CTkEntry(options_frame, textvariable=api_key_var, show="*", width=250)
    api_key_entry.grid(row=0, column=1, padx=20, pady=20, sticky="e")

    label_modo = ctk.CTkLabel(options_frame, text="Modo de Exibição:", font=("Arial", 16))

    label_modo.grid(row=3, column=0, padx=20, pady=20, sticky="w") 

    switch_tema = ctk.CTkSwitch(options_frame, text="", font=("Arial", 14), command=mudar_modo,
                                progress_color=("#1F6AA5", "#1F6AA5"))
    switch_tema.grid(row=3, column=1, padx=20, pady=20, sticky="e")

    if ctk.get_appearance_mode().lower() == "light":
        switch_tema.deselect()
    else:
        switch_tema.select()

    if theme_options:
        label_tema = ctk.CTkLabel(options_frame, text="Cor do Tema:", font=("Arial", 16))
        label_tema.grid(row=1, column=0, padx=20, pady=20, sticky="w")

        theme_menu = ctk.CTkOptionMenu(options_frame, values=theme_options,
                                       command=selecionar_opcao_tema, variable=valor_selecionado,
                                       width=200, font=("Arial", 14), dropdown_font=("Arial", 14))
        theme_menu.grid(row=1, column=1, padx=20, pady=20, sticky="e")

    btn_salvar = ctk.CTkButton(config_frame,corner_radius=32, text="Salvar Alterações",
                               command=lambda: salvar_configs(ctk.get_appearance_mode().lower(), "themes/"+valor_selecionado.get()+".json"),
                               height=40, font=("Arial", 16, "bold"))
    btn_salvar.configure(command=lambda: salvar_configs(
        ctk.get_appearance_mode().lower(),
        "themes/"+valor_selecionado.get()+".json",
        api_key_var.get() 
    ))
    btn_salvar.grid(row=2, column=0, sticky="ew", padx=10, pady=(20, 0))

def show_quiz_page():
    global color_btn_true,color_btn_false, quiz_frame,botoes_frame, correct_label, errors_label,btn_back, progress_label, progress_bar, question_label, app_color,btn_true, btn_false, feedback_label, btn_next, final_frame, results_label, btn_restart, btn_redo_wrong, btn_goto_home, feedback_frame, question_frame, vf_buttons_frame
    
    quiz_frame = ctk.CTkFrame(app, fg_color="transparent")
    botoes_frame = ctk.CTkFrame(quiz_frame, fg_color="transparent")
    
    back_button = ctk.CTkButton(quiz_frame, text="←", command=back_home, font=("Arial", 24, "bold"), width=40, height=40)
    back_button.place(x=20, y=20)

    ctk.CTkLabel(quiz_frame, text="Quiz", font=("Arial", 24, "bold")).pack(pady=(20, 5))
    scoreboard_frame = ctk.CTkFrame(quiz_frame, fg_color="transparent")
    scoreboard_frame.pack(pady=5)
    correct_label = ctk.CTkLabel(scoreboard_frame, text="Acertos: 0", font=("Arial", 16), text_color="#0BB44E"); correct_label.grid(row=0, column=0, padx=20)
    errors_label = ctk.CTkLabel(scoreboard_frame, text="Erros: 0", font=("Arial", 16), text_color="#e23535"); errors_label.grid(row=0, column=1, padx=20)
    progress_label = ctk.CTkLabel(quiz_frame, text="", font=("Arial", 12)); progress_label.pack()
    progress_bar = ctk.CTkProgressBar(quiz_frame, width=400); progress_bar.set(0); progress_bar.pack(pady=(5, 10))
    question_frame = ctk.CTkFrame(quiz_frame)
    question_label = ctk.CTkLabel(question_frame, text="", wraplength=750, font=("Arial", 18), justify="left"); question_label.pack(pady=20, padx=20)
    vf_buttons_frame = ctk.CTkFrame(quiz_frame, fg_color="transparent")
    
    btn_true = ctk.CTkButton(vf_buttons_frame,corner_radius=32, text="Verdadeiro", width=200, height=50, font=("Arial", 16, "bold"), fg_color=color_btn_true, hover_color="#006400", command=lambda: check_answer(True)); btn_true.grid(row=0, column=0, padx=20)
    btn_false = ctk.CTkButton(vf_buttons_frame,corner_radius=32, text="Falso", width=200, height=50, font=("Arial", 16, "bold"), fg_color=color_btn_false, hover_color="#AC0B1E", command=lambda: check_answer(False)); btn_false.grid(row=0, column=1, padx=20)
    feedback_frame = ctk.CTkFrame(quiz_frame, corner_radius=10)
    feedback_label = ctk.CTkLabel(feedback_frame, text="", wraplength=750, font=("Arial", 16), justify="left"); feedback_label.pack(pady=20, padx=20)
    btn_next = ctk.CTkButton(botoes_frame, text="Próxima Questão",corner_radius=32, command=lambda: load_next_question(), width=200, height=40, font=("Arial", 14))
    btn_back = ctk.CTkButton(botoes_frame, text="Questão Anterior",corner_radius=32, command=lambda: load_back_question(), width=200, height=40, font=("Arial", 14))
    final_frame = ctk.CTkFrame(quiz_frame, fg_color="transparent")
    results_label = ctk.CTkLabel(final_frame, text="", font=("Arial", 22, "bold")); results_label.pack(pady=20)
    btn_restart = ctk.CTkButton(final_frame, text="Reiniciar Quiz Completo",corner_radius=32, command=lambda: start_full_round(), width=200, height=50, font=("Arial", 16)); btn_restart.pack(pady=10)
    btn_redo_wrong = ctk.CTkButton(final_frame, text="Refazer Questões Erradas",corner_radius=32, command=lambda: start_wrong_round(),width=200, height=50, font=("Arial", 16))
    btn_goto_home = ctk.CTkButton(final_frame, text="Início",corner_radius=32, command=lambda: back_home(), width=200, height=50, font=("Arial", 16))


def prepare_new_round(list_of_questions):
    global current_index, score, errors, shuffled_questions,respostas_questões
    if not list_of_questions: return
    current_index, score, errors = 0, 0, 0
    respostas_questões = {}
    correct_label.configure(text=f"Acertos: {score}"); errors_label.configure(text=f"Erros: {errors}")
    shuffled_questions = random.sample(list_of_questions, len(list_of_questions))
    final_frame.pack_forget()
    question_frame.pack(pady=20, padx=20, fill="x", expand=True)
    vf_buttons_frame.pack(pady=10)
    feedback_frame.pack_forget()
    load_next_question()

def back_home():
    if quiz_frame: 
        print("quizzzzzzzzzzzzzzzzzzzz")
        quiz_frame.pack_forget()
    if config_frame: config_frame.pack_forget()
    show_home_page()

def start_full_round():
    global wrong_questions; wrong_questions = []
    prepare_new_round(questions)
    
def start_wrong_round():
    global wrong_questions
    questions_to_redo = list(wrong_questions); wrong_questions = []
    prepare_new_round(questions_to_redo)

def show_question_prompt(index):
    global color_btn_true, color_btn_false
    """Mostra a interface para responder uma pergunta."""
    botoes_frame.pack_forget()
    feedback_frame.pack_forget()
    
    statement = shuffled_questions[index][0]
    question_label.configure(text=f"Q{index + 1}: {statement}")
    progress_label.configure(text=f"Questão {index + 1} de {len(shuffled_questions)}")
    progress_bar.set((index + 1) / len(shuffled_questions))
    
    # Mostra os botões de V/F
    vf_buttons_frame.pack(pady=10)
    btn_true.configure(state="normal", fg_color=color_btn_true)
    btn_false.configure(state="normal",fg_color=color_btn_false)

def show_feedback(index):
    """Mostra o feedback de uma pergunta já respondida."""
    global color_feedback_correct, color_feedback_wrong
    vf_buttons_frame.pack_forget() # Esconde botões de V/F
    
    _, correct_answer, justification = shuffled_questions[index]
    user_answer = respostas_questões.get(index)

    if user_answer == correct_answer:
        feedback_msg = f"✅ CORRETO!\n\n{justification}"
        feedback_frame.configure(fg_color=color_feedback_correct)
    else:
        feedback_msg = f"❌ ERRADO!\n\nA resposta correta é '{'Verdadeiro' if correct_answer else 'Falso'}'.\n\n{justification}"
        feedback_frame.configure(fg_color=color_feedback_wrong)
        
    feedback_label.configure(text=feedback_msg)
    feedback_frame.pack(pady=20, padx=20, fill="x", expand=True)
    botoes_frame.pack(pady=5)
    btn_back.grid(row=0,column=0,padx=10)
    btn_next.grid(row=0,column=1)

def check_answer(user_answer):
    global score, errors, current_index, wrong_questions
    
    # Armazena a resposta no dicionário
    respostas_questões[current_index] = user_answer
    
    _, correct_answer, _ = shuffled_questions[current_index]
    
    # Atualiza a pontuação
    if user_answer == correct_answer:
        score += 1
    else:
        errors += 1
        wrong_questions.append(shuffled_questions[current_index])
    
    correct_label.configure(text=f"Acertos: {score}")
    errors_label.configure(text=f"Erros: {errors}")
    
    # Mostra o feedback e os botões de navegação
    show_feedback(current_index)

def load_next_question():
    global current_index
    
    # Se já houver uma resposta para a questão atual, avança o índice
    if current_index in respostas_questões:
        current_index += 1

    # Verifica se o quiz acabou
    if current_index >= len(shuffled_questions):
        botoes_frame.pack_forget()
        show_final_results()
        return

    if current_index in respostas_questões:
        show_feedback(current_index)
        statement = shuffled_questions[current_index][0]
        question_label.configure(text=f"Q{current_index + 1}: {statement}")
        progress_label.configure(text=f"Questão {current_index + 1} de {len(shuffled_questions)}")
    else: 
        show_question_prompt(current_index)

def load_back_question():
    global current_index
    if current_index > 0 and (current_index - 1) in respostas_questões:
        current_index -= 1
        show_feedback(current_index)
        statement = shuffled_questions[current_index][0]
        question_label.configure(text=f"Q{current_index + 1}: {statement}")
        progress_label.configure(text=f"Questão {current_index + 1} de {len(shuffled_questions)}")
    
    
def show_final_results():
    question_frame.pack_forget(); vf_buttons_frame.pack_forget(); feedback_frame.pack_forget(); btn_next.pack_forget()
    results_label.configure(text=f"Quiz Finalizado!\n\nAcertos: {score}\nErros: {errors}")
    if wrong_questions: btn_redo_wrong.pack(pady=10)
    else: btn_redo_wrong.pack_forget()
    btn_goto_home.pack(pady=10)
    final_frame.pack(pady=20, padx=20, fill="both", expand=True)
    btn_restart.pack(pady=10)

if __name__ == "__main__":
    app = ctk.CTk()
    app.title("QuizzV")
    app.iconbitmap(resource_path("image/quiz.ico"))
    app.geometry("900x700")
    app.minsize(700, 600)
    carregar_configs()
    valor_selecionado = tk.StringVar(master=app, value=theme_options[0] if theme_options else "")
    # if valor_selecionado.get():
    #     selecionar_opcao_tema(valor_selecionado.get())
    
    show_quiz_page()
    show_home_page()

    app.mainloop()