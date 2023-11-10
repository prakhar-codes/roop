import threading
from typing import Any, Optional, List
import insightface
import numpy

import roop.globals
from roop.typing import Frame, Face

FACE_ANALYSER = None
THREAD_LOCK = threading.Lock()


def get_face_analyser() -> Any:
    global FACE_ANALYSER

    with THREAD_LOCK:
        if FACE_ANALYSER is None:
            FACE_ANALYSER = insightface.app.FaceAnalysis(name='buffalo_l', providers=roop.globals.execution_providers)
            FACE_ANALYSER.prepare(ctx_id=0)
    return FACE_ANALYSER


def clear_face_analyser() -> Any:
    global FACE_ANALYSER

    FACE_ANALYSER = None


def get_one_face(frame: Frame, position: int = 0) -> Optional[Face]:
    all_faces = get_all_faces(frame)
    if all_faces:
        try:
            return all_faces[position]
        except IndexError:
            return all_faces[-1]
    return None


def get_all_faces(frame: Frame) -> Optional[List[Face]]:
    try:
        return get_face_analyser().get(frame)
    except ValueError:
        return None


def find_similar_face(frame: Frame, reference_face: Face) -> Optional[Face]:
    all_faces = get_all_faces(frame)
    if len(all_faces)==1:
        if(is_similar_face(all_faces[0], reference_face)): return all_faces[0]
    elif len(all_faces) > 1:
        face_distances = []
        for face in all_faces:
            face_distances.append(get_faces_distance(face, reference_face))
        return all_faces[face_distances.index(min(face_distances))]
    return None

def is_similar_face(face: Face, reference_face: Face) -> bool:
    if(get_faces_distance(face, reference_face)<roop.globals.similar_face_distance):
        return True
    else:
        return False

def get_faces_distance(face: Face, reference_face: Face) -> int:
    if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
        distance = numpy.sum(numpy.square(face.normed_embedding - reference_face.normed_embedding))
        return distance
    else:
        return numpy.nan