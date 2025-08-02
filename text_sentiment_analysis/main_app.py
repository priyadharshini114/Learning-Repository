import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from gemini import get_sentiment

class analyse:
    def __init__(self, root):
        self.root = root
        self.root.title("Talk to Pooh") 
        self.root.geometry("450x550")
        self.neutral_pooh_img = Image.open("main_pic.gif").resize((400, 325), Image.Resampling.LANCZOS)
        self.neutral_pooh_photo = ImageTk.PhotoImage(self.neutral_pooh_img)
        self.happy_pooh_img = Image.open("pooh.png").resize((400, 325), Image.Resampling.LANCZOS)
        self.happy_pooh_photo = ImageTk.PhotoImage(self.happy_pooh_img)        
        self.sad_pooh_img = Image.open("sad_pooh.png").resize((400, 325), Image.Resampling.LANCZOS)
        self.sad_pooh_photo = ImageTk.PhotoImage(self.sad_pooh_img)
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12, "bold"))
        self.info_label = ttk.Label(root, text="Say something to Winnie the Pooh:", wraplength=400) 
        self.info_label.pack(pady=10)
        self.text_entry = tk.Text(root, height=3, width=50, font=("Helvetica", 11))
        self.text_entry.pack(pady=5, padx=10)
        self.talk_button = ttk.Button(root, text="Talk!", command=self.update_pooh_mood)
        self.talk_button.pack(pady=10)
        self.image_label = ttk.Label(root, image=self.neutral_pooh_photo)
        self.image_label.pack(pady=20)        
        self.root.bind('<Return>', self.on_enter_key)
    def on_enter_key(self, event):
        """Allows pressing Enter to trigger the button."""
        self.update_pooh_mood()
    def update_pooh_mood(self):
        """
        Gets text, analyzes sentiment, and updates Pooh's image.
        """
        user_input = self.text_entry.get("1.0", tk.END)
        sentiment = get_sentiment(user_input)
        print(f"Input: '{user_input.strip()}' -> Sentiment: {sentiment}")
        if sentiment == 'positive':
            self.image_label.config(image=self.happy_pooh_photo)
        else: 
            self.image_label.config(image=self.sad_pooh_photo)
if __name__ == "__main__":
    main_window = tk.Tk()
    app = analyse(main_window) 
    
    main_window.mainloop()