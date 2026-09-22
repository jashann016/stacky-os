import tkinter as tk
import math
import time
import threading

class StackyNotchHUD:
    """Integrated Dynamic Notch Island and Floating Presence for Stacky AI."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stacky AI Presence")
        
        # Transparent, frameless, topmost window
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # macOS transparency attributes
        try:
            self.root.wm_attributes("-alpha", 0.94)
        except Exception:
            pass

        self.root.config(bg="#02060d")

        # Dimensions: Seamless notch integration
        self.width = 480
        self.height = 54
        
        screen_w = self.root.winfo_screenwidth()
        x_pos = int((screen_w - self.width) / 2)
        y_pos = 0  # Attached right to the top bezel / notch
        
        self.root.geometry(f"{self.width}x{self.height}+{x_pos}+{y_pos}")

        self.canvas = tk.Canvas(
            self.root, 
            width=self.width, 
            height=self.height, 
            bg="#02060d", 
            highlightthickness=1, 
            highlightbackground="#00f3ff"
        )
        self.canvas.pack(fill="both", expand=True)

        # Draw Notch integration curvature
        self.canvas.create_arc(0, -20, 30, 30, start=180, extent=90, style="arc", outline="#00f3ff")
        self.canvas.create_arc(self.width-30, -20, self.width, 30, start=270, extent=90, style="arc", outline="#00f3ff")

        # Arc Reactor Core Icon
        self.arc_outer = self.canvas.create_oval(18, 14, 42, 38, outline="#00f3ff", width=2)
        self.arc_inner = self.canvas.create_oval(24, 20, 36, 32, fill="#00f3ff", outline="")

        # Soundwave Equalizer Bars (9 dynamic frequency lines)
        self.bars = []
        for i in range(9):
            bx = 56 + (i * 6)
            line = self.canvas.create_line(bx, 25, bx, 27, fill="#00f3ff", width=2)
            self.bars.append(line)

        # Micro-typography Status Text
        self.status_label = self.canvas.create_text(
            124, 25, 
            anchor="w", 
            text="STACKY MK-II // ALL SYSTEMS NOMINAL, SIR", 
            fill="#e0f7ff", 
            font=("Courier", 10, "bold")
        )

        # Animation Loop
        self.running = True
        threading.Thread(target=self._animate_pulse, daemon=True).start()

        # Click to dismiss or trigger
        self.canvas.bind("<Button-1>", lambda e: self.trigger_briefing())

    def trigger_briefing(self):
        self.update_status("DISPATCHING TELEPHONY BRIEFING...", "#ff9d00")
        # Reset after 3 seconds
        threading.Thread(target=self._auto_reset, daemon=True).start()

    def _auto_reset(self):
        time.sleep(3)
        self.update_status("STACKY MK-II // ALL SYSTEMS NOMINAL, SIR", "#e0f7ff")

    def update_status(self, text: str, color: str = "#e0f7ff"):
        self.canvas.itemconfig(self.status_label, text=text, fill=color)

    def _animate_pulse(self):
        step = 0
        while self.running:
            step += 0.25
            for idx, bar in enumerate(self.bars):
                offset = math.sin(step + (idx * 0.7)) * 9
                bx = 56 + (idx * 6)
                self.canvas.coords(bar, bx, 25 - offset, bx, 27 + offset)
            time.sleep(0.04)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StackyNotchHUD()
    app.run()
