import cv2
import face_recognition
import numpy as np
from tqdm import tqdm
import pickle

consistent_faces = {}
DATABASE_FILENAME = 'faces_database.pkl'

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

def save_database(faces):
    with open(DATABASE_FILENAME, 'wb') as f:
        pickle.dump(faces, f)

def load_database():
    try:
        with open(DATABASE_FILENAME, 'rb') as f:
            faces = pickle.load(f)
        return faces
    except FileNotFoundError:
        return []
    
def draw_bounding_box(image_test, loc_test):
    top, right, bottom, left = loc_test
    line_color = (0, 255, 0)
    line_thickness = 2
    cv2.rectangle(image_test, (left, top), (right, bottom), line_color, line_thickness)
    return image_test

def draw_name(image_test, loc_test, pred_name, conf):
    top, right, bottom, left = loc_test
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.75
    font_color = (0, 0, 255)
    line_thickness = 2
    text_size, _ = cv2.getTextSize(str(pred_name) + " " + str(round(conf, 2)) + "%" , font, font_scale, line_thickness)
    bg_top_left = (left, top - text_size[1])
    bg_bottom_right = (left + text_size[0], top)
    cv2.rectangle(image_test, bg_top_left, bg_bottom_right, (0, 255, 0), -1)   
    cv2.putText(image_test, str(pred_name) + " " + str(round(conf, 2)) + "%", (left, top), font, font_scale, font_color, line_thickness)
    return image_test

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

def detect_faces(image_test, faces, detected_faces, threshold=0.6, unknown_threshold=0.55, min_frames = 20):
    locs_test = face_recognition.face_locations(image_test, model='hog')
    vecs_test = face_recognition.face_encodings(image_test, locs_test, num_jitters=1)

    if len(locs_test) == 0:  # Check if no faces are detected
        print("No Faces Detected")
        return image_test

    for loc_test, vec_test in zip(locs_test, vecs_test):
        distances = [face_recognition.face_distance([vec_test], face.feature_vector) for face in faces]
        min_distance = np.min(distances)
        match_percentage = (1 - min_distance) * 100

        if match_percentage / 100 < threshold:
            print("Unknown Face Detected")
            pred_name = 'Unknown Face Detected'

        else:
            if match_percentage / 100 < unknown_threshold:
                print("Unknown Face Detected")
                pred_name = 'Unknown Face Detected'
            else:
                pred_index = np.argmin(distances)
                pred_name = faces[pred_index].name
                confidence = match_percentage / 100
                print(f"Detected person: {pred_name} (Confidence: {match_percentage:.2f}%)")

            # Update local storage
            if pred_name not in detected_faces:
                detected_faces[pred_name] = 0
            detected_faces[pred_name] += 1

        image_test = draw_bounding_box(image_test, loc_test)
        image_test = draw_name(image_test, loc_test, pred_name, match_percentage)

    for name, count in detected_faces.items():
        if count >= min_frames:
            consistent_faces[name] = count

    return image_test