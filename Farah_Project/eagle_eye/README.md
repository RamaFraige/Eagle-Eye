# 🚀 Eagle Eye

## 📖 Overview

Eagle Eye is a cutting-edge, real-time AI application designed to bring powerful computer vision capabilities directly to your browser via WebRTC! 🌐✨

Built with performance and modularity in mind, this project leverages the power of **FastAPI** and **FastRTC** to deliver seamless video streaming and processing. Whether you need to detect objects in a busy scene or recognize faces with precision, Eagle Eye has you covered. 🕵️‍♂️📸

## ✨ Key Features

-   **⚡ Real-Time Processing**: Experience low-latency video processing powered by WebRTC.
-   **🔍 Object Detection**: Instantly identify and track objects using state-of-the-art YOLO models. 📦🚗
-   **👤 Face Recognition**: Advanced facial recognition capabilities integrated smoothly into the pipeline. 🆔
-   **🛠️ Modular Architecture**: Easily extendable "Use Cases" allow for flexible and dynamic pipeline creation.
-   **🔀 Dynamic Pipelines**: Combine multiple AI tasks on the fly to suit your specific needs!
-   **📹 Live & Stream Support**: Process both live camera feeds and existing video streams.

## 🚀 Getting Started

Dive into the world of real-time AI!

### 1️⃣ Installation

Make sure you have Python installed, then set up the project:

```bash
# Install dependencies
uv sync
```

### 2️⃣ Running the App

Launch the API server and start streaming:

```bash
python main.py
```

Visit `http://localhost:8000/docs` to explore the API or connect via the WebRTC playground! 🎮

## 🛠️ Technologies Used

-   **FastAPI** ⚡
-   **FastRTC** 📡
-   **YOLO (Ultralytics)** 👁️
-   **DeepFace** 🧠
-   **OpenCV** 📷
