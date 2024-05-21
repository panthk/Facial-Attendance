import os
import cv2
import time
from datetime import datetime
from faceid import Face, load_image, create_database, detect_faces, save_database, load_database, consistent_faces
from gsheets import setup_gspread, check_and_update_sheet, mark_attendance
from datepopulator import populate_dates

def main():
    faces = load_database()

    if not faces:
        filenames = os.listdir('known_faces')
        images = [load_image(f'known_faces/{filename}') for filename in filenames]
        faces = create_database(filenames, images)
        save_database(faces)

    frame_count = -1
    prev_frame_time = 0
    total_frame_time = []
    detected_faces = {}

    client = setup_gspread()
    sheet_name = "TKS Attendance Tracker"
    worksheet_index = 0
    sheet = client.open(sheet_name).get_worksheet(worksheet_index)
    folder_path = "known_faces"
    check_and_update_sheet(folder_path, sheet)

    # Check and populate dates if needed
    if not sheet.row_values(1):
        date_range = input("Enter the date range (YYYY-MM-DD to YYYY-MM-DD): ")
        populate_dates(sheet, date_range)

    else:
        print("Dates already populated in the Google Sheet.")

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        ret, image = cap.read()
        if ret:
            frame_time = time.time() - prev_frame_time
            prev_frame_time = time.time()
            total_frame_time.append(frame_time)
            image_display = image.copy()

            if frame_count % 1 == 0:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_display = detect_faces(image, faces, detected_faces, threshold=0.6)
                image_display = cv2.cvtColor(image_display, cv2.COLOR_RGB2BGR)
                frame_time = time.time() - prev_frame_time
                prev_frame_time = time.time()
                total_frame_time.append(frame_time)

            cv2.imshow('image', image_display)
            print("Time taken for each frame:", frame_time)

        frame_count += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            total_frame_time.remove(total_frame_time[0])
            print("Average frame time:", sum(total_frame_time) / frame_count)
            break

    today = datetime.now().strftime("%B %d, %Y").replace(", 2024", "")

    if not consistent_faces:
        print("Nothing Added to the Google Sheet")
        
    else:
        for name, count in consistent_faces.items():
            if name != 'Unknown Face Detected':
                mark_attendance(sheet, name)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()