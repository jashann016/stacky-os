import tkinter as tk
import time
import threading
import math

class StackyLuminousBorder:
    """True animated Apple Intelligence & Stark HUD screen perimeter glow."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Stacky Luminous Border")
        
        # Transparent click-through overlay
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # Transparent window background
        self.root.config(bg="black")
        try:
            self.root.wm_attributes("-transparentcolor", "black")
        except Exception:
            try:
                self.root.wm_attributes("-alpha", 0.92)
            except Exception:
                pass

        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_w}x{self.screen_h}+0+0")

        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_w,
            height=self.screen_h,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.running = True
        self.num_segments = 40  # Segments per border for smooth wave/chase animation
        self.segment_lines = []

        # Build perimeter segments (Top, Right, Bottom, Left)
        # 1. Top
        seg_w = self.screen_w / self.num_segments
        for i in range(self.num_segments):
            x1 = i * seg_w
            x2 = (i + 1) * seg_w
            line = self.canvas.create_line(x1, 3, x2, 3, width=4, fill="#00f3ff")
            self.segment_lines.append(line)

        # 2. Right
        seg_h = self.screen_h / self.num_segments
        for i in range(self.num_segments):
            y1 = i * seg_h
            y2 = (i + 1) * seg_h
            line = self.canvas.create_line(self.screen_w - 3, y1, self.screen_w - 3, y2, width=4, fill="#00f3ff")
            self.segment_lines.append(line)

        # 3. Bottom
        for i in range(self.num_segments):
            x1 = self.screen_w - (i * seg_w)
            x2 = self.screen_w - ((i + 1) * seg_w)
            line = self.canvas.create_line(x1, self.screen_h - 3, x2, self.screen_h - 3, width=4, fill="#00f3ff")
            self.segment_lines.append(line)

        # 4. Left
        for i in range(self.num_segments):
            y1 = self.screen_h - (i * seg_h)
            y2 = self.screen_h - ((i + 1) * seg_h)
            line = self.canvas.create_line(3, y1, 3, y2, width=4, fill="#00f3ff")
            self.segment_lines.append(line)

        # Micro indicator
        self.badge = self.canvas.create_text(
            self.screen_w - 95, 22,
            text="● STACKY ACTIVE",
            fill="#00ff88",
            font=("Courier", 10, "bold")
        )

        threading.Thread(target=self._animate_flowing_light, daemon=True).start()

    def _animate_flowing_light(self):
        """Creates a continuous rotating laser-wave light stream around the perimeter."""
        step = 0
        total = len(self.segment_lines)
        
        # Color gradient palette: Cyan -> Electric Blue -> Emerald -> Amber -> Gold -> Purple
        colors = [
            "#00f3ff", "#00d4ff", "#00aaff", "#0077ff", "#00ffaa", 
            "#00ff88", "#ffbb00", "#ff7700", "#ff007f", "#00f3ff"
        ]

        while self.running:
            step += 1
            for idx, line in enumerate(self.segment_lines):
                # Calculate wave phase offset for every segment
                phase = (idx - step) % total
                color_idx = int((phase / total) * len(colors)) % len(colors)
                color = colors[color_idx]
                
                # Dynamic laser pulse width
                intensity = math.sin((idx * 0.1) - (step * 0.15))
                width = 3 + int(3 * ((intensity + 1) / 2))

                self.canvas.itemconfig(line, fill=color, width=width)

            time.sleep(0.03)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StackyLuminousBorder()
    app.run()
