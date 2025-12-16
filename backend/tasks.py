from file_requests.models import Request, UploadedFile, EditedFile
from time import sleep
from file_requests.cutom_image_handler import ImageHandler
from file_requests.frames_to_times import *

import zipfile
from io import BytesIO

from django.utils import timezone

from backend.celery import app

@app.task
def task_process_video(file_id):
    try:
        video = UploadedFile.get_by_id(file_id)

        # edited_image = image_handler.edit(image.get_file_data())

        file = EditedFile.create_file(video.request, video.uploaded_name, video.get_file_data())

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
