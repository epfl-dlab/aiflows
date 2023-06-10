from typing import List
import uuid
import time

def create_unique_id(existing_ids: List[str] = None):
    if existing_ids is None:
        existing_ids = set()

    while True:
        unique_id = str(uuid.uuid4())
        if unique_id not in existing_ids:
            return unique_id


def get_current_datetime_ns():
    time_of_creation_ns = time.time_ns()

    # Convert nanoseconds to seconds and store as a time.struct_time object
    time_of_creation_struct = time.gmtime(time_of_creation_ns // 1000000000)

    # Format the time.struct_time object into a human-readable string
    formatted_time_of_creation = time.strftime("%Y-%m-%d %H:%M:%S", time_of_creation_struct)

    # Append the nanoseconds to the human-readable string
    formatted_time_of_creation += f".{time_of_creation_ns % 1000000000:09d}"

    return formatted_time_of_creation