from flask import Flask, request, jsonify
import cv2
from flask_cors import CORS
import numpy as np
import base64
import face_recognition
from io import BytesIO
from PIL import Image
from database import collection  # Import MongoDB connection
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)


def base64_to_image(base64_string):
    """ Convert base64 string to an OpenCV image """
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]  # Remove prefix if exists

        img_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(img_data)).convert("RGB")  # Ensure consistency
        return np.array(image)
    except Exception as e:
        logging.error(f"Error decoding base64 image: {e}")
        return None  # Return None if conversion fails


def preprocess_image(image_array):
    """ Preprocess image for better accuracy """
    try:
        # Convert to grayscale
        gray_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Apply histogram equalization to improve contrast
        equalized_image = cv2.equalizeHist(gray_image)

        # Convert back to RGB (needed for face_recognition) 
        return cv2.cvtColor(equalized_image, cv2.COLOR_GRAY2RGB)
    except Exception as e:
        logging.error(f"Error in image preprocessing: {e}")
        return image_array  # Return original image if preprocessing fails


def get_face_encodings(image_array):
    """ Extract face encodings from an image with improved accuracy """
    try:
        preprocessed_img = preprocess_image(image_array)  # Preprocess the image

        # Try face detection with HOG model first (faster)
        face_locations = face_recognition.face_locations(preprocessed_img, model="hog", number_of_times_to_upsample=2)
        
        if not face_locations:
            logging.warning("⚠️ No face found with HOG model. Retrying with CNN model...")
            face_locations = face_recognition.face_locations(preprocessed_img, model="cnn")
        
        if not face_locations:
            logging.warning("⚠️ No face detected after both attempts.")
            return None  # No face detected

        encodings = face_recognition.face_encodings(preprocessed_img, face_locations)

        if not encodings:
            logging.warning("⚠️ Face detected but no encodings found.")
        
        return encodings if encodings else None
    except Exception as e:
        logging.error(f"Error extracting face encodings: {e}")
        return None  # Return None if encoding fails


@app.route("/api/upload", methods=["POST"])
def upload_image():
    logging.info("Received image upload request")

    if "image" not in request.files:
        logging.warning("No image provided in request")
        return jsonify({"success": False, "message": "No image provided"}), 400

    # Convert uploaded image to numpy array
    image_file = request.files["image"]
    logging.info(f"Image received: {image_file.filename}")

    image = Image.open(image_file).convert("RGB")  # Ensure consistency
    image_array = np.array(image)

    # Get face encodings of uploaded image
    uploaded_encodings = get_face_encodings(image_array)
    if not uploaded_encodings:
        return jsonify({"success": False, "message": "No face detected"}), 400

    # Fetch stored images from MongoDB
    try:
        stored_faces = collection.find({})
    except Exception as e:
        logging.error(f"Database error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500

    matched_faces = []
    threshold = 0.5  # Set a strict threshold for better accuracy

    for stored_face in stored_faces:
        stored_base64 = stored_face.get("image", "")
        stored_image = base64_to_image(stored_base64)

        if stored_image is None:
            continue  # Skip invalid stored images

        stored_encodings = get_face_encodings(stored_image)
        if stored_encodings:
            for stored_encoding in stored_encodings:  # Compare with all detected faces
                for uploaded_encoding in uploaded_encodings:
                    distance = face_recognition.face_distance([stored_encoding], uploaded_encoding)[0]
                    if distance < threshold:  # If it's a match, store the details
                        matched_faces.append({
                            "name": stored_face.get("name", "Unknown"),
                            "age": stored_face.get("age", ""),
                            "gender": stored_face.get("gender", ""),
                            "lastSeenLocation": stored_face.get("lastSeenLocation", ""),
                            "dateMissing": stored_face.get("dateMissing", ""),
                            "contactNumber": stored_face.get("contactNumber", ""),
                            "description": stored_face.get("description", ""),
                            "image": stored_face.get("image", ""),  # Return image if needed
                            "match_score": round(1 - distance, 2)  # Convert distance to similarity score
                        })

    if matched_faces:
        return jsonify({"success": True, "message": "✅ Matches found", "matches": matched_faces}), 200
    else:
        return jsonify({"success": False, "message": "❌ No matching face found"}), 200



@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    """ Fetch complaints from MongoDB """
    try:
        complaints = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB ObjectId
        return jsonify({"success": True, "data": complaints}), 200
    except Exception as e:
        logging.error(f"Error fetching complaints: {e}")
        return jsonify({"success": False, "message": "Error fetching complaints"}), 500


if __name__ == "__main__":
    app.run(debug=True)
