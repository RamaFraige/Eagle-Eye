import torch

available = torch.cuda.is_available()  # Returns True if CUDA is available
device = torch.device("cuda" if available else "cpu")

print(f"CUDA available? {available}")
print(f"Using device: {device}")
if available:
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    print(f"Current GPU name: {torch.cuda.get_device_name(0)}")
