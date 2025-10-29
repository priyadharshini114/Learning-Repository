import os
import cv2
from ultralytics import YOLO

class YOLOModel:
    """
    Wrapper for the YOLO model to perform detection,
    with optional filtering for specific target classes.
    """
    def __init__(self, model_path, target_class_indices=None): # Added target_class_indices
        if not os.path.exists(model_path):
            # If model_path is a standard name like "yolov8m.pt", YOLO() will download it.
            # This check is more for custom local paths.
            # However, YOLO() itself will raise an error if it can't find/download.
            # We can simplify this, as YOLO handles it.
            pass # YOLO constructor will handle path/name resolution

        self.model_path = model_path
        self.model = YOLO(self.model_path) # YOLO handles download if model_path is like "yolov8n.pt"
        self.BBOX_EXPANSION = 0.20
        self.target_class_indices = target_class_indices
        
        # Expose model names for GUI to use for mapping
        self.model_names = self.model.names if hasattr(self.model, 'names') else {}


    def set_bbox_expansion(self, expansion_ratio):
        self.BBOX_EXPANSION = expansion_ratio

    def detect(self, image_cv2, conf_threshold=0.5):
        height, width = image_cv2.shape[:2]
        results = self.model(image_cv2, conf=conf_threshold, verbose=False)
        
        detected_boxes = []
        if results and results[0].boxes:
            for box in results[0].boxes:
                # Filter by target class if specified
                if self.target_class_indices is not None and len(self.target_class_indices) > 0:
                    detected_cls_index = int(box.cls[0])
                    if detected_cls_index not in self.target_class_indices:
                        continue # Skip this box if its class is not targeted

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                box_width = x2 - x1
                box_height = y2 - y1

                # Skip if box has no area (can happen with extreme confidences or odd models)
                if box_width <= 0 or box_height <= 0:
                    continue

                expand_w = box_width * self.BBOX_EXPANSION / 2
                expand_h = box_height * self.BBOX_EXPANSION / 2
                
                x1_expanded = max(0, int(x1 - expand_w))
                y1_expanded = max(0, int(y1 - expand_h))
                x2_expanded = min(width, int(x2 + expand_w))
                y2_expanded = min(height, int(y2 + expand_h))
                
                detected_boxes.append([x1_expanded, y1_expanded, x2_expanded, y2_expanded])
        return detected_boxes

class AnnotationProcessor:
    @staticmethod
    def yolo_to_pixels(yolo_bbox, img_width, img_height):
        x_center_norm, y_center_norm, w_norm, h_norm = yolo_bbox
        box_w = w_norm * img_width
        box_h = h_norm * img_height
        x_center = x_center_norm * img_width
        y_center = y_center_norm * img_height
        x1 = int(x_center - box_w / 2)
        y1 = int(y_center - box_h / 2)
        x2 = int(x_center + box_w / 2)
        y2 = int(y_center + box_h / 2)
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(img_width, x2); y2 = min(img_height, y2)
        return [x1, y1, x2, y2]

    @staticmethod
    def pixels_to_yolo(pixel_bbox, img_width, img_height):
        x1, y1, x2, y2 = pixel_bbox
        if img_width == 0 or img_height == 0: return [0.0, 0.0, 0.0, 0.0]
        x_center = ((x1 + x2) / 2) / img_width
        y_center = ((y1 + y2) / 2) / img_height
        w_norm = (x2 - x1) / img_width
        h_norm = (y2 - y1) / img_height
        return [
            max(0.0, min(1.0, x_center)), max(0.0, min(1.0, y_center)),
            max(0.0, min(1.0, w_norm)), max(0.0, min(1.0, h_norm)),
        ]

    @staticmethod
    def load_yolo_labels(label_file_path, img_width, img_height):
        annotations = []
        if not os.path.exists(label_file_path):
            return annotations
        with open(label_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        class_id = int(parts[0])
                        yolo_bbox_norm = list(map(float, parts[1:]))
                        pixel_bbox = AnnotationProcessor.yolo_to_pixels(yolo_bbox_norm, img_width, img_height)
                        annotations.append({'class_id': class_id, 'bbox_pixels': pixel_bbox})
                    except ValueError as e:
                        print(f"Warning: Skipping malformed line in {label_file_path}: {line.strip()} - Error: {e}")
        return annotations

    @staticmethod
    def save_yolo_labels(label_file_path, annotations, img_width, img_height):
        label_dir = os.path.dirname(label_file_path)
        if label_dir: os.makedirs(label_dir, exist_ok=True)
        with open(label_file_path, 'w') as f:
            for ann in annotations:
                if ann.get('class_id') is None: continue
                class_id = ann['class_id']
                pixel_bbox = ann['bbox_pixels']
                yolo_bbox_norm = AnnotationProcessor.pixels_to_yolo(pixel_bbox, img_width, img_height)
                f.write(f"{class_id} {yolo_bbox_norm[0]:.6f} {yolo_bbox_norm[1]:.6f} {yolo_bbox_norm[2]:.6f} {yolo_bbox_norm[3]:.6f}\n")

def list_image_files(root_folder_path):
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
    image_info_list = []

    if not os.path.isdir(root_folder_path):
        print(f"Warning: Image folder not found or is not a directory: {root_folder_path}")
        return image_info_list

    for fname in os.listdir(root_folder_path):
        fpath = os.path.join(root_folder_path, fname)
        if os.path.isfile(fpath) and fname.lower().endswith(supported_formats):
            image_info_list.append({'path': fpath, 'parent_folder_name': None})

    for class_folder_name_candidate in os.listdir(root_folder_path):
        class_folder_path = os.path.join(root_folder_path, class_folder_name_candidate)
        if os.path.isdir(class_folder_path):
            for img_fname_direct in os.listdir(class_folder_path):
                img_fpath_direct = os.path.join(class_folder_path, img_fname_direct)
                if os.path.isfile(img_fpath_direct) and img_fname_direct.lower().endswith(supported_formats):
                    image_info_list.append({'path': img_fpath_direct, 'parent_folder_name': class_folder_name_candidate})
            
            images_subfolder_path = os.path.join(class_folder_path, "images")
            if os.path.isdir(images_subfolder_path):
                for img_fname_in_images_subfolder in os.listdir(images_subfolder_path):
                    img_fpath_in_sub = os.path.join(images_subfolder_path, img_fname_in_images_subfolder)
                    if os.path.isfile(img_fpath_in_sub) and img_fname_in_images_subfolder.lower().endswith(supported_formats):
                        image_info_list.append({'path': img_fpath_in_sub, 'parent_folder_name': class_folder_name_candidate})

    unique_image_info_list = []
    seen_paths = set()
    for item in image_info_list:
        if item['path'] not in seen_paths:
            unique_image_info_list.append(item)
            seen_paths.add(item['path'])
    
    unique_image_info_list.sort(key=lambda x: x['path'])
    return unique_image_info_list


if __name__ == '__main__':
    print("Testing annotation_core.py...")
    # Test with a general model and target classes
    try:
        print("\nTesting with yolov8n.pt and target_class_indices=[0] (person)")
        # YOLO will download yolov8n.pt if not present
        model_person = YOLOModel("yolov8n.pt", target_class_indices=[0]) 
        print(f"YOLOModel with target initialized. Available model classes: {model_person.model_names}")
        
        # Create a dummy image that might have a person (or not)
        # For a real test, use an image with known objects.
        # Here, we'll just ensure it runs without error.
        dummy_image_name_person = "dummy_test_image_person.png"
        img_height_p, img_width_p = 480, 640 # A slightly larger dummy image
        # Create a colorful dummy image to give detector something to work on
        dummy_img_cv2_person = cv2.UMat(img_height_p, img_width_p, cv2.CV_8UC3).get() 
        dummy_img_cv2_person[:, :, 0] = 100 # B
        dummy_img_cv2_person[:, :, 1] = 50  # G
        dummy_img_cv2_person[:, :, 2] = 200 # R
        cv2.putText(dummy_img_cv2_person, "Test", (50,50), cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)
        cv2.imwrite(dummy_image_name_person, dummy_img_cv2_person)

        detections_person = model_person.detect(dummy_img_cv2_person)
        print(f"Detections for person on dummy image: {detections_person}")
        if os.path.exists(dummy_image_name_person): os.remove(dummy_image_name_person)

    except Exception as e:
        print(f"Could not initialize YOLOModel for person detection testing: {e}")


    # Original tests
    try:
        test_model_path = "yolov8n-face.pt" # Assuming this is a face-specific model
        print(f"\nAttempting to initialize YOLOModel with: {test_model_path} (no target classes)")
        model = YOLOModel(test_model_path) # No target classes, assumes specialized model
        print("YOLOModel (face) initialized.")
        print(f"Face model names (if any from model): {model.model_names}")
    except Exception as e:
        print(f"Could not initialize YOLOModel for testing: {e}")
        model = None

    dummy_image_name = "dummy_test_image.png"
    img_height, img_width = 100, 100
    dummy_img_cv2 = cv2.UMat(img_height, img_width, cv2.CV_8UC3).get() 
    cv2.imwrite(dummy_image_name, dummy_img_cv2)

    if model:
        print("\nTesting YOLOModel (face) detection...")
        detections = model.detect(dummy_img_cv2)
        print(f"Detections on dummy image (face model): {detections}") 

    print("\nTesting AnnotationProcessor...")
    ap = AnnotationProcessor()
    px_bbox = [10, 20, 60, 80]; yolo_bbox = ap.pixels_to_yolo(px_bbox, img_width, img_height)
    print(f"Pixel {px_bbox} to YOLO: {yolo_bbox}")
    re_px_bbox = ap.yolo_to_pixels(yolo_bbox, img_width, img_height)
    print(f"YOLO {yolo_bbox} back to Pixel: {re_px_bbox}")

    dummy_label_file = "dummy_test_label.txt"
    test_annotations = [{'class_id': 0, 'bbox_pixels': [10,10,50,50]}]
    ap.save_yolo_labels(dummy_label_file, test_annotations, img_width, img_height)
    loaded_annotations = ap.load_yolo_labels(dummy_label_file, img_width, img_height)
    print(f"Loaded annotations: {loaded_annotations}")

    print("\nTesting modified list_image_files...")
    import shutil
    test_root = "test_image_hierarchy_core"
    os.makedirs(os.path.join(test_root, "female", "images"), exist_ok=True)
    os.makedirs(os.path.join(test_root, "male"), exist_ok=True)

    cv2.imwrite(os.path.join(test_root, "root_img.jpg"), dummy_img_cv2)
    cv2.imwrite(os.path.join(test_root, "female", "f_direct.png"), dummy_img_cv2)
    cv2.imwrite(os.path.join(test_root, "female", "images", "f_in_images_sub.jpg"), dummy_img_cv2)
    cv2.imwrite(os.path.join(test_root, "male", "m1.jpeg"), dummy_img_cv2)
    
    image_list = list_image_files(test_root)
    print("Images found with hierarchy:")
    for img_info in image_list:
        print(img_info)
    
    if os.path.exists(dummy_image_name): os.remove(dummy_image_name)
    if os.path.exists(dummy_label_file): os.remove(dummy_label_file)
    if os.path.exists(test_root): shutil.rmtree(test_root)
    print("\nCore logic tests completed.")