import tkinter as tk
from PIL import Image, ImageTk
import random
import os

class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        
        # Make window transparent and always on top
        self.root.overrideredirect(True)  # Remove window border
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-transparentcolor', 'white')  # Make white transparent
        self.root.config(bg='white')
        
        # Load your sprite frames
        self.frames = []
        sprite_folder = "sprites"  # Put your PNGs in a 'sprites' folder
        
        # Load all PNG files from the sprites folder
        try:
            for filename in sorted(os.listdir(sprite_folder)):
                if filename.endswith('.png'):
                    img_path = os.path.join(sprite_folder, filename)
                    img = Image.open(img_path)
                    # Resize if needed (adjust size as needed)
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    self.frames.append(ImageTk.PhotoImage(img))
        except FileNotFoundError:
            print("Error: 'sprites' folder not found!")
            print("Please create a 'sprites' folder and add your PNG files there.")
            self.root.destroy()
            return
        
        if not self.frames:
            print("No PNG files found in sprites folder!")
            self.root.destroy()
            return
        
        # Create label to display sprite
        self.label = tk.Label(self.root, bg='white', bd=0)
        self.label.pack()
        
        # Animation variables
        self.current_frame = 0
        self.x = 100
        self.y = 100
        self.speed_x = 3
        self.speed_y = 3
        self.direction = 1  # 1 for right, -1 for left
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Start animation
        self.animate()
        self.move()
        
        # Allow dragging the pet
        self.label.bind('<Button-1>', self.start_drag)
        self.label.bind('<B1-Motion>', self.drag)
        
        # Right-click to close
        self.label.bind('<Button-3>', lambda e: self.root.destroy())
        
    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        
    def drag(self, event):
        self.x = self.root.winfo_x() + event.x - self.drag_x
        self.y = self.root.winfo_y() + event.y - self.drag_y
        self.root.geometry(f'+{self.x}+{self.y}')
        
    def animate(self):
        # Cycle through animation frames
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        frame = self.frames[self.current_frame]
        
        # Flip sprite based on direction
        if self.direction == -1:
            img = ImageTk.getimage(frame)
            flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
            frame = ImageTk.PhotoImage(flipped)
            self.label.flipped_frame = frame  # Keep reference
        
        self.label.config(image=frame)
        self.label.image = frame
        
        # Call again after delay (adjust speed: lower = faster animation)
        self.root.after(100, self.animate)
        
    def move(self):
        # Update position
        self.x += self.speed_x * self.direction
        self.y += self.speed_y
        
        # Bounce off screen edges
        if self.x <= 0 or self.x >= self.screen_width - 64:
            self.direction *= -1
            
        if self.y <= 0 or self.y >= self.screen_height - 64:
            self.speed_y *= -1
            
        # Randomly change direction sometimes
        if random.randint(1, 100) > 98:
            self.direction *= -1
            
        if random.randint(1, 100) > 98:
            self.speed_y *= -1
        
        # Update window position
        self.root.geometry(f'+{int(self.x)}+{int(self.y)}')
        
        # Call again after delay (adjust speed: lower = faster movement)
        self.root.after(30, self.move)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    pet = DesktopPet()
    pet.run()