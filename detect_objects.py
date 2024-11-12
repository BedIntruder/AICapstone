import torch
from image_processing import format_detection_results
from commons import values as common_values

# Load the YOLOv5 pretrained model (now unused)
def load_model():
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    return model

# Load the fine-tuned YOLOv5 model
def load_custom_trained_model(model_path='capstone.pt'):
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
    return model

# Run object detection on an image
def detect_objects(model, image):
    results = model(image)
    return results

# Filter confident results:
def filter_results(results,conf=0.5):
    detections=format_detection_results(results)
    filtered=set(range(365))-set(common_values["classNames"].keys())
    filtered_results=[]
    for detection in detections:
        if detection['confidence']>=conf and detection['class'] not in filtered:
            filtered_results.append(detection)
    return filtered_results