from detect_objects import load_custom_trained_model, detect_objects, filter_results
from image_processing import load_image, save_image_with_annotations, format_detection_results
from train_model import train_custom_yolov5
from commons import values as common_values
import os

# Train and save the custom YOLOv5 model
def train_and_save_model(config_path, epochs=35):
    train_custom_yolov5(config_path, epochs=epochs)
    print("Custom model training complete.")

# Save detection results to a JSON file
def save_detections_to_json(detections, output_path):
    import json
    with open(output_path, 'w') as f:
        json.dump(detections, f, indent=4)

# Use the trained model to predict and return a list of qualified labels:
def predict_and_list_labels(image_path, model_path='ai_capstone.pt', confidence = 0.6, boxes_dir="boxes"):
    # Gets some values for later use:
    image_name=os.path.basename(image_path).rsplit('.')[0]
    # Load the custom-trained model
    model = load_custom_trained_model(model_path)
    # Loads image to detect:
    image = load_image(image_path)
    results = detect_objects(model, image)
    # Filters confident results:
    detections = filter_results(results,confidence)
    # Saves to boxes_dir for detailed look:
    os.makedirs(boxes_dir, exist_ok=True)
    save_image_with_annotations(image, detections, f'{boxes_dir}/{image_name}-boxes.jpg')
    save_detections_to_json(detections, f'{boxes_dir}/{image_name}-boxes.json')
    # Returns recommended tags:
    detections_=[common_values["classNames"][i["class"]] for i in detections]
    recommended=[]
    for detection in detections_:
     recommended+=detection.split("/")
    return sorted(list(set(recommended)),key=recommended.index)

if __name__ == "__main__":
 predict_and_list_labels('test.jpg')