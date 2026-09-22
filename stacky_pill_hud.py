import tkinter as tk
import time
import threading

class StackyFloatingPill:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stacky AI")
        
        # Frameless, transparent, floating always-on-top window
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.config(bg="#050b14")
        
        # Dimensions
        self.width = 460
        self.height = 48
        
        # Position centered at the very top (just below the notch)
        screen_width = self.root.winfo_screenwidth()
        x_pos = int((screen_width - self.width) / 2)
        y_pos = 12
        self.root.geometry(f"{self.width}x{self.height}+{x_pos}+{y_pos}")
        
        # Rounded look canvas
        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bg="#050b14", 
            highlightthickness=1, 
            highlightbackground="#00f3ff"
        )
        self.canvas.pack(fill="both", expand=True)

        # Draw glowing mini arc reactor icon
        self.canvas.create_oval(14, 12, 36, 34, outline="#00f3ff", width=2)
        self.canvas.create_oval(19, 17, 31, 29, fill="#00f3ff", outline="")

        # Dynamic Soundwave bars
        self.wave_bars = []
        for i in range(7):
            bx = 48 + (i * 7)
            bar = self.canvas.create_line(bx, 23, bx, 25, fill="#00f3ff", width=2)
            self.wave_bars.append(bar)

        # Live Status text
        self.status_text = self.canvas.create_text(
            110, 23, 
            anchor="w", 
            text="STACKY // ONLINE & OBSERVING", 
            fill="#e0f7ff", 
            font=("Courier", 11, "bold")
        )

        # Pulse animation thread
        self.animating = True
        threading.Thread(target=self._animate_wave, daemon=True).start()

    def set_status(self, text, fill_color="#e0f7ff"):
        self.canvas.itemconfig(self.status_text, text=text, fill=fill_color)

    def _animate_wave(self):
        import math
        step = 0
        while self.animating:
            step += 0.3
            for idx, bar in enumerate(self.wave_bars):
                offset = math.sin(step + (idx * 0.8)) * 8
                bx = 48 + (idx * 7)
                self.canvas.coords(bar, bx, 23 - offset, bx, 25 + offset)
            time.sleep(0.05)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StackyFloatingPill()
    app.run()
