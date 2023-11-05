import cv2
import os
from tqdm import tqdm

# Specify the path to the folder containing your frame images
file_name = ""
frame_folder = "content\\target\\temp\\"+file_name

# Define the output video file name and parameters
output_video_path = "content\\temp_video\\output_video.mp4"
frame_rate = 30  # Adjust the frame rate as needed
frame_size = (1280, 720)  # Set the frame size to match your images

# Get the list of frame files sorted by frame number
frame_files = sorted([f for f in os.listdir(frame_folder) if f.endswith(".png")], key=lambda x: int(os.path.splitext(x)[0]))

target_frame = len(frame_files)
# target_frame = x (frame to target)
target_filename = f"{target_frame:04}.png"

# Create a VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_video_path, fourcc, frame_rate, frame_size)

# Create a tqdm progress bar to track the processing
progress_bar = tqdm(total=target_frame, unit="frame")

# Loop through the frame images and write them to the video
for frame_file in frame_files:
    frame_path = os.path.join(frame_folder, frame_file)
    frame = cv2.imread(frame_path)
    out.write(frame)
    progress_bar.update(1)  # Update the progress bar
    if(frame_file == target_filename) : break

# Release the VideoWriter object
out.release()

# Close the tqdm progress bar
progress_bar.close()

print("Video created successfully.")