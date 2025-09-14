import customtkinter as ctk
import random
import csv
from tkinter import messagebox, filedialog

# --- QUESTION DATABASE ---
def load_questions_csv(filename):
    """Reads questions from a CSV file and returns them as a list."""
    loaded_questions = []
    try:
        with open(filename, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=';')
            for row in csv_reader:
                statement = row['enunciado']
                answer_bool = row['resposta'].strip().lower() == 'true'
                justification = row['justificativa']
                loaded_questions.append((statement, answer_bool, justification))
    except FileNotFoundError:
        messagebox.showerror("File Error", f"The file '{filename}' was not found.")
        return None
    except KeyError as e:
        messagebox.showerror("Format Error", f"The CSV file seems to be malformed. Expected column not found: {e}.\n\nMake sure the header is 'enunciado;resposta;justificativa'.")
        return None
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An error occurred while reading the CSV file: {e}")
        return None
    
    if not loaded_questions:
        messagebox.showwarning("Empty File", "The questions file was found but is empty or malformed.")
        return None
        
    return loaded_questions


# --- GLOBAL SETTINGS ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# --- VARIABLES ---
current_index = 0
score = 0
errors = 0
questions = []
shuffled_questions = []
wrong_questions = []


# --- QUIZ FUNCTIONS ---
def prepare_new_round(list_of_questions):
    global current_index, score, errors, shuffled_questions
    current_index = 0
    score = 0
    errors = 0
    
    correct_label.configure(text=f"Correct: {score}")
    errors_label.configure(text=f"Errors: {errors}")

    shuffled_questions = random.sample(list_of_questions, len(list_of_questions))
    
    final_frame.pack_forget()
    question_frame.pack(pady=20, padx=20, fill="x", expand=True)
    vf_buttons_frame.pack(pady=10)
    feedback_frame.pack(pady=20, padx=20, fill="x", expand=True)
    
    load_next_question()

def start_full_round():
    global wrong_questions
    wrong_questions.clear()
    prepare_new_round(questions)
    
def start_wrong_round():
    global wrong_questions
    questions_to_redo = list(wrong_questions)
    wrong_questions.clear()
    prepare_new_round(questions_to_redo)

def load_next_question():
    global current_index
    
    if current_index < len(shuffled_questions):
        feedback_label.configure(text="")
        feedback_frame.configure(fg_color="transparent")
        
        statement = shuffled_questions[current_index][0]
        question_label.configure(text=f"Q{current_index + 1}: {statement}")
        
        progress_label.configure(text=f"Question {current_index + 1} of {len(shuffled_questions)}")
        progress_bar.set(current_index / len(shuffled_questions))
        
        btn_true.configure(state="normal")
        btn_false.configure(state="normal")
        btn_next.pack_forget()
    else:
        show_final_results()

def check_answer(user_answer):
    global score, errors, current_index, wrong_questions
    
    statement, correct_answer, justification = shuffled_questions[current_index]
    
    btn_true.configure(state="disabled")
    btn_false.configure(state="disabled")
    
    if user_answer == correct_answer:
        score += 1
        feedback_msg = f"✅ CORRECT!\n\n{justification}"
        feedback_frame.configure(fg_color="#0D5009")
    else:
        errors += 1
        wrong_questions.append(shuffled_questions[current_index])
        feedback_msg = f"❌ WRONG!\n\nThe correct answer is '{'True' if correct_answer else 'False'}'.\n\n{justification}"
        feedback_frame.configure(fg_color="#611214")
    
    correct_label.configure(text=f"Correct: {score}")
    errors_label.configure(text=f"Errors: {errors}")
        
    feedback_label.configure(text=feedback_msg)
    
    current_index += 1
    progress_bar.set(current_index / len(shuffled_questions))
    btn_next.pack(pady=20)
    
def show_final_results():
    question_frame.pack_forget()
    vf_buttons_frame.pack_forget()
    feedback_frame.pack_forget()
    btn_next.pack_forget()
    
    results_label.configure(text=f"Quiz Finished!\n\nCorrect: {score}\nErrors: {errors}")
    
    if wrong_questions:
        btn_redo_wrong.pack(pady=10)
    else:
        btn_redo_wrong.pack_forget()
        
    final_frame.pack(pady=20, padx=20, fill="both", expand=True)


# --- PROGRAM INITIALIZATION ---
# Opens the window to choose the CSV file
csv_path = filedialog.askopenfilename(
    title="Select the questions file (CSV)",
    filetypes=[("CSV Files", "*.csv")]
)

if csv_path:
    questions = load_questions_csv(csv_path)
else:
    messagebox.showerror("No File", "You did not select any CSV file.")
    quit()

if questions:
    app = ctk.CTk()
    app.title("Quiz")
    app.geometry("900x700")
    app.minsize(700, 600)

    # --- INTERFACE ---
    ctk.CTkLabel(app, text="Quiz", font=("Arial", 24, "bold")).pack(pady=(20, 5))

    scoreboard_frame = ctk.CTkFrame(app, fg_color="transparent")
    scoreboard_frame.pack(pady=5)
    
    correct_label = ctk.CTkLabel(scoreboard_frame, text="Correct: 0", font=("Arial", 16), text_color="#0BB44E")
    correct_label.grid(row=0, column=0, padx=20)
    
    errors_label = ctk.CTkLabel(scoreboard_frame, text="Errors: 0", font=("Arial", 16), text_color="#e23535")
    errors_label.grid(row=0, column=1, padx=20)
    
    progress_label = ctk.CTkLabel(app, text="", font=("Arial", 12))
    progress_label.pack()
    progress_bar = ctk.CTkProgressBar(app, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=(5, 10))

    question_frame = ctk.CTkFrame(app)
    question_frame.pack(pady=20, padx=20, fill="x", expand=True)
    question_label = ctk.CTkLabel(question_frame, text="", wraplength=750, font=("Arial", 18), justify="left")
    question_label.pack(pady=20, padx=20)

    vf_buttons_frame = ctk.CTkFrame(app, fg_color="transparent")
    vf_buttons_frame.pack(pady=10)

    btn_true = ctk.CTkButton(vf_buttons_frame, text="True", width=200, height=50, font=("Arial", 16, "bold"),
                             fg_color="#008000", hover_color="#006400",
                             command=lambda: check_answer(True))
    btn_true.grid(row=0, column=0, padx=20)

    btn_false = ctk.CTkButton(vf_buttons_frame, text="False", width=200, height=50, font=("Arial", 16, "bold"),
                             fg_color="#D2042D", hover_color="#AC0B1E",
                             command=lambda: check_answer(False))
    btn_false.grid(row=0, column=1, padx=20)

    feedback_frame = ctk.CTkFrame(app, corner_radius=10)
    feedback_frame.pack(pady=20, padx=20, fill="x", expand=True)
    feedback_label = ctk.CTkLabel(feedback_frame, text="", wraplength=750, font=("Arial", 16), justify="left")
    feedback_label.pack(pady=20, padx=20)

    btn_next = ctk.CTkButton(app, text="Next Question", command=load_next_question, 
                             width=200, height=40, font=("Arial", 14))

    final_frame = ctk.CTkFrame(app, fg_color="transparent")
    results_label = ctk.CTkLabel(final_frame, text="", font=("Arial", 22, "bold"))
    results_label.pack(pady=20)
    btn_restart = ctk.CTkButton(final_frame, text="Restart Full Quiz", command=start_full_round, 
                                 width=200, height=50, font=("Arial", 16))
    btn_restart.pack(pady=10)
    
    btn_redo_wrong = ctk.CTkButton(final_frame, text="Redo Wrong Answers", command=start_wrong_round, 
                                     fg_color="#555", hover_color="#333",
                                     width=200, height=50, font=("Arial", 16))

    # Starts the quiz
    start_full_round()
    app.mainloop()