# Conversion Pipeline Summary

1️⃣ .pt ➡️ .onnx

    ```
    yolo export model=yolov8m.pt format=onnx
    ```

# Optional for dynamic input shapes:
    ```
    yolo export model=yolov8m.pt format=onnx dynamic=True
    ```

2️⃣ .onnx ➡️ .engine (TensorRT)
    ⚠️ This exports directly from .pt, not from .onnx.
    
    ```
    yolo export model=yolov8m.pt format=engine
    ```



3️⃣ .onnx ➡️ slim.onnx (ONNX optimization)

    ```
    onnxslim yolov8m.onnx yolov8m.slim.onnx
    ```
