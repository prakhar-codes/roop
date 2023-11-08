from typing import Any, List, Callable
import cv2
import insightface
import threading
import os
import numpy as np
from tqdm import tqdm

import roop.globals
import roop.processors.frame.core
from roop.core import update_status
from roop.face_analyser import get_one_face, get_all_faces, find_similar_face, is_similar_face, get_faces_distance
from roop.face_reference import get_face_reference, set_face_reference, clear_face_reference
from roop.typing import Face, Frame
from roop.utilities import conditional_download, resolve_relative_path, is_image, is_video,get_faces_directory_path, get_face_path, clean_faces_path

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()
NAME = 'ROOP.FACE-SWAPPER'


def get_face_swapper() -> Any:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            model_path = resolve_relative_path('../models/inswapper_128.onnx')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=roop.globals.execution_providers)
    return FACE_SWAPPER


def clear_face_swapper() -> None:
    global FACE_SWAPPER

    FACE_SWAPPER = None


def pre_check() -> bool:
    download_directory_path = resolve_relative_path('../models')
    conditional_download(download_directory_path, ['https://huggingface.co/CountFloyd/deepfake/resolve/main/inswapper_128.onnx'])
    return True


def pre_start() -> bool:
    if not is_image(roop.globals.source_path):
        update_status('Select an image for source path.', NAME)
        return False
    elif not get_one_face(cv2.imread(roop.globals.source_path)):
        update_status('No face in source path detected.', NAME)
        return False
    if not is_image(roop.globals.target_path) and not is_video(roop.globals.target_path):
        update_status('Select an image or video for target path.', NAME)
        return False
    return True


def post_process() -> None:
    clear_face_swapper()
    clear_face_reference()


def swap_face(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
    return get_face_swapper().get(temp_frame, target_face, source_face, paste_back=True)


def process_frame(source_face: Face, reference_face: Face, temp_frame: Frame) -> Frame:
    if roop.globals.all_faces:
        all_faces = get_all_faces(temp_frame)
        if all_faces:
            for target_face in all_faces:
                temp_frame = swap_face(source_face, target_face, temp_frame)
    else:
        target_face = find_similar_face(temp_frame, reference_face)
        if target_face:
            temp_frame = swap_face(source_face, target_face, temp_frame)
        elif roop.globals.only_swapped_frames:
            temp_frame = None
    return temp_frame


def process_frames(source_path: str, temp_frame_paths: List[str], update: Callable[[], None]) -> None:
    source_face = get_one_face(cv2.imread(source_path))
    reference_face = None if roop.globals.all_faces else get_face_reference()
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        result = process_frame(source_face, reference_face, temp_frame)
        if result is None and roop.globals.only_swapped_frames:
            os.remove(temp_frame_path)
        else:
            cv2.imwrite(temp_frame_path, result)
        if update:
            update()

def write_face(target_path: str, frame: Frame, face: Face, position: int) -> bool:
    if face.bbox is not None:
        x1, y1, x2, y2 = map(abs, face.bbox.astype(int))
        face_image = frame[min(y1,y2):max(y1,y2), min(x1,x2):max(x1,x2)]
        face_path = get_face_path(target_path, position)
        if not face_image is None and face_image.size>0:
            cv2.imwrite(face_path, face_image)
            print("Face",position,"saved at", face_path)
            return True
    return False

def process_image(source_path: str, target_path: str, output_path: str) -> None:
    source_face = get_one_face(cv2.imread(source_path))
    target_frame = cv2.imread(target_path)
    if(roop.globals.many_faces):
        all_faces = get_all_faces(target_frame)
        position = 0
        for face in all_faces:
            if(write_face(target_path, target_frame, face, position)): position += 1
        print(position, " face(s) found") 
        roop.globals.reference_face_position = int(input("Enter index of face to be swapped: "))    
    reference_face = None if roop.globals.all_faces else get_one_face(target_frame, roop.globals.reference_face_position)
    result = process_frame(source_face, reference_face, target_frame)
    cv2.imwrite(output_path, result)
    clean_faces_path(target_path)

def process_video(target_path: str, source_path: str, temp_frame_paths: List[str]) -> None:
    if(roop.globals.many_faces):
        detected_faces = []
        detected_frame_number = []
        detected_pos = []
        num_of_faces = int(input("Enter number of faces in the video : "))
        num_of_frames = len(temp_frame_paths)
        print(f"There are {num_of_frames} frames in the video")
        user_input = input("Enter the frame number upto which face needs to be detected : ")
        try:
            frames_to_be_detected = int(user_input)  # Try to convert user input to an integer
            if 1 <= frames_to_be_detected <= num_of_frames:
                pass  
            else:
                frames_to_be_detected = num_of_frames
        except ValueError:
            frames_to_be_detected = num_of_frames
        distance_values = np.full((num_of_faces, num_of_frames, num_of_faces), np.nan, dtype=float)
        # to find*frames*found
        position = 0
        progress_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
        progress_bar = tqdm(total=frames_to_be_detected, unit="frame", desc='Finding faces', dynamic_ncols=True, bar_format=progress_bar_format)
        for num_frame, temp_frame_path in enumerate(temp_frame_paths):
            progress_bar.update(1)
            temp_frame = cv2.imread(temp_frame_path)
            all_faces = get_all_faces(temp_frame)
            if(len(all_faces)>num_of_faces):
                raise RuntimeError("Number of faces found in a frame exceeds the number of faces given by user.")
            for num_face, face in enumerate(all_faces):
                isNewFace = True
                for num_ref, reference_face in enumerate(detected_faces):
                    if(is_similar_face(face, reference_face)):
                        isNewFace = False
                    distance_values[num_ref][num_frame][num_face] = get_faces_distance(face, reference_face)
                if(isNewFace and position < num_of_faces):
                    if(not write_face(target_path, temp_frame, face, position)) : continue
                    detected_faces.append(face)
                    detected_frame_number.append(num_frame+1)
                    detected_pos.append(num_face)
                    position+=1
            if num_frame + 1 >= frames_to_be_detected: break
        progress_bar.close()
        print(position, " face(s) found")
        distance_values = np.sort(distance_values, axis=-1)
        # print(distance_values)
        for i, element in enumerate(distance_values):
            faces_directory_path = get_faces_directory_path(target_path)
            face_value_path = os.path.join(faces_directory_path, f'face{i}.txt')
            os.makedirs(os.path.dirname(face_value_path), exist_ok=True)
            np.savetxt(face_value_path, element, fmt='%f', delimiter='\t')
            min_values = np.nanmin(element, axis=0)
            val1 = np.max(min_values)
            max_values = np.nanmax(element, axis=0)
            val2 = np.min(max_values)
            for j, (min_val, max_val) in enumerate(zip(min_values, max_values)):
                print(f'For face{i} : min distance = {min_val}, max distance = {max_val} from {j}th nearest face')
            # print("Face ",i," lies in range : ",val1, val2)
        selected_face = int(input("Enter position of face to be swapped : "))
        roop.globals.reference_frame_number = detected_frame_number[selected_face]
        roop.globals.reference_face_position = detected_pos[selected_face]
        roop.globals.similar_face_distance = float(input("Enter distance value : "))
        print("REFERENCE FRAME NUMBER : ",roop.globals.reference_frame_number," REFERENCE FACE POSITION : ", roop.globals.reference_face_position)
    if not roop.globals.all_faces and not get_face_reference():
        reference_frame = cv2.imread(temp_frame_paths[roop.globals.reference_frame_number])
        reference_face = get_one_face(reference_frame, roop.globals.reference_face_position)
        set_face_reference(reference_face)
    roop.processors.frame.core.process_video(source_path, temp_frame_paths, process_frames)
    clean_faces_path(target_path)
