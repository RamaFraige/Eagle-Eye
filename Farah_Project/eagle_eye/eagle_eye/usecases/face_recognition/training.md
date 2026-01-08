# Face Recognition System Guide

This guide details the internal working of the **Face Recognition** system, including the model used, the vector database structure, and the similarity search mechanism.

> [!NOTE]
> Unlike the other use cases, this system uses **pre-trained models** and does not require a training phase (backpropagation). Instead, it relies on "registering" faces into a vector database.

## 1. Model Details

The system uses the **DeepFace** framework for face analysis.

*   **Model Architecture**: `VGG-Face`
*   **Input**: RGB Images (aligned and processed by DeepFace)
*   **Output**: Face Embeddings (Vector representation of the face)
*   **Framework**: `DeepFace` (atop TensorFlow/Keras)

## 2. Vector Database

We use **FAISS** (Facebook AI Similarity Search) to store and search face embeddings efficiently.

### Structure
*   **Index Type**: `IndexIDMap(IndexFlatL2)`
    *   `IndexFlatL2`: Performs exact search using L2 (Euclidean) distance.
    *   `IndexIDMap`: Maps the internal FAISS vector IDs to our custom Person IDs (stored in SQL).
*   **Storage**: The index is serialized to disk as `faiss_index.bin` in the vector directory.

### Registration Process (Building the DB)
1.  **Detection**: The system detects faces in an input image.
2.  **Representation**: `DeepFace.represent` is called with `model_name="VGG-Face"`.
3.  **Indexing**: The resulting embedding vector is added to the FAISS index, associated with a unique Person ID.
4.  **Metadata**: The Person ID and Name are stored in a relational database (SQLite/PostgreSQL) via `MetadataStore`.

## 3. Similarity Search

When the system sees a new face, it performs the following steps to identify it:

1.  **Generate Vector**: The new face is converted into an embedding using the same `VGG-Face` model.
2.  **FAISS Search**: The system queries the FAISS index for the *nearest neighbor* (k=1) using **L2 Distance**.
3.  **Similarity Calculation**:
    The raw L2 distance is converted into a normalized similarity score (0 to 1).

    $$ \text{Similarity} = 1.0 - \left( \frac{\text{Distance}}{2.0} \right) $$

    *   **Distance 0** → **Similarity 1.0** (Perfect Match)
    *   **Distance 2** → **Similarity 0.0** (Completely Different)

4.  **Thresholding**:
    *   If `Similarity > Threshold` (configured in `confidence_threshold`), the face is identified as the person.
    *   Otherwise, it is labeled as **"Unknown"**.
