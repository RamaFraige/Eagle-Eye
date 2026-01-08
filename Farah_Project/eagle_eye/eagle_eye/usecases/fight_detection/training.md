# ActionLSTM Training Guide

This guide details how to train the **ActionLSTM** model on a custom dataset for the Behavior Detection system.

## 1. Dataset Format

The training system requires two specific text files: one for input features (keypoints) and one for target labels (actions).

### Files Required
*   **`train_x.txt`**: The input features.
*   **`train_y.txt`**: The target labels.
*   *(Optional)* `val_x.txt` / `val_y.txt`: Validation set (same format).

### Data Structure Rules
The model uses a sliding window (time-distributed) approach. You must adhere to the following strict relationships between the files:

*   **Sequence Length (`n_steps`)**: The model consumes fixed-length sequences of frames. The default is **32 frames**.
*   **Relationship**: The number of lines in `train_x.txt` must be exactly `n_steps` times the number of lines in `train_y.txt`.

$$ \text{Lines in X} = \text{Lines in Y} \times \text{n\_steps} $$

### File Formats in Detail

#### `train_x.txt` (Features)
*   **Content**: Flattened pose keypoints for a single frame per line.
*   **Format**: Comma-separated floating-point values.
*   **Example**:
    ```text
    0.54,0.32,0.66,0.21,... (total n_input values)
    0.55,0.33,0.66,0.22,...
    ...
    ```

#### `train_y.txt` (Labels)
*   **Content**: One label per **sequence** (i.e., per block of 32 frames).
*   **Format**: Integer representing the action class.
*   **indexing**: The file should use **1-based indexing** (e.g., 1, 2, 3...). The loader automatically converts this to 0-based indexing (0, 1, 2...) for training.
*   **Example**:
    ```text
    1
    1
    4
    2
    ...
    ```
    *(If line 1 is `1`, it means the first 32 lines of `train_x.txt` belong to class 1).*

## 2. Model & Training Parameters

When setting up the training script, you can tune the following parameters.

### `ActionLSTM` (The Model)
Located in `behavior_detection.core.model`.

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `n_input` | `int` | The size of the feature vector for a single frame (e.g., 24 for 17 x,y points). |
| `n_hidden` | `int` | The number of hidden units in the LSTM layers. Larger values capture more complex patterns but risk overfitting. |
| `n_classes` | `int` | The total number of unique action classes to predict. |
| `lambda_l2` | `float` | L2 regularization factor (optional, used for loss calculation if manually implemented). |

### `ActionTrainer.fit` (The Training Loop)
Located in `behavior_detection.training.trainer`.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `epochs` | `int` | `100` | Number of times to iterate over the entire dataset. |
| `batch_size` | `int` | `1024` | Number of sequences to process at once. |
| `learning_rate` | `float` | `0.0025` | Step size for the optimizer (Adam). |
| `lambda_loss` | `float` | `0.0015` | Weight decay (L2 penalty) applied by the optimizer to prevent overfitting. |
| `save_path` | `str` | `None` | File path to save the trained model weights (`.pth`). |

## 3. Training Script

Create a Python script (e.g., `train_custom.py`) with the following content to start training.

```python
import torch
from behavior_detection.core import ActionLSTM
from behavior_detection.training import ActionTrainer

def main():
    # 1. Configuration
    # Adjust these to match your dataset and needs
    N_INPUT_FEATURES = 24  # e.g., 17 keypoints * 2 (x, y)
    N_HIDDEN_UNITS = 34    # Hidden layer size
    N_CLASSES = 4          # Number of action classes
    
    BATCH_SIZE = 1024
    EPOCHS = 300
    LEARNING_RATE = 0.0025
    
    # 2. Setup Device and Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = ActionLSTM(
        n_input=N_INPUT_FEATURES, 
        n_hidden=N_HIDDEN_UNITS, 
        n_classes=N_CLASSES
    )
    
    # 3. Initialize Trainer
    trainer = ActionTrainer(model, device)
    
    # 4. Start Training
    try:
        trainer.fit(
            # Paths to your custom dataset
            train_x_path="data/my_dataset/train_x.txt",
            train_y_path="data/my_dataset/train_y.txt",
            val_x_path="data/my_dataset/val_x.txt",
            val_y_path="data/my_dataset/val_y.txt",
            
            # Hyperparameters
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            lambda_loss=0.0015,
            
            # Output
            save_path="weights/my_custom_model.pth"
        )
    except Exception as e:
        print(f"An error occurred during training: {e}")

if __name__ == "__main__":
    main()
```

## 4. Verification

After training, you can verify your model using the `test` method provided by the trainer:

```python
# ... setup model and trainer as above ...

# Load the best saved weights
model.load_state_dict(torch.load("weights/my_custom_model.pth"))

# Run evaluation on a separate test set
trainer.test(
    test_x_path="data/my_dataset/test_x.txt",
    test_y_path="data/my_dataset/test_y.txt"
)
```


## 5. Dataset

The dataset is constructed by extracting feature vectors for each frame and organizing them into action sequences. Each sequence consists of **32 frames**, generated using a sliding window with an **overlap of 24 frames**.

### Dataset Summary

| Action | Sequence Count | Source Breakdown |
| :--- | :--- | :--- |
| **Standing (1)** | 7,474 | 7,474 (pose3_stand) |
| **Walking (2)** | 4,213 | 854 (pose3_walk), 3,359 (pose6_walk) |
| **Punching (3)** | 2,187 | 1,115 (mhad_punch), 1,072 (mhad_punch_flip) |
| **Kicking (4)** | 4,694 | 2,558 (pose3_kick), 2,136 (pose6_kick) |
| **Total** | **18,573** | [Download Dataset](https://drive.google.com/open?id=1ZNJDzQUjo2lDPwGoVkRLg77eA57dKUqx) |
| **Time** | **18,573** | ≈ 19.3 minutes |

* For training on this dataset, use the `train_custom.py` script.

```py
# train_custom.py
import torch
from pathlib import Path
from behavior_detection.core import ActionLSTM
from behavior_detection.training import ActionTrainer
from behavior_detection.training.dataset_split import train_val_split

DATA_DIR = Path("./training")
DATASET_DIR =  DATA_DIR / 'datasets'
SPLIT_DIR = DATA_DIR / 'split'
WEIGHTS_DIR = Path("./weights")

def main():
    # 1. Configuration
    # Adjust these to match your dataset and needs
    N_INPUT_FEATURES = 24  # Match actual dataset dimension
    N_HIDDEN_UNITS = 34    # Hidden layer size
    N_CLASSES = 4          # Number of action classes
    
    N_STEP = 32

    BATCH_SIZE = 1024
    EPOCHS = 100
    LEARNING_RATE = 0.0025

    # 2. Train val split
    train_x, train_y, val_x, val_y = train_val_split(
        X_path=DATASET_DIR / "pose_36.txt",
        y_path=DATASET_DIR / "pose36_c.txt",
        output_dir=SPLIT_DIR,
        val_ratio=0.2,
        n_steps=N_STEP
    )

    
    # 3. Setup Device and Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = ActionLSTM(
        n_input=N_INPUT_FEATURES, 
        n_hidden=N_HIDDEN_UNITS, 
        n_classes=N_CLASSES
    )
    
    # 4. Initialize Trainer
    trainer = ActionTrainer(model, device)
    
    # 5. Start Training
    try:
        trainer.fit(
            # Paths to your custom dataset
            train_x_path=SPLIT_DIR / "train_x.txt",
            train_y_path=SPLIT_DIR / "train_y.txt",
            val_x_path=SPLIT_DIR / "val_x.txt",
            val_y_path=SPLIT_DIR / "val_y.txt",
            
            # Hyperparameters
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            lambda_loss=0.0015,
            
            # Output
            save_path=WEIGHTS_DIR / "action.pth"
        )
    except Exception as e:
        print(f"An error occurred during training: {e}")

    # 6. Test the model
    state_dict = torch.load(WEIGHTS_DIR / "action.pth", map_location=device)
    model.load_state_dict(state_dict)

    loss, accuracy = trainer.test(
        test_x_path=SPLIT_DIR / "val_x.txt",
        test_y_path=SPLIT_DIR / "val_y.txt",
        batch_size=BATCH_SIZE,
    ) # Test Results | Loss: 0.0321 | Accuracy: 0.9917

if __name__ == "__main__":
    main()
```
