from PIL import Image
import cv2
import numpy as np
from commons import values as common_values

# Load an image from a file path
def load_image(image_path):
    image = Image.open(image_path)
    return image

# Convert detections to a formatted dictionary
def format_detection_results(results):
    detections = []
    for *box, conf, cls in results.xyxy[0].cpu().numpy():
        detection = {
            'class': int(cls),
            'confidence': float(conf),
            'bbox': [int(x) for x in box]
        }
        detections.append(detection)
    return detections

# Save the image with bounding box annotations
def save_image_with_annotations(image, detections, output_path):
    # Convert PIL image to an OpenCV-compatible format
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Loop over each detection and draw it on the image
    for detection in detections:
        bbox = detection['bbox']
        class_id = detection['class']
        confidence = detection['confidence']

        # Extract bounding box coordinates
        x_min, y_min, x_max, y_max = bbox

        # Draw the bounding box
        cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

        # Prepare the label with class name and confidence
        label = f"{common_values['classNames'][class_id]}: {confidence:.2f}"

        # Calculate text size and background rectangle
        (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x_min = x_min
        label_y_min = y_min - text_height - 10 if y_min - text_height - 10 > 0 else y_min + text_height + 10
        
        # Draw a filled rectangle for the label background
        cv2.rectangle(image, (label_x_min, label_y_min - text_height - baseline), 
                      (label_x_min + text_width, label_y_min + baseline), (0, 255, 0), -1)

        # Put the label text on the image
        cv2.putText(image, label, (label_x_min, label_y_min), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Convert image back to RGB for PIL compatibility
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    annotated_image = Image.fromarray(image)

    # Save the annotated image
    annotated_image.save(output_path)