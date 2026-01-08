# Object Detection Training Guide (Guns)

This guide details how to train the **YOLOv11** model on a custom dataset for the Gun Detection system.

## 1. Prerequisites

Ensure you have the necessary libraries installed.

```bash
pip install -Uq ultralytics roboflow
```

## 2. Dataset Format

We use a dataset from Roboflow. The training script handles the download automatically.

*   **Workspace**: `muha`
*   **Project**: `gun-soqmi`
*   **Version**: `2`
*   **Format**: `yolov11`

## 3. Training Script

Create a Python script (e.g., `train_object_detection.py`) with the following content to start training.

```python
import os
from pathlib import Path
from IPython import display
import ultralytics
from ultralytics import YOLO
from roboflow import Roboflow

def main():
    # 1. Configuration
    EPOCHS = 100
    IMG_SIZE = 640
    MODEL_VARIANT = "yolo11n.pt"  # Options: yolo11n.pt, yolo11s.pt, etc.
    
    # 2. Setup
    ultralytics.checks()
    HOME = Path.cwd()
    DATASET_DIR = HOME / "datasets"
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    
    # 3. Download Dataset
    # https://universe.roboflow.com/muha/gun-soqmi
    rf = Roboflow(api_key="<API_KEY>")
    project = rf.workspace("muha").project("gun-soqmi")
    version = project.version(2)
    dataset = version.download("yolov11", location=str(DATASET_DIR))
    
    print(f"Dataset directory: {DATASET_DIR}")
    
    # 4. Initialize Model
    model = YOLO(MODEL_VARIANT)
    
    # 5. Train
    # The dataset download usually provides a data.yaml file in the download location
    yaml_file = str(DATASET_DIR / "data.yaml")
    
    results = model.train(
        data=yaml_file,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        device=0,  # Use 0 for GPU, 'cpu' for CPU
    )
    
    # 6. Validation
    metrics = model.val()
    print("Summary")
    print(metrics.summary())
    
    print("mAP@0.5:", metrics.box.map50)
    print("mAP@0.5:0.95:", metrics.box.map)
    print("Precision:", metrics.box.mp)
    print("Recall:", metrics.box.mr)

if __name__ == "__main__":
    main()
```

## 4. Model & Parameters

| Parameter | Value | Description |
| :--- | :--- | :--- |
| `EPOCHS` | `100` | Number of training epochs. |
| `IMG_SIZE` | `640` | Input image resolution. |
| `MODEL` | `yolo11n.pt` | The base pre-trained model. You can choose other variants like `yolo11s.pt`, `yolo11m.pt`, etc. |
| `Device` | `0` | GPU device index. Use `cpu` if no GPU is available. |
| `Time` | `≈7.30 Hours` | Training time |