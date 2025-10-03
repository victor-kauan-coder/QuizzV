import customtkinter as ctk
import math    

class LoadingAnimation(ctk.CTkFrame):
    """
    Um widget de animação que pode ser colocado dentro de qualquer frame.
    """
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.label = ctk.CTkLabel(self, text="Gerando questões, aguarde alguns segundos..", font=("Arial", 16))
        self.label.pack(pady=40)

        self.animation_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.animation_frame.pack(expand=True, fill="x", pady=20)

        self.ball_size = 20
        self.bounce_height = 20
        self.ball_y = 10
        self.balls = []

        # Container para centralizar as bolinhas
        ball_container = ctk.CTkFrame(self.animation_frame, fg_color="transparent")
        ball_container.pack()

        for i in range(3):
            ball = ctk.CTkFrame(ball_container, width=self.ball_size, height=self.ball_size, corner_radius=self.ball_size)
            ball.pack(side="left", padx=5)
            self.balls.append(ball)

        self.animation_running = True
        self.step = 0
        self.animate()

    def animate(self):
        if not self.animation_running:
            return

        for i, ball in enumerate(self.balls):
            delay_step = self.step - i * 4
            offset = self.bounce_height * (1 + math.sin(delay_step * 0.2)) / 2
            # Usamos pack_configure para mover na vertical, uma alternativa ao place
            # Adicionamos um padding dinâmico no topo para simular o movimento
            ball.pack_configure(pady=(offset, 0))

        self.step += 1
        self.after(50, self.animate)

    def stop(self):
        self.animation_running = False
        self.destroy()