import os
import cv2
import face_recognition
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def load_image(path):
    image = cv2.imread(path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  #1
    return image

def show_image(image):
    plt.imshow(image)
    plt.xticks([])
    plt.yticks([])
    plt.show()
    return

filenames = os.listdir('templates')
images = [load_image(f'templates/{filename}') for filename in filenames]

show_image(images[0])

class Face:
    def __init__(self, bounding_box, cropped_face, name, feature_vector):
        self.bounding_box = bounding_box      #1
        self.cropped_face = cropped_face      #2
        self.name = name                      #3
        self.feature_vector = feature_vector  #4

def create_database(filenames, images):
    faces = []
    for filename, image in tqdm(zip(filenames, images), total=len(filenames)):
        locs = face_recognition.face_locations(image, model='hog')
        
        if not locs:
            print(f"No face detected in {filename}. Skipping.")
            continue
        
        loc = locs[0]
        vec = face_recognition.face_encodings(image, [loc], num_jitters=20)[0]
        
        top, right, bottom, left = loc
        cropped_face = image[top:bottom, left:right]
        
        face = Face(bounding_box=loc, cropped_face=cropped_face, 
                    name=filename.split('.')[0], feature_vector=vec)
        
        faces.append(face)
    
    return faces

faces = create_database(filenames, images)

if faces:
    show_image(faces[0].cropped_face)
else:
    print("No faces detected in any images.")




# image_test = load_image('test/test1.jpg')
# show_image(image_test)

def detect_faces(image_test, faces, threshold=0.6):    #1
    locs_test = face_recognition.face_locations(image_test, model='hog')  #2
    vecs_test = face_recognition.face_encodings(image_test, locs_test, 
                                                num_jitters=1)            #3
    
    for loc_test, vec_test in zip(locs_test, vecs_test):    #4
        distances = []
        for face in faces:
            distance = face_recognition.face_distance([vec_test], 
                                                      face.feature_vector)  #5
            distances.append(distance)
            
        if np.min(distances) > threshold:  #6
            pred_name = 'unknown'
        else:
            pred_index = np.argmin(distances)    #7
            pred_name = faces[pred_index].name
        
        image_test = draw_bounding_box(image_test, loc_test)
        image_test = draw_name(image_test, loc_test, pred_name)
    
    return image_test

def draw_bounding_box(image_test, loc_test):
    top, right, bottom, left = loc_test
    
    line_color = (0, 255, 0)
    line_thickness = 2
    
    cv2.rectangle(image_test, (left, top), (right, bottom), 
                  line_color, line_thickness)

    return image_test

def draw_name(image_test, loc_test, pred_name):
    top, right, bottom, left = loc_test 
    
    font_style = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    font_color = (0, 0, 255)
    font_thickness = 3
    
    text_size, _ = cv2.getTextSize(pred_name, font_style, font_scale, font_thickness)
    
    bg_top_left = (left, top-text_size[1])
    bg_bottom_right = (left+text_size[0], top)
    line_color = (0, 255, 0)
    line_thickness = -1

    cv2.rectangle(image_test, bg_top_left, bg_bottom_right, 
                  line_color, line_thickness)   

    cv2.putText(image_test, pred_name, (left, top), font_style, font_scale, font_color, font_thickness)
    
    return image_test

# show_image(detect_faces(image_test, faces))