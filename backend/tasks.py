from file_requests.models import Request, UploadedFile, EditedFile
from time import sleep
from file_requests.cutom_image_handler import ImageHandler
from file_requests.frames_to_times import *

import zipfile
from io import BytesIO

from django.utils import timezone

from backend.celery import app

from ultralytics import YOLO
import numpy as np
import cv2
import tempfile

WHEEL_MODEL_PATH = "../ml/models/wheels_yolov11.pt"

print("типа начали загружаться модели................")
car_model = YOLO('yolov8n.pt') 
wheel_model = YOLO(WHEEL_MODEL_PATH)
print("типа загрузились модели....................")


def detect_wheels(car_crop, frame, wheel_model, x1, x2, y1, y2):
    wheel_results = wheel_model.predict(car_crop, verbose=False, conf=0.25)
                
    wheels_list = []
    
    for w_result in wheel_results:
        w_boxes = w_result.boxes.xyxy.cpu().numpy()
        
        for w_box in w_boxes:
            wx1, wy1, wx2, wy2 = map(int, w_box)
            
            global_wx1 = x1 + wx1
            global_wy1 = y1 + wy1
            global_wx2 = x1 + wx2
            global_wy2 = y1 + wy2
            
            wheels_list.append([global_wx1, global_wy1, global_wx2, global_wy2])

            # Рисуем колеса (зеленым)
            cv2.rectangle(frame, (global_wx1, global_wy1), (global_wx2, global_wy2), (0, 255, 0), 2)
    
    return wheels_list


def process_video_traffic(input_video_path, output_video_path):

    # Классы COCO, относящиеся к транспорту (2: car, 5: bus, 7: truck)
    vehicle_classes = [2, 5, 7] 

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Ошибка открытия видео")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    frame_count = 0
    frames_data = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        frame_data = []

        results = car_model.track(frame, persist=True, classes=vehicle_classes, verbose=False)
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = map(int, box)
                
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)

                car_crop = frame[y1:y2, x1:x2]
                if car_crop.size == 0:
                    continue

                wheels_list = detect_wheels(car_crop, frame, wheel_model, x1, x2, y1, y2)

                car_info = {
                    "tracking_id": int(track_id),
                    "car_bbox": [x1, y1, x2, y2],
                    "wheels_bboxes": wheels_list
                }
                frame_data.append(car_info)
                

                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        print(f"Кадр {frame_count}: Обнаружено {len(frame_data)} машин.")
        frames_data.append({"frame": frame_count, "data": frame_data})
        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    return frames_data



@app.task
def task_process_video(file_id):
    try:
        video = UploadedFile.get_by_id(file_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tfile:
            tfile.write(video.get_file_data()) # Используем ваш метод чтения байтов
            temp_input_path = tfile.name

        print("сохранили видео, путь: ", temp_input_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as out_tfile:
            temp_output_path = out_tfile.name

        print("путь для выходного видео: ", temp_output_path)

        frames_data = process_video_traffic(
            input_video_path=temp_input_path, 
            output_video_path=temp_output_path
        )

        with open(temp_output_path, 'rb') as processed_f:
            processed_video_bytes = processed_f.read()

        # edited_image = image_handler.edit(image.get_file_data())
        print(video)
        print(type(video))
        print("типа обработалось видео")

        file = EditedFile.create_file(video.request, video.uploaded_name, processed_video_bytes)

        example_intervals = [(1, 40), (100, 120)]
        fancy_intervals = frame_intervals_to_string(example_intervals, file)

        file.request.update_file(str(file.request.id) + '.mp4', file.get_file_data())
        file.request.update_timings(fancy_intervals)
        file.request.update_status_done()

    except Exception as e:
        print(e)
        return file_id, False
    return file.id, True
        

@app.task
def task_to_zip(file_ids):
    example_id = None

    buffer_archive = BytesIO()
    with zipfile.ZipFile(buffer_archive, 'w') as archive:
        for file_id, is_edited in file_ids:
            if not is_edited:
                continue

            example_id = file_id
            file = EditedFile.get_by_id(file_id)
            buffer_file = file.get_file_data()
            archive.writestr(file.file.name, buffer_file)
    buffer_archive.seek(0)

    if example_id is None:
        request = UploadedFile.get_by_id(file_ids[0][0]).request
        request.delete()
        return False

    file_example = EditedFile.get_by_id(example_id)
    
    file_example.request.update_file(str(file_example.request.id) + '.zip', buffer_archive.getvalue())
    file_example.request.update_status_done()
    
    file_example.request.update_expiration_date()

    return True


@app.task
def task_clear_requests():
    requests = Request.objects.all()
    for request in requests:
        if request.expiration_date is None:
            request.update_expiration_date()
        elif request.expiration_date < timezone.now():
            request.delete()
    return True
