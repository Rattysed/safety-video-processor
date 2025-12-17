from .geometry import Car, Polygon, Point

def restore_missing_cars_with_interpolation(frames):
    """
    Восстанавливает пропавшие объекты Car, четко разделяя промежутки на две половины.
    """
    # Собираем все уникальные id
    all_car_ids = set()
    for frame in frames:
        for car in frame:
            all_car_ids.add(car.id)
    
    # Создаем словарь для хранения информации о появлениях каждого автомобиля
    car_appearances = {car_id: [] for car_id in all_car_ids}
    
    # Заполняем информацию о появлениях
    for frame_idx, frame in enumerate(frames):
        for car in frame:
            car_appearances[car.id].append(frame_idx)
    
    # Восстанавливаем кадры
    restored_frames = []
    
    for frame_idx, frame in enumerate(frames):
        restored_frame = []
        current_frame_ids = {car.id for car in frame}
        
        for car_id in all_car_ids:
            if car_id in current_frame_ids:
                # Автомобиль есть в текущем кадре
                restored_frame.append(next(c for c in frame if c.id == car_id))
            else:
                # Ищем ближайшие появления автомобиля
                appearances = car_appearances[car_id]
                
                prev_appearance = None
                next_appearance = None
                
                for app_idx in appearances:
                    if app_idx < frame_idx:
                        prev_appearance = app_idx
                    elif app_idx > frame_idx:
                        next_appearance = app_idx
                        break
                
                # Находим автомобили в этих кадрах
                prev_car = None
                next_car = None
                
                if prev_appearance is not None:
                    for car in frames[prev_appearance]:
                        if car.id == car_id:
                            prev_car = car
                            break
                
                if next_appearance is not None:
                    for car in frames[next_appearance]:
                        if car.id == car_id:
                            next_car = car
                            break
                
                # Восстанавливаем автомобиль
                if prev_car and next_car:
                    # Есть и предыдущий, и следующий кадры
                    # Определяем середину промежутка
                    gap_start = prev_appearance
                    gap_end = next_appearance
                    gap_middle = gap_start + (gap_end - gap_start) // 2
                    
                    if frame_idx <= gap_middle:
                        # В первой половине промежутка - используем полигоны из предыдущего кадра
                        restored_car = Car(
                            wheels=prev_car.wheels,
                            bounding_box=prev_car.bounding_box,
                            id=car_id
                        )
                    else:
                        # Во второй половине промежутка - используем полигоны из следующего кадра
                        restored_car = Car(
                            wheels=next_car.wheels,
                            bounding_box=next_car.bounding_box,
                            id=car_id
                        )
                        
                elif prev_car:
                    # Только предыдущий кадр
                    restored_car = Car(
                        wheels=prev_car.wheels,
                        bounding_box=prev_car.bounding_box,
                        id=car_id
                    )
                    
                elif next_car:
                    # Только следующий кадр
                    restored_car = Car(
                        wheels=next_car.wheels,
                        bounding_box=next_car.bounding_box,
                        id=car_id
                    )
                    
                else:
                    # Никогда не появлялся (не должно происходить)
                    restored_car = Car(
                        wheels=Polygon(),
                        bounding_box=Polygon(),
                        id=car_id
                    )
                
                restored_frame.append(restored_car)
        
        restored_frames.append(restored_frame)
    
    return restored_frames
