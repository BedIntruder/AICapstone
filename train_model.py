import torch
import yaml
import subprocess
import os

MODEL_NAME="ai_capstone"

# Quick sanity check on dataset integrity and class counts:
def check_dataset_integrity(image_dir, label_dir):
    missing_labels = []
    class_counts = {}

    for image_file in os.listdir(image_dir):
        base_name = os.path.splitext(image_file)[0]
        label_file = os.path.join(label_dir, f"{base_name}.txt")
        
        if not os.path.exists(label_file):
            missing_labels.append(image_file)
        else:
            with open(label_file, 'r') as f:
                for line in f:
                    class_id = int(line.split()[0])
                    if class_id not in class_counts:
                        class_counts[class_id] = 0
                    class_counts[class_id] += 1

    print("Missing label files for images:", missing_labels)
    print("Class distribution:", class_counts)

# Load class names from the configuration file
def load_classes(config_path):
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    return data['names']

# Train the YOLOv5 model using custom classes and transfer learning
def train_custom_yolov5(config_path, epochs=100, batch_size=4, img_size=640):
    # Load the number of classes from the config file
    class_names = load_classes(config_path)
    num_classes = len(class_names)

    # Run YOLOv5's train.py as a subprocess to handle custom model training
    command = [
        "python", "yolov5/train.py",
        "--img", str(img_size),
        "--batch", str(batch_size),
        "--epochs", str(epochs),
        "--data", config_path,  # Path to the dataset config file
        "--weights", "yolov5x.pt",  # Start with a pretrained model
        "--project", "runs/train",  # Output directory
        "--name", MODEL_NAME,  # Name of the run
        '--hyp', 'hyperparameters.yaml' # Hyperparameters:
        "--exist-ok",  # Overwrite existing runs
    ]

    # Run the training command
    subprocess.run(command, check=True)
    print(f"Training complete. Model saved in 'runs/train/{MODEL_NAME}' folder.")