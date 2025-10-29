# Image Annotation Tool 🖼️

An interactive GUI-based image annotation tool built using **Tkinter** and **YOLOv8** for automated and manual bounding box creation.

## 🚀 Features
- Auto-detection using YOLOv8 (Ultralytics)
- Manual annotation and class assignment
- Supports zoom, pan, and auto-save
- YOLO format label handling (load & save)
- Folder-based image loading and organization

## 🧠 Tech Stack
- Python 3.12  
- Tkinter  
- OpenCV  
- Ultralytics (YOLOv8)  
- Pillow (PIL)

## ⚙️ Setup

```
    git clone <your-repo-url>
    cd <your-repo-name>
    python -m venv env
    .\env\Scripts\activate   # For Windows
    pip install -r requirements.txt

```

# Run the Application
```
    python annotation_gui.py
```

📦 Create Requirements File
```
    cd 'prject location'
    python pyreq.py
```
🖊️ Notes

Default model: yolov8n.pt
For specific models: drag and drop (e.g., yolov8m-face.pt or your custom-trained model)
Output: Annotations are saved in YOLO format inside your chosen label folder.


🏷️ Example
class_id x_center y_center width height

📸 Preview
Coming soon...

🔖 License
MIT License © 2025

---

Would you like me to generate the `requirements.txt` content manually (based on your imports) so you can include it directly without running `pip freeze`?
