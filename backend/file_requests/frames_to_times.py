import cv2


def get_frames_timing_bulk(video, frame_numbers):
    video_path = f"/tmp/{video.request.id}.mp4"

    with open(video_path, "wb") as tmp_file:
        tmp_file.write(video.get_file_data())

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    frame_times = {}
    
    for target_frame in frame_numbers:
        time_seconds = target_frame / fps
        frame_times[target_frame] = round(time_seconds, 3)

    
    cap.release()
    return frame_times


def frame_intervals_to_string(intervals: list[tuple[int]], file) -> str:
    flattened = [item for tup in intervals for item in tup]
    timings_to_seconds = get_frames_timing_bulk(file, flattened)
    
    result = ""
    for interval in intervals:
        result += f"from: {format_time(timings_to_seconds[interval[0]])}, to: {format_time(timings_to_seconds[interval[1]])}; "
    
    return result


def format_time(seconds):
    """Конвертирует время в секундах в читаемый формат"""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{minutes:02d}:{secs:06.3f}"