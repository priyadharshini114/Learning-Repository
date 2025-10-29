import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import os
from annotation_core import YOLOModel, AnnotationProcessor, list_image_files
from ultralytics import YOLO

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class AnnotationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Annotation Tool")
        self.geometry("1200x850") # Increased height slightly for new entry

        # App state
        self.image_folder = tk.StringVar()
        self.label_folder = tk.StringVar()
        self.model_path = tk.StringVar(value="") 
        self.model_conf_threshold = tk.DoubleVar(value=0.5) 
        self.model_bbox_expansion = tk.DoubleVar(value=0.20)
        self.auto_save_enabled = tk.BooleanVar(value=False) 
        self.target_class_names_str = tk.StringVar(value="") # For specific class filtering
        
        self.classes = [] 
        self.class_map = {} 

        self.yolo_model_instance = None # Renamed from self.yolo_model to avoid conflict
        self.annotation_processor = AnnotationProcessor()

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ProjectSetupPage, ClassDefinitionPage, AnnotationPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ProjectSetupPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()
        if page_name == "AnnotationPage":
            self.focus_force() 
            frame.focus_set()   


    def initialize_model(self):
        model_file_path = self.model_path.get()
        if not model_file_path:
            messagebox.showerror("Error", "Model path is not set.")
            return False

        target_class_indices = None
        user_target_names_str = self.target_class_names_str.get().strip()

        # Temporarily load model to get its class names if user specified target classes
        temp_model_for_names = None
        actual_model_names = {}
        if user_target_names_str:
            try:
                print(f"Attempting to load model '{model_file_path}' to get class names for filtering...")
                # Use a generic YOLO load just to get .names
                # This assumes YOLO() can take the path/name directly.
                # If model_file_path is a standard ultralytics name (e.g. "yolov8m.pt"), it will download.
                # If it's a local path, it will load from there.
                temp_yolo_obj = YOLO(model_file_path)
                if hasattr(temp_yolo_obj, 'names') and isinstance(temp_yolo_obj.names, dict):
                    actual_model_names = temp_yolo_obj.names
                    print(f"Model '{model_file_path}' loaded. Available classes: {actual_model_names}")
                else:
                    messagebox.showwarning("Model Info", f"Model '{model_file_path}' loaded, but class names not found or not in expected format. Class filtering might not work as intended.")
                del temp_yolo_obj # Release memory if possible
            except Exception as e:
                messagebox.showerror("Model Load Error", f"Could not load model '{model_file_path}' to get class names: {e}")
                self.yolo_model_instance = None
                return False
        
            if actual_model_names:
                target_class_indices = []
                user_names_list = [name.strip().lower() for name in user_target_names_str.split(',') if name.strip()]
                
                # Create a reverse map: name -> index
                name_to_index_map = {name.lower(): idx for idx, name in actual_model_names.items()}
                
                found_all_user_names = True
                for user_name in user_names_list:
                    if user_name in name_to_index_map:
                        target_class_indices.append(name_to_index_map[user_name])
                    else:
                        messagebox.showwarning("Class Filter Warning", f"Class name '{user_name}' not found in the loaded model's classes. It will be ignored.")
                        found_all_user_names = False
                
                if not target_class_indices and user_names_list: # User specified names but none were found
                     messagebox.showerror("Class Filter Error", "None of the specified target class names were found in the model. Aborting model initialization.")
                     self.yolo_model_instance = None
                     return False
                print(f"Filtering for class indices: {target_class_indices} (based on user names: {user_names_list})")


        # Now, initialize our YOLOModel wrapper
        try:
            print(f"Initializing YOLOModel with path: {model_file_path} and target indices: {target_class_indices}")
            self.yolo_model_instance = YOLOModel(model_file_path, target_class_indices=target_class_indices)
            self.yolo_model_instance.set_bbox_expansion(self.model_bbox_expansion.get())
            # The YOLOModel now also has .model_names exposed, which should match actual_model_names if successfully loaded
            # print(f"YOLOModel instance names: {self.yolo_model_instance.model_names}")
            messagebox.showinfo("Success", "YOLO Model initialized successfully with current settings.")
            return True
        except FileNotFoundError as e: # Should be less likely if YOLO() handles download
            messagebox.showerror("Model Error", str(e))
            self.yolo_model_instance = None
            return False
        except Exception as e:
            messagebox.showerror("Model Error", f"An unexpected error occurred initializing the YOLOModel wrapper: {e}")
            self.yolo_model_instance = None
            return False


class ProjectSetupPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Project Setup", font=("Arial", 16)).pack(pady=20)

        tk.Label(self, text="Image Folder").pack(pady=5)
        tk.Entry(self, textvariable=self.controller.image_folder, width=50).pack()
        tk.Button(self, text="Browse", command=self.browse_image_folder).pack()

        tk.Label(self, text="Label Output Folder").pack(pady=5)
        tk.Entry(self, textvariable=self.controller.label_folder, width=50).pack()
        tk.Button(self, text="Browse", command=self.browse_label_folder).pack()
        
        tk.Button(self, text="Next", command=self.next_page).pack(pady=20)

    def browse_image_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.controller.image_folder.set(folder)

    def browse_label_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.controller.label_folder.set(folder)
            
    def next_page(self):
        if not self.controller.image_folder.get() or \
           not self.controller.label_folder.get():
            messagebox.showerror("Error", "Image and Label Output folders must be selected.")
            return
        
        self.controller.show_frame("ClassDefinitionPage")


class ClassDefinitionPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.class_entries = [] 

        tk.Label(self, text="Class Definition & Model Configuration", font=("Arial", 16)).pack(pady=10)

        # --- Class Definitions ---
        class_def_frame = tk.LabelFrame(self, text="Define Annotation Classes", padx=10, pady=10)
        class_def_frame.pack(pady=5, padx=10, fill="x")
        self.classes_widget_frame = tk.Frame(class_def_frame)
        self.classes_widget_frame.pack(pady=5)
        self.add_class_entry()
        tk.Button(class_def_frame, text="Add Another Class", command=self.add_class_entry).pack(pady=5)

        # --- Model Configuration ---
        model_config_frame = tk.LabelFrame(self, text="YOLO Model Settings", padx=10, pady=10)
        model_config_frame.pack(pady=5, padx=10, fill="x")

        path_frame = tk.Frame(model_config_frame)
        path_frame.pack(fill="x", pady=2)
        tk.Label(path_frame, text="Model Path/Name (.pt):").pack(side=tk.LEFT, padx=(0,5))
        tk.Entry(path_frame, textvariable=self.controller.model_path, width=35).pack(side=tk.LEFT, expand=True, fill="x")
        tk.Button(path_frame, text="Browse", command=self.browse_model_path).pack(side=tk.LEFT, padx=(5,0))
        
        # --- Model Class Filtering ---
        filter_frame = tk.LabelFrame(model_config_frame, text="Model Class Filtering (Optional for general models)", padx=5, pady=5)
        filter_frame.pack(fill="x", pady=(5,2))
        tk.Label(filter_frame, text="Focus on specific classes (comma-separated, e.g., person,dog):").pack(anchor='w')
        tk.Entry(filter_frame, textvariable=self.controller.target_class_names_str, width=50).pack(fill="x", pady=(0,5))
        tk.Label(filter_frame, text="If empty, all model classes will be used. If a specific model is already defined (e.g., a face.pt model), you can leave this field blank.", font=("Arial", 8), wraplength=350, justify=tk.LEFT).pack(anchor='w')


        conf_frame = tk.Frame(model_config_frame)
        conf_frame.pack(fill="x", pady=2)
        tk.Label(conf_frame, text="Confidence Threshold:").pack(side=tk.LEFT, padx=(0,10))
        self.conf_scale = tk.Scale(conf_frame, from_=0.0, to=1.0, resolution=0.01,
                                   orient=tk.HORIZONTAL, variable=self.controller.model_conf_threshold,
                                   length=180, command=self._update_conf_entry_from_scale)
        self.conf_scale.pack(side=tk.LEFT, padx=5)
        self.conf_entry_var = tk.StringVar() 
        self.conf_entry = tk.Entry(conf_frame, textvariable=self.conf_entry_var, width=5)
        self.conf_entry.pack(side=tk.LEFT, padx=5)
        self.conf_entry.bind("<Return>", self._update_conf_from_entry)
        self.conf_entry.bind("<FocusOut>", self._update_conf_from_entry)
        self._update_conf_entry_from_scale() 

        bbox_exp_frame = tk.Frame(model_config_frame)
        bbox_exp_frame.pack(fill="x", pady=2)
        tk.Label(bbox_exp_frame, text="BBox Expansion Ratio:").pack(side=tk.LEFT, padx=(0,10))
        self.bbox_scale = tk.Scale(bbox_exp_frame, from_=0.0, to=1.0, resolution=0.01,
                                    orient=tk.HORIZONTAL, variable=self.controller.model_bbox_expansion,
                                    length=180, command=self._update_bbox_label_from_scale)
        self.bbox_scale.pack(side=tk.LEFT, padx=5)
        self.bbox_value_label = tk.Label(bbox_exp_frame, text="0.00") 
        self.bbox_value_label.pack(side=tk.LEFT, padx=5)
        self._update_bbox_label_from_scale() 

        nav_button_frame = tk.Frame(self)
        nav_button_frame.pack(pady=15, fill="x")
        tk.Button(nav_button_frame, text="Back", command=lambda: controller.show_frame("ProjectSetupPage")).pack(side=tk.LEFT, padx=20, expand=True)
        tk.Button(nav_button_frame, text="Start Annotating", command=self.done_and_start_annotating).pack(side=tk.RIGHT, padx=20, expand=True)

    def _update_conf_entry_from_scale(self, event=None):
        value = self.controller.model_conf_threshold.get()
        self.conf_entry_var.set(f"{value:.2f}")

    def _update_conf_from_entry(self, event=None):
        try:
            value_str = self.conf_entry_var.get()
            value = float(value_str)
            if 0.0 <= value <= 1.0:
                self.controller.model_conf_threshold.set(value) 
            else:
                messagebox.showerror("Invalid Input", "Confidence threshold must be between 0.0 and 1.0.")
                self._update_conf_entry_from_scale() 
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for confidence threshold.")
            self._update_conf_entry_from_scale() 

    def _update_bbox_label_from_scale(self, event=None):
        value = self.controller.model_bbox_expansion.get()
        self.bbox_value_label.config(text=f"{value:.2f}")

    def on_show(self):
        for widget in self.classes_widget_frame.winfo_children():
            widget.destroy()
        self.class_entries = []
        
        if not self.controller.classes: 
            self.add_class_entry()
        else: 
            for i, class_name in enumerate(self.controller.classes):
                self.add_class_entry(class_name, i)
        
        self._update_conf_entry_from_scale() 
        self.bbox_scale.set(self.controller.model_bbox_expansion.get()) 
        self._update_bbox_label_from_scale()
        self.controller.focus_force() 

    def add_class_entry(self, name="", index=None):
        if index is None:
            index = len(self.class_entries)

        entry_frame = tk.Frame(self.classes_widget_frame)
        entry_frame.pack(fill="x", pady=2)

        label = tk.Label(entry_frame, text=f"Class {index}:")
        label.pack(side=tk.LEFT, padx=5)
        
        entry = tk.Entry(entry_frame, width=30)
        entry.insert(0, name)
        entry.pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        self.class_entries.append(entry)
        
        remove_btn = tk.Button(entry_frame, text="X", command=lambda e=entry: self.remove_class_entry(e), relief=tk.GROOVE, width=2)
        remove_btn.pack(side=tk.LEFT, padx=5)

    def remove_class_entry(self, entry_to_remove):
        if len(self.class_entries) <= 1 and entry_to_remove == self.class_entries[0]:
            messagebox.showinfo("Info", "At least one class entry is required.")
            return

        found_index = -1
        for i, entry in enumerate(self.class_entries):
            if entry == entry_to_remove:
                found_index = i
                break
        if found_index != -1:
            self.class_entries.pop(found_index).master.destroy() 
            for i, entry_widget in enumerate(self.class_entries):
                label_widget = entry_widget.master.winfo_children()[0]
                if isinstance(label_widget, tk.Label):
                    label_widget.config(text=f"Class {i}:")

    def browse_model_path(self):
        filepath = filedialog.askopenfilename(
            title="Select YOLO Model",
            filetypes=(("PyTorch Model", "*.pt"), ("All files", "*.*"))
        )
        if filepath:
            self.controller.model_path.set(filepath)

    def done_and_start_annotating(self):
        self._update_conf_from_entry() 

        self.controller.classes = [entry.get().strip().lower() for entry in self.class_entries if entry.get().strip()]
        if not self.controller.classes:
            messagebox.showerror("Error", "Please define at least one class.")
            return
        if len(self.controller.classes) != len(set(self.controller.classes)): 
            messagebox.showerror("Error", "Class names must be unique.")
            return
        self.controller.class_map = {name: i for i, name in enumerate(self.controller.classes)}
        
        print("Defined classes (lowercase):", self.controller.classes)
        print("Class map:", self.controller.class_map)
        print(f"Model Path/Name: {self.controller.model_path.get()}")
        print(f"Target Class Names Str: {self.controller.target_class_names_str.get()}")
        print(f"Confidence Threshold: {self.controller.model_conf_threshold.get()}") 
        print(f"BBox Expansion: {self.controller.model_bbox_expansion.get()}")

        if not self.controller.model_path.get():
            messagebox.showerror("Error", "YOLO Model path/name must be provided.")
            return
        
        if not self.controller.initialize_model(): # This now handles target class parsing
            return 

        self.controller.show_frame("AnnotationPage")


class AnnotationPage(tk.Frame):
    MAX_CANVAS_WIDTH = 800
    MAX_CANVAS_HEIGHT = 600
    HANDLE_SIZE = 8 
    MIN_ZOOM = 0.1 
    MAX_ZOOM = 10.0
    CLASS_BUTTON_AREA_MAX_HEIGHT = 150

    CLASS_COLORS = [
        "red", "green", "cyan", "magenta", "orange", 
        "purple", "brown", "pink", "DarkOliveGreen", "SlateBlue",
        "DarkGoldenrod", "LightSeaGreen", "IndianRed", "SteelBlue", "MediumVioletRed"
    ]
    DEFAULT_BOX_COLOR = "blue"
    SELECTED_BOX_COLOR = "yellow"


    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.info_label = tk.Label(self, text="Image: N/A", justify=tk.LEFT, anchor='w')
        self.info_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(5,0))

        main_content_frame = tk.Frame(self)
        main_content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_content_frame, bg="lightgray", width=self.MAX_CANVAS_WIDTH, height=self.MAX_CANVAS_HEIGHT)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.controls_panel = tk.Frame(main_content_frame, width=250)
        self.controls_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.controls_panel.pack_propagate(False) 

        tk.Label(self.controls_panel, text="Navigation Controls", font=("Arial", 12, "bold")).pack(pady=(10, 2), fill=tk.X, anchor='w')
        nav_frame = tk.Frame(self.controls_panel)
        nav_frame.pack(pady=10, fill=tk.X)
        tk.Button(nav_frame, text="Previous Image (A)", command=self.prev_image).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(nav_frame, text="Next Image (D)", command=self.next_image).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        tk.Label(self.controls_panel, text="Zoom Controls", font=("Arial", 12, "bold")).pack(pady=(10, 2), fill=tk.X, anchor='w')
        zoom_frame = tk.Frame(self.controls_panel)
        zoom_frame.pack(pady=5, fill=tk.X)
        tk.Button(zoom_frame, text="Zoom In (+)", command=self.zoom_in_button).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(zoom_frame, text="Zoom Out (-)", command=self.zoom_out_button).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.controls_panel, text="Reset View", command=self.reset_view).pack(pady=(0,10), fill=tk.X)
        
        tk.Label(self.controls_panel, text="Annotation Tool Box", font=("Arial", 12, "bold")).pack(pady=(10, 2), fill=tk.X, anchor='w')
        
        save_controls_frame = tk.Frame(self.controls_panel)
        save_controls_frame.pack(pady=5, fill=tk.X)
        tk.Button(save_controls_frame, text="Save (Ctrl+S)", command=self.save_annotations).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Checkbutton(save_controls_frame, text="Auto-Save", variable=self.controller.auto_save_enabled).pack(side=tk.LEFT, padx=(5,0))

        tk.Button(self.controls_panel, text="detect (W)", command=self.re_detect_objects).pack(pady=5, fill=tk.X)
        tk.Button(self.controls_panel, text="Delete Selected Box", command=self.delete_selected_box).pack(pady=5, fill=tk.X)
        tk.Button(self.controls_panel, text="Delete All Boxes", command=self.delete_all_boxes).pack(pady=5, fill=tk.X)

        tk.Label(self.controls_panel, text="Assign Class", font=("Arial", 12,"bold")).pack(pady=(15,0),fill=tk.X)
        class_button_container = tk.Frame(self.controls_panel, height=self.CLASS_BUTTON_AREA_MAX_HEIGHT)
        class_button_container.pack(pady=5, fill=tk.X, expand=False) 
        class_button_container.pack_propagate(False) 

        self.class_canvas = tk.Canvas(class_button_container, borderwidth=0, background="#ffffff")
        self.class_buttons_frame = tk.Frame(self.class_canvas, background="#ffffff") 
        self.class_scrollbar = ttk.Scrollbar(class_button_container, orient="vertical", command=self.class_canvas.yview)
        self.class_canvas.configure(yscrollcommand=self.class_scrollbar.set)
        self.class_scrollbar.pack(side="right", fill="y")
        self.class_canvas.pack(side="left", fill="both", expand=True)
        self.class_canvas_window = self.class_canvas.create_window((0, 0), window=self.class_buttons_frame, anchor="nw")
        self.class_buttons_frame.bind("<Configure>", self._on_class_buttons_frame_configure)
        self.class_canvas.bind('<Enter>', self._bind_mousewheel_to_class_canvas)
        self.class_canvas.bind('<Leave>', self._unbind_mousewheel_from_class_canvas)
        
        self.image_files_info = [] 
        self.current_image_index = -1
        self.current_image_info = None 
        self.current_image_path = None
        self.current_image_cv2 = None
        self.tk_image = None 
        
        self.image_canvas_origin_x = 0.0
        self.image_canvas_origin_y = 0.0
        self.effective_scale_factor = 1.0 
        self.zoom_step_factor = 1.2       

        self._pan_active = False
        self._pan_last_mouse_x = 0
        self._pan_last_mouse_y = 0

        self.annotations = [] 
        self.selected_box_idx = None
        
        self.rect_start_canvas_x = None
        self.rect_start_canvas_y = None
        self.current_rect_item = None 

        self.dragging_handle_info = None 
        self.dragging_box_info = None 

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel) 
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)   
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)   

        self.canvas.bind("<ButtonPress-2>", self._on_pan_press)
        self.canvas.bind("<B2-Motion>", self._on_pan_motion)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_release)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press) 
        self.canvas.bind("<B3-Motion>", self._on_pan_motion)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_release)

        self.bind("<KeyPress>", self._handle_keypress) 
        self.bind("<Control-KeyPress-s>", lambda e: self.save_annotations(event=e)) 
        self.bind("<Control-KeyPress-S>", lambda e: self.save_annotations(event=e)) 


    def _handle_keypress(self, event):
        focused_widget = self.focus_get()
        if isinstance(focused_widget, tk.Entry):
            if not (event.keysym.lower() == 's' and (event.state & 4)):
                 return 
        
        key = event.keysym.lower()
        
        if key == 'a':
            self.prev_image(event)
        elif key == 'd':
            self.next_image(event)
        elif key == 'w':
            self.re_detect_objects(event)
        elif key == 'delete' or key == 'backspace':
            if focused_widget == self.canvas or not isinstance(focused_widget, tk.Entry):
                self.delete_selected_box(event)

    def _on_class_buttons_frame_configure(self, event=None):
        self.class_canvas.configure(scrollregion=self.class_canvas.bbox("all"))
        self.class_canvas.itemconfig(self.class_canvas_window, width=self.class_canvas.winfo_width())

    def _on_class_canvas_mousewheel(self, event):
        if event.num == 4 or event.delta > 0: 
            self.class_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0: 
            self.class_canvas.yview_scroll(1, "units")

    def _bind_mousewheel_to_class_canvas(self, event):
        self.class_canvas.bind_all("<MouseWheel>", self._on_class_canvas_mousewheel)
        self.class_canvas.bind_all("<Button-4>", self._on_class_canvas_mousewheel)
        self.class_canvas.bind_all("<Button-5>", self._on_class_canvas_mousewheel)

    def _unbind_mousewheel_from_class_canvas(self, event):
        self.class_canvas.unbind_all("<MouseWheel>")
        self.class_canvas.unbind_all("<Button-4>")
        self.class_canvas.unbind_all("<Button-5>")
        
    def _trigger_auto_save(self):
        """Helper function to save annotations if auto-save is enabled."""
        if self.controller.auto_save_enabled.get() and self.current_image_cv2 is not None:
            self.save_annotations(is_auto_save=True)

    def on_show(self):
        if not self.controller.yolo_model_instance: # Check instance name
            messagebox.showerror("Error", "YOLO Model not initialized. Please set up model in previous step.")
            self.controller.show_frame("ClassDefinitionPage")
            return

        self.image_files_info = list_image_files(self.controller.image_folder.get())
        if not self.image_files_info:
            messagebox.showinfo("Info", "No images found in the selected folder or its subfolders.")
            self.current_image_index = -1
            self.clear_canvas_and_state()
            self.update_info_label()
        else:
            self.current_image_index = 0
            self.load_image_and_process_annotations() 
        
        self.update_class_buttons()
        self.after(100, self._on_class_buttons_frame_configure)
        self.focus_set() 

    def clear_canvas_and_state(self):
        self.canvas.delete("all") 
        self.tk_image = None 
        self.annotations = []
        self.selected_box_idx = None
        self.current_image_path = None
        self.current_image_cv2 = None
        self.current_image_info = None
        self.dragging_handle_info = None
        self.dragging_box_info = None
        self.rect_start_canvas_x = None 
        if self.current_rect_item:
            self.canvas.delete(self.current_rect_item)
            self.current_rect_item = None
        self.image_canvas_origin_x = 0.0
        self.image_canvas_origin_y = 0.0
        self.effective_scale_factor = 1.0

    def load_image_and_process_annotations(self):
        if not (0 <= self.current_image_index < len(self.image_files_info)):
            self.clear_canvas_and_state()
            self.update_info_label("No image loaded or index out of bounds.")
            return

        self.current_image_info = self.image_files_info[self.current_image_index]
        self.current_image_path = self.current_image_info['path']
        try:
            self.current_image_cv2 = cv2.imread(self.current_image_path)
            if self.current_image_cv2 is None:
                raise IOError(f"cv2.imread returned None for: {self.current_image_path}. Image might be corrupted or format not supported by OpenCV.")
        except Exception as e:
            messagebox.showerror("Image Load Error", str(e))
            self.clear_canvas_and_state()
            self.update_info_label(f"Error loading: {os.path.basename(self.current_image_path)}")
            return

        self.annotations = []
        self.selected_box_idx = None
        self.dragging_handle_info = None 
        self.dragging_box_info = None

        self.reset_view() 

        img_h, img_w = self.current_image_cv2.shape[:2]
        base, _ = os.path.splitext(os.path.basename(self.current_image_path))
        label_file_name = base + ".txt"
        label_file = os.path.join(self.controller.label_folder.get(), label_file_name)

        if os.path.exists(label_file):
            # --- MODIFIED LOGIC ---
            # Label file exists, it is the source of truth.
            loaded_anns_from_file = self.controller.annotation_processor.load_yolo_labels(label_file, img_w, img_h)

            for ann_from_file in loaded_anns_from_file:
                class_id_from_file = ann_from_file['class_id']
                
                # Check if the class ID from the file is valid under current GUI class definitions
                is_id_from_file_valid = False
                if class_id_from_file is not None:
                    is_id_from_file_valid = any(
                        gui_id == class_id_from_file for gui_id in self.controller.class_map.values()
                    )
                else: # None is valid (unclassified)
                    is_id_from_file_valid = True

                final_class_id_for_ann = class_id_from_file
                if not is_id_from_file_valid and class_id_from_file is not None:
                    # The ID from the file is no longer valid. Mark as unclassified and warn user.
                    print(f"Warning: Image '{os.path.basename(self.current_image_path)}' - "
                          f"Loaded Class ID {class_id_from_file} from its label file is not valid "
                          f"with the current class definitions. Marking this annotation as unclassified.")
                    final_class_id_for_ann = None

                self.annotations.append({
                    'bbox_pixels': ann_from_file['bbox_pixels'],
                    'class_id': final_class_id_for_ann,
                    'canvas_item': None, 'label_item': None, 'handles': {}
                })
        else:
            # No existing label file, perform auto-detection and folder-based labeling
            self.perform_auto_detection_and_labeling()  
        
        self.redraw_all_annotations_on_canvas() 
        self.update_info_label()

        # Proactively auto-save after loading, if enabled.
        self._trigger_auto_save()


    def reset_view(self, event=None): 
        if self.current_image_cv2 is None:
            self.display_image_on_canvas() 
            self.redraw_all_annotations_on_canvas()
            return

        img_h, img_w = self.current_image_cv2.shape[:2]
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1: 
            canvas_w = self.MAX_CANVAS_WIDTH
            canvas_h = self.MAX_CANVAS_HEIGHT

        scale_w = canvas_w / img_w if img_w > 0 else 1.0
        scale_h = canvas_h / img_h if img_h > 0 else 1.0
        fit_scale = min(scale_w, scale_h)
        fit_scale = min(fit_scale, 1.0) 

        self.effective_scale_factor = fit_scale 

        disp_w_eff = img_w * self.effective_scale_factor
        disp_h_eff = img_h * self.effective_scale_factor
        self.image_canvas_origin_x = (canvas_w - disp_w_eff) / 2.0
        self.image_canvas_origin_y = (canvas_h - disp_h_eff) / 2.0
        
        self.display_image_on_canvas() 
        self.redraw_all_annotations_on_canvas()

    def display_image_on_canvas(self):
        self.canvas.delete("bg_image") 
        self.tk_image = None 

        if self.current_image_cv2 is None: return

        img_h, img_w = self.current_image_cv2.shape[:2]
        
        disp_w_eff = int(img_w * self.effective_scale_factor)
        disp_h_eff = int(img_h * self.effective_scale_factor)

        if disp_w_eff <= 0 or disp_h_eff <= 0:
             return

        try:
            resized_img = cv2.resize(self.current_image_cv2, (disp_w_eff, disp_h_eff), interpolation=cv2.INTER_AREA)
            img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            self.tk_image = ImageTk.PhotoImage(image=img_pil)
            
            self.canvas.create_image(int(round(self.image_canvas_origin_x)), int(round(self.image_canvas_origin_y)), 
                                     anchor=tk.NW, image=self.tk_image, tags="bg_image")
        except Exception as e:
            print(f"Error displaying image: {e}")
            self.tk_image = None 

        self.canvas.lift("box_group") 
        self.canvas.lift("label_group")
        self.canvas.lift("handle_group")
        self.canvas.lift("new_box_drawing_temp")


    def perform_auto_detection_and_labeling(self):
        if self.current_image_cv2 is None or self.controller.yolo_model_instance is None or self.current_image_info is None:
            return
        
        conf_thresh = self.controller.model_conf_threshold.get()
        # Use yolo_model_instance
        detected_pixel_boxes = self.controller.yolo_model_instance.detect(self.current_image_cv2, conf_threshold=conf_thresh)
        
        auto_class_id = None
        # If model is filtered, auto-assignment by folder name might be less relevant
        # unless the folder name matches one of the *filtered* classes.
        # For now, the user-defined classes take precedence for manual annotation.
        # Auto-assignment from folder still happens if a match is found in user-defined classes.
        parent_folder_name = self.current_image_info.get('parent_folder_name')
        if parent_folder_name: 
            auto_class_id = self.controller.class_map.get(parent_folder_name.lower())

        for bbox_pixels in detected_pixel_boxes:
            self.annotations.append({
                'bbox_pixels': bbox_pixels,
                'class_id': auto_class_id, # This might be None if folder doesn't match a GUI-defined class
                'canvas_item': None,
                'label_item': None,
                'handles': {} 
            })

    def redraw_all_annotations_on_canvas(self):
        self.canvas.delete("box_group")
        self.canvas.delete("label_group")
        self.canvas.delete("handle_group")
        
        for ann in self.annotations:
            ann['canvas_item'] = None
            ann['label_item'] = None
            ann['handles'] = {} 

        for idx, ann_data in enumerate(self.annotations):
            self.draw_single_annotation_on_canvas(ann_data, idx, is_selected=(idx == self.selected_box_idx))

    def draw_single_annotation_on_canvas(self, annotation_data, annotation_index, is_selected=False):
        x1_orig, y1_orig, x2_orig, y2_orig = annotation_data['bbox_pixels']
        
        cv_x1, cv_y1 = self._img_coords_to_canvas_coords(x1_orig, y1_orig)
        cv_x2, cv_y2 = self._img_coords_to_canvas_coords(x2_orig, y2_orig)

        class_id = annotation_data.get('class_id')
        
        if class_id is not None:
            color_index = class_id % len(self.CLASS_COLORS)
            assigned_color = self.CLASS_COLORS[color_index]
            box_color = assigned_color
            text_color = assigned_color
        else:
            box_color = self.DEFAULT_BOX_COLOR
            text_color = self.DEFAULT_BOX_COLOR
            
        if is_selected:
            box_color = self.SELECTED_BOX_COLOR
            text_color = self.SELECTED_BOX_COLOR
        
        if annotation_data.get('canvas_item'): self.canvas.delete(annotation_data['canvas_item'])
        if annotation_data.get('label_item'): self.canvas.delete(annotation_data['label_item'])
        for handle_id in annotation_data.get('handles', {}).values(): self.canvas.delete(handle_id)
        annotation_data['handles'] = {}

        box_id = self.canvas.create_rectangle(cv_x1, cv_y1, cv_x2, cv_y2, outline=box_color, width=2, 
                                              tags=("box_group", f"box_{annotation_index}"))
        annotation_data['canvas_item'] = box_id
        
        label_text = ""
        class_id_from_data = annotation_data.get('class_id')
        if class_id_from_data is not None:
            class_name_display = "Unknown"
            for c_name, c_id_map in self.controller.class_map.items():
                if c_id_map == class_id_from_data:
                    class_name_display = c_name.capitalize()
                    break
            label_text = class_name_display
        
        label_id = self.canvas.create_text(cv_x1, cv_y1 - 5, text=label_text, anchor=tk.SW, 
                                           fill=text_color, font=("Arial", 10, "bold"),
                                           tags=("label_group", f"label_{annotation_index}"))
        annotation_data['label_item'] = label_id

        if is_selected:
            hs = self.HANDLE_SIZE // 2
            handle_positions = {
                'tl': (cv_x1, cv_y1), 'tr': (cv_x2, cv_y1),
                'bl': (cv_x1, cv_y2), 'br': (cv_x2, cv_y2)
            }
            for handle_type, (hx, hy) in handle_positions.items():
                handle_canvas_id = self.canvas.create_oval(hx - hs, hy - hs, hx + hs, hy + hs, 
                                                          fill="white", outline="black", width=1,
                                                          tags=("handle_group", f"handle_{annotation_index}_{handle_type}"))
                annotation_data['handles'][handle_type] = handle_canvas_id
    
    def _img_coords_to_canvas_coords(self, img_x, img_y):
        canvas_x = int(round(img_x * self.effective_scale_factor + self.image_canvas_origin_x))
        canvas_y = int(round(img_y * self.effective_scale_factor + self.image_canvas_origin_y))
        return canvas_x, canvas_y

    def _canvas_coords_to_img_coords(self, canvas_x, canvas_y):
        if self.current_image_cv2 is None or self.effective_scale_factor == 0:
            return 0, 0

        img_x_float = (float(canvas_x) - self.image_canvas_origin_x) / self.effective_scale_factor
        img_y_float = (float(canvas_y) - self.image_canvas_origin_y) / self.effective_scale_factor
        
        img_h, img_w = self.current_image_cv2.shape[:2]
        max_img_x = float(img_w -1) if img_w > 0 else 0.0
        max_img_y = float(img_h -1) if img_h > 0 else 0.0
        
        img_x_clamped = max(0.0, min(img_x_float, max_img_x))
        img_y_clamped = max(0.0, min(img_y_float, max_img_y))
        
        return int(round(img_x_clamped)), int(round(img_y_clamped))


    def on_canvas_press(self, event):
        self.rect_start_canvas_x = event.x 
        self.rect_start_canvas_y = event.y
        self.dragging_handle_info = None
        self.dragging_box_info = None 

        if self.selected_box_idx is not None:
            selected_annotation = self.annotations[self.selected_box_idx]
            for handle_type, handle_id in selected_annotation.get('handles', {}).items():
                hx1, hy1, hx2, hy2 = self.canvas.coords(handle_id)
                if hx1 <= event.x <= hx2 and hy1 <= event.y <= hy2:
                    self.dragging_handle_info = {
                        'box_idx': self.selected_box_idx,
                        'handle_type': handle_type,
                        'orig_bbox_pixels': list(selected_annotation['bbox_pixels']) 
                    }
                    self.canvas.config(cursor="crosshair")
                    return 

        clicked_box_idx = None
        for idx in range(len(self.annotations) - 1, -1, -1): 
            ann = self.annotations[idx]
            cv_x1_b, cv_y1_b, cv_x2_b, cv_y2_b = 0,0,0,0
            if ann.get('canvas_item'):
                try:
                    coords = self.canvas.coords(ann['canvas_item'])
                    if len(coords) == 4:
                        cv_x1_b, cv_y1_b, cv_x2_b, cv_y2_b = min(coords[0],coords[2]), min(coords[1],coords[3]), \
                                                             max(coords[0],coords[2]), max(coords[1],coords[3])
                        if cv_x1_b <= event.x <= cv_x2_b and cv_y1_b <= event.y <= cv_y2_b:
                            clicked_box_idx = idx
                            break
                        continue 
                except tk.TclError: pass
            else:
                cv_x1_calc, cv_y1_calc = self._img_coords_to_canvas_coords(*ann['bbox_pixels'][:2])
                cv_x2_calc, cv_y2_calc = self._img_coords_to_canvas_coords(*ann['bbox_pixels'][2:])
                if min(cv_x1_calc, cv_x2_calc) <= event.x <= max(cv_x1_calc, cv_x2_calc) and \
                   min(cv_y1_calc, cv_y2_calc) <= event.y <= max(cv_y1_calc, cv_y2_calc):
                    clicked_box_idx = idx
                    break
        
        if clicked_box_idx is not None:
            if self.selected_box_idx != clicked_box_idx: 
                self.selected_box_idx = clicked_box_idx
                self.redraw_all_annotations_on_canvas() 
            img_mouse_x, img_mouse_y = self._canvas_coords_to_img_coords(event.x, event.y)
            box_pixels = self.annotations[self.selected_box_idx]['bbox_pixels']
            self.dragging_box_info = {
                'box_idx': self.selected_box_idx,
                'offset_x': img_mouse_x - box_pixels[0],
                'offset_y': img_mouse_y - box_pixels[1],
                'box_width': box_pixels[2] - box_pixels[0],
                'box_height': box_pixels[3] - box_pixels[1]
            }
            self.canvas.config(cursor="fleur")
            self.rect_start_canvas_x = None 
            return

        if self.selected_box_idx is not None:
            self.selected_box_idx = None
            self.redraw_all_annotations_on_canvas() 
        
        if self.current_image_cv2 is not None and self.rect_start_canvas_x is not None: 
            if self.effective_scale_factor > 0:
                self.current_rect_item = self.canvas.create_rectangle(
                    self.rect_start_canvas_x, self.rect_start_canvas_y, 
                    self.rect_start_canvas_x, self.rect_start_canvas_y, 
                    outline="cyan", width=2, tags="new_box_drawing_temp"
                )
                self.canvas.config(cursor="crosshair")


    def on_canvas_drag(self, event):
        current_canvas_x, current_canvas_y = event.x, event.y

        if self.dragging_handle_info:
            box_idx = self.dragging_handle_info['box_idx']
            handle_type = self.dragging_handle_info['handle_type']
            annotation_data = self.annotations[box_idx]
            current_bbox_pixels = list(annotation_data['bbox_pixels']) 
            img_mouse_x, img_mouse_y = self._canvas_coords_to_img_coords(current_canvas_x, current_canvas_y)

            if handle_type == 'tl':
                current_bbox_pixels[0] = img_mouse_x
                current_bbox_pixels[1] = img_mouse_y
            elif handle_type == 'tr':
                current_bbox_pixels[2] = img_mouse_x
                current_bbox_pixels[1] = img_mouse_y
            elif handle_type == 'bl':
                current_bbox_pixels[0] = img_mouse_x
                current_bbox_pixels[3] = img_mouse_y
            elif handle_type == 'br':
                current_bbox_pixels[2] = img_mouse_x
                current_bbox_pixels[3] = img_mouse_y
            
            annotation_data['bbox_pixels'] = current_bbox_pixels 
            self.draw_single_annotation_on_canvas(annotation_data, box_idx, is_selected=True)

        elif self.dragging_box_info:
            box_idx = self.dragging_box_info['box_idx']
            annotation_data = self.annotations[box_idx]
            img_mouse_x, img_mouse_y = self._canvas_coords_to_img_coords(current_canvas_x, current_canvas_y)
            
            new_x1 = img_mouse_x - self.dragging_box_info['offset_x']
            new_y1 = img_mouse_y - self.dragging_box_info['offset_y']

            img_h, img_w = self.current_image_cv2.shape[:2]
            box_width = self.dragging_box_info['box_width']
            box_height = self.dragging_box_info['box_height']

            new_x1 = max(0, min(new_x1, img_w - box_width))
            new_y1 = max(0, min(new_y1, img_h - box_height))
            
            new_x2 = new_x1 + box_width
            new_y2 = new_y1 + box_height
            
            annotation_data['bbox_pixels'] = [new_x1, new_y1, new_x2, new_y2]
            self.draw_single_annotation_on_canvas(annotation_data, box_idx, is_selected=True)

        elif self.current_rect_item and self.rect_start_canvas_x is not None: 
            self.canvas.coords(self.current_rect_item, self.rect_start_canvas_x, self.rect_start_canvas_y, 
                               current_canvas_x, current_canvas_y)


    def on_canvas_release(self, event):
        self.canvas.config(cursor="") 

        if self.dragging_handle_info:
            box_idx = self.dragging_handle_info['box_idx']
            annotation_data = self.annotations[box_idx]
            x1, y1, x2, y2 = annotation_data['bbox_pixels']
            annotation_data['bbox_pixels'] = [min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2)]
            self.dragging_handle_info = None
            self.redraw_all_annotations_on_canvas() 
        
        elif self.dragging_box_info:
            self.dragging_box_info = None
            self.redraw_all_annotations_on_canvas()

        elif self.current_rect_item and self.rect_start_canvas_x is not None: 
            end_canvas_x, end_canvas_y = event.x, event.y
            self.canvas.delete(self.current_rect_item) 
            self.current_rect_item = None

            img_x1, img_y1 = self._canvas_coords_to_img_coords(self.rect_start_canvas_x, self.rect_start_canvas_y)
            img_x2, img_y2 = self._canvas_coords_to_img_coords(end_canvas_x, end_canvas_y)

            final_x1 = min(img_x1, img_x2)
            final_y1 = min(img_y1, img_y2)
            final_x2 = max(img_x1, img_x2)
            final_y2 = max(img_y1, img_y2)
            
            if (final_x2 - final_x1) > 5 and (final_y2 - final_y1) > 5 :
                new_ann = {'bbox_pixels': [final_x1, final_y1, final_x2, final_y2], 
                           'class_id': None, 'canvas_item': None, 'label_item': None, 'handles': {}}
                self.annotations.append(new_ann)
                self.selected_box_idx = len(self.annotations) - 1 
                self.redraw_all_annotations_on_canvas()
            
        self.rect_start_canvas_x = None 
        self.rect_start_canvas_y = None
        
        # Trigger auto-save after any box creation/modification
        self._trigger_auto_save()


    def assign_class(self, class_id, class_name): 
        if self.selected_box_idx is not None and 0 <= self.selected_box_idx < len(self.annotations):
            self.annotations[self.selected_box_idx]['class_id'] = class_id
            self.redraw_all_annotations_on_canvas() 
            print(f"Assigned class '{class_name}' (ID: {class_id}) to box {self.selected_box_idx}")
            self._trigger_auto_save()
        else:
            messagebox.showinfo("Info", "Select a bounding box first to assign a class.")
            
    def delete_selected_box(self, event=None):
        if self.selected_box_idx is not None and 0 <= self.selected_box_idx < len(self.annotations):
            self.annotations.pop(self.selected_box_idx)
            self.selected_box_idx = None
            self.dragging_handle_info = None 
            self.dragging_box_info = None
            self.redraw_all_annotations_on_canvas() 
            print("Deleted selected box.")
            self._trigger_auto_save()
        else:
            if event is None:
                messagebox.showinfo("Info", "No bounding box selected to delete.")
            else: 
                print("No bounding box selected to delete.")
            
    def delete_all_boxes(self):
        if not self.annotations:
            messagebox.showinfo("Info", "No boxes to delete.")
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to delete ALL boxes for this image?"):
            self.annotations = []
            self.selected_box_idx = None
            self.dragging_handle_info = None
            self.dragging_box_info = None
            self.redraw_all_annotations_on_canvas()
            print("Deleted all boxes for the current image.")
            self._trigger_auto_save()

    def save_annotations(self, is_auto_save=False, event=None):
        if self.current_image_cv2 is None or not self.current_image_path:
            if not is_auto_save:
                messagebox.showerror("Error", "No image loaded to save annotations for.")
            else:
                print("Auto-save: No image loaded, skipping save.")
            return
        
        img_h, img_w = self.current_image_cv2.shape[:2]
        base, _ = os.path.splitext(os.path.basename(self.current_image_path))
        label_file = os.path.join(self.controller.label_folder.get(), base + ".txt")
        
        annotations_to_save = [ann for ann in self.annotations if ann.get('class_id') is not None]

        if is_auto_save:
            if annotations_to_save: 
                self.controller.annotation_processor.save_yolo_labels(label_file, annotations_to_save, img_w, img_h)
                print(f"Auto-saved: Annotations for {base} to {label_file}")
            elif self.annotations and os.path.exists(label_file): 
                self.controller.annotation_processor.save_yolo_labels(label_file, [], img_w, img_h)
                print(f"Auto-saved: Empty annotation file for {base} (cleared classifications/unclassified boxes).")
            elif not self.annotations and os.path.exists(label_file):
                self.controller.annotation_processor.save_yolo_labels(label_file, [], img_w, img_h)
                print(f"Auto-saved: Empty annotation file for {base} (all boxes deleted).")
            elif not annotations_to_save and not os.path.exists(label_file):
                 print(f"Auto-save: No classified annotations for new file {base}, nothing to save.")
            else: 
                # This case avoids spamming logs when no changes are made.
                pass

        else: # Manual Save
            if not annotations_to_save and os.path.exists(label_file):
                if messagebox.askyesno("Empty Classified Annotations", 
                                       f"No classified bounding boxes to save for {base}. "
                                       f"Do you want to save an empty annotation file (this will overwrite existing and remove any unclassified boxes)?"):
                    self.controller.annotation_processor.save_yolo_labels(label_file, [], img_w, img_h)
                    messagebox.showinfo("Success", f"Empty annotation file saved for {base}")
                else:
                    messagebox.showinfo("Info", f"Annotation saving for {base} cancelled by user.")
            elif annotations_to_save:
                 self.controller.annotation_processor.save_yolo_labels(label_file, annotations_to_save, img_w, img_h)
                 messagebox.showinfo("Success", f"Annotations saved to {label_file}")
            elif not annotations_to_save and not self.annotations: 
                 messagebox.showinfo("Info", f"No annotations (classified or unclassified) to save for {base}.")
            else: 
                 messagebox.showinfo("Info", f"No classified annotations to save for {base}. Please classify boxes first or use Auto-Save to clear if needed.")


    def next_image(self, event=None):
        if self.controller.auto_save_enabled.get() and self.current_image_cv2 is not None:
            print(f"Auto-saving (next): {os.path.basename(self.current_image_path) if self.current_image_path else 'current image'}")
            self.save_annotations(is_auto_save=True)

        if self.current_image_index < len(self.image_files_info) - 1:
            self.current_image_index += 1
            self.load_image_and_process_annotations()
        else:
            messagebox.showinfo("Info", "This is the last image.")

    def prev_image(self, event=None):
        if self.controller.auto_save_enabled.get() and self.current_image_cv2 is not None:
            print(f"Auto-saving (prev): {os.path.basename(self.current_image_path) if self.current_image_path else 'current image'}")
            self.save_annotations(is_auto_save=True)

        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_image_and_process_annotations()
        else:
            messagebox.showinfo("Info", "This is the first image.")

    def update_class_buttons(self):
        for widget in self.class_buttons_frame.winfo_children():
            widget.destroy()
        
        if not self.controller.class_map:
             tk.Label(self.class_buttons_frame, text="No classes defined.", background="#ffffff").pack(pady=5)
        else:
            for class_name, class_id in self.controller.class_map.items():
                btn_text = f"{class_name.capitalize()} ({class_id})"
                btn = tk.Button(self.class_buttons_frame, text=btn_text, 
                                command=lambda cid=class_id, cname_debug=class_name: self.assign_class(cid, cname_debug))
                btn.pack(fill=tk.X, pady=2, padx=2)
        
        self.class_buttons_frame.update_idletasks()
        self._on_class_buttons_frame_configure()


    def update_info_label(self, custom_message=None):
        if custom_message:
            self.info_label.config(text=custom_message)
            return

        if self.current_image_path:
            img_name = os.path.basename(self.current_image_path)
            text = f"Image: {img_name}  ({self.current_image_index + 1}/{len(self.image_files_info)})"
            zoom_percentage = self.effective_scale_factor * 100 
            text += f"    Zoom: {zoom_percentage:.0f}%"

            self.info_label.config(text=text)
        else:
            self.info_label.config(text="Image: N/A")

    def re_detect_objects(self, event=None):
        if self.current_image_cv2 is None:
            messagebox.showinfo("Info", "No image loaded to perform detection on.")
            return
        
        confirm_msg = "This will clear ALL current annotations for this image and run detection again with current model settings. Continue?"
        should_proceed = False
        if event is not None : 
            if self.controller.auto_save_enabled.get():
                self.save_annotations(is_auto_save=True) 
                print("Re-detecting objects...")
                should_proceed = True
            elif messagebox.askyesno("Confirm Re-detection", confirm_msg):
                should_proceed = True
        elif messagebox.askyesno("Confirm Re-detection", confirm_msg): 
            should_proceed = True
        
        if not should_proceed:
            return

        self.annotations = [] 
        self.selected_box_idx = None
        self.perform_auto_detection_and_labeling() 
        self.redraw_all_annotations_on_canvas()
        self.update_info_label()
        if event is None: 
            messagebox.showinfo("Detection", "Object re-detection complete.")
        else:
            print("Object re-detection complete.")
        
        self._trigger_auto_save()


    def _zoom_at_canvas_coords(self, factor, focal_canvas_x, focal_canvas_y):
        if self.current_image_cv2 is None: return

        img_focal_x, img_focal_y = self._canvas_coords_to_img_coords(focal_canvas_x, focal_canvas_y)
        
        new_effective_scale = self.effective_scale_factor * factor
        new_effective_scale = max(self.MIN_ZOOM, min(new_effective_scale, self.MAX_ZOOM))
        
        self.image_canvas_origin_x = focal_canvas_x - (img_focal_x * new_effective_scale)
        self.image_canvas_origin_y = focal_canvas_y - (img_focal_y * new_effective_scale)
        self.effective_scale_factor = new_effective_scale

        self.display_image_on_canvas()
        self.redraw_all_annotations_on_canvas()
        self.update_info_label() 

    def zoom_in_button(self): 
        self._zoom_at_canvas_coords(self.zoom_step_factor, self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2)

    def zoom_out_button(self): 
        self._zoom_at_canvas_coords(1.0 / self.zoom_step_factor, self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2)

    def _on_mouse_wheel(self, event):
        if self.current_image_cv2 is None: return
        factor = 0
        if event.num == 4 or event.delta > 0: 
            factor = self.zoom_step_factor
        elif event.num == 5 or event.delta < 0: 
            factor = 1.0 / self.zoom_step_factor
        
        if factor != 0:
            self._zoom_at_canvas_coords(factor, event.x, event.y)

    def _on_pan_press(self, event):
        if self.current_image_cv2 is None: return
        self.canvas.config(cursor="fleur")
        self._pan_active = True
        self._pan_last_mouse_x = event.x
        self._pan_last_mouse_y = event.y

    def _on_pan_motion(self, event):
        if not self._pan_active or self.current_image_cv2 is None: return
        
        dx = event.x - self._pan_last_mouse_x
        dy = event.y - self._pan_last_mouse_y
        
        self.image_canvas_origin_x += dx
        self.image_canvas_origin_y += dy
        
        self._pan_last_mouse_x = event.x
        self._pan_last_mouse_y = event.y
        
        self.display_image_on_canvas()
        self.redraw_all_annotations_on_canvas()

    def _on_pan_release(self, event):
        self._pan_active = False
        self.canvas.config(cursor="")


if __name__ == "__main__":
    app = AnnotationApp()
    app.mainloop()