import os
import cv2
import face_recognition
import numpy as np
from tqdm import tqdm
import time
import pickle
import gspread

class Face:
    def __init__(self, bounding_box, cropped_face, name, feature_vector):
        self.bounding_box = bounding_box
        self.cropped_face = cropped_face
        self.name = name
        self.feature_vector = feature_vector
        
def load_image(path):
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

def create_database(filenames, images):
    faces = []
    for filename, image in tqdm(zip(filenames, images), total=len(filenames)):
        try:
            loc = face_recognition.face_locations(image, model='hog')[0]
            vec = face_recognition.face_encodings(image, [loc], num_jitters=20)[0]
        except Exception as e:
            print(f"No Face Found in {filename}")
            continue
        
        top, right, bottom, left = loc
        cropped_face = image[top:bottom, left:right]
        face = Face(bounding_box=loc, cropped_face=cropped_face, name=filename.split('.')[0], feature_vector=vec)
        faces.append(face)
    
    return faces

def detect_faces(image_test, faces, threshold=0.6, unknown_threshold=0.55):
    locs_test = face_recognition.face_locations(image_test, model='hog')
    vecs_test = face_recognition.face_encodings(image_test, locs_test, num_jitters=1)

    name_counts = {}
    name_percentages = {}
    unknown_detected = False

    for loc_test, vec_test in zip(locs_test, vecs_test):
        distances = []
        for face in faces:
            distance = face_recognition.face_distance([vec_test], face.feature_vector)
            distances.append(distance)

        min_distance = np.min(distances)
        match_percentage = (1 - min_distance) * 100  # Convert distance to percentage match

        if match_percentage / 100 < threshold:
            pred_name = 'Unknown Face Detected'
            unknown_detected = True
        else:
            if match_percentage / 100 < unknown_threshold:
                pred_name = 'Unknown Face Detected'
                unknown_detected = True
            else:
                pred_index = np.argmin(distances)
                pred_name = faces[pred_index].name

            # Update counts and percentages
            if pred_name not in name_counts:
                name_counts[pred_name] = 0
                name_percentages[pred_name] = 0
            name_counts[pred_name] += 1
            name_percentages[pred_name] += match_percentage

        image_test = draw_bounding_box(image_test, loc_test)
        image_test = draw_name(image_test, loc_test, pred_name)

    if unknown_detected:
        print("Unknown Face Detected")
    else:
        if name_percentages:  # Check if name_percentages is not empty
            # Calculate average match percentages
            for name in name_counts:
                name_percentages[name] /= name_counts[name]

            # Determine the person with the highest average match percentage
            highest_match_name = max(name_percentages, key=name_percentages.get)    

            if highest_match_name == "Unknown Face Detected":
                print("Unknown Face Detected")
            else:
                print(f"Detected person: {highest_match_name} (Average confidence: {name_percentages[highest_match_name]:.2f}%)")
        else:
            # print(highest_match_name)
            print("No faces detected.")

    return image_test

def draw_bounding_box(image_test, loc_test):
    top, right, bottom, left = loc_test
    line_color = (0, 255, 0)
    line_thickness = 2
    cv2.rectangle(image_test, (left, top), (right, bottom), line_color, line_thickness)
    return image_test

def draw_name(image_test, loc_test, pred_name):
    top, right, bottom, left = loc_test 
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    font_color = (0, 0, 255)
    line_thickness = 3
    text_size, _ = cv2.getTextSize(pred_name, font, font_scale, line_thickness)
    bg_top_left = (left, top-text_size[1])
    bg_bottom_right = (left+text_size[0], top)
    cv2.rectangle(image_test, bg_top_left, bg_bottom_right, (0, 255, 0), -1)   
    cv2.putText(image_test, pred_name, (left, top), font, font_scale, font_color, line_thickness)
    return image_test

# Define the filename for saving and loading the database
DATABASE_FILENAME = 'faces_database.pkl'

# Function to save the face database
def save_database(faces):
    with open(DATABASE_FILENAME, 'wb') as f:
        pickle.dump(faces, f)

# Function to load the face database
def load_database():
    try:
        with open(DATABASE_FILENAME, 'rb') as f:
            faces = pickle.load(f)
        return faces
    except FileNotFoundError:
        return []

if __name__ == "__main__":
    # Load or create the face database
    faces = load_database()

    # If the database is empty, create it
    if not faces:
        filenames = os.listdir('known_faces')
        images = [load_image(f'known_faces/{filename}') for filename in filenames]
        faces = create_database(filenames, images)
        # Save the database for future use
        save_database(faces)

    # Open webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    frame_count = -1
    prev_frame_time = 0
    total_frame_time = []

    while True:
        start_time = time.time()

        ret, image = cap.read()

        if ret:
            # Calculate the time taken to capture each frame
            frame_time = time.time() - prev_frame_time
            prev_frame_time = time.time()

            total_frame_time.append(frame_time)

            image_display = image.copy()  # Create a copy for display

            # Process every 10th frame
            if frame_count % 10 == 0:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                image = detect_faces(image, faces, threshold=0.6)

            # Show the output image
            cv2.imshow('image', image_display)

            # Print the time taken to capture each frame
            print("Time taken for each frame:", frame_time)

        frame_count += 1

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            
            total_frame_time.remove(total_frame_time[0])

            print("Average frame time:", sum(total_frame_time) / frame_count)
            break
    
    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()