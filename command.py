import tkinter as tk
import subprocess

def run_command():
    type_entry = ""
    others = ""
    if face_swapper_var.get():
        type_entry+="face_swapper "
    if face_enhancer_var.get():
        type_entry+="face_enhancer "
    if skip_audio_var.get():
        others+="--skip-audio "
    if keep_fps_var.get():
        others+="--keep-fps "
    if only_swapped_frames_var.get():
        others+="--only-swapped-frames "
    if use_temp_var.get():
        others+="--use-temp "
    if all_faces_var.get():
        others+="--all-faces "
    if many_faces_var.get():
        others+="--many-faces "
    if distance_entry.get():
        others+="--similar-face-distance "+distance_entry.get()
    if from_entry.get() != 'start':
        others+='--from-frame '+from_entry.get()
    if to_entry.get() != 'end':
        others+='--to-frame '+to_entry.get()
    command = f"python run.py --target {target_entry.get()} --source {source_entry.get()} -o {output_entry.get()} --execution-provider {processor_entry.get()} --frame-processor {type_entry} {others}"

    app.destroy()
    
    print(command+"\n")

    # Open a system shell and run the command
    subprocess.run(command, shell=True, text=True, check=True)


app = tk.Tk()
app.title("Face Swapper")

app.geometry("600x600")

# Create input fields and labels
tk.Label(app, text="Target:").pack()
target_entry = tk.Entry(app, width=70)
target_entry.insert(0, "content\\target\\")
target_entry.pack()

tk.Label(app, text="Source:").pack()
source_entry = tk.Entry(app, width=70)
source_entry.insert(0, "\"C:\\Program Files\\JetBrains\\IntelliJ IDEA 2022.2.3\\ai\\original\\\"")
source_entry.pack()

tk.Label(app, text="Output:").pack()
output_entry = tk.Entry(app, width=70)
output_entry.insert(0, "content\\output\\swapped.")
output_entry.pack()

tk.Label(app, text="Execution Type:").pack()
face_swapper_var = tk.IntVar(value=1)
face_swapper_checkbox = tk.Checkbutton(app, text="face_swapper", variable=face_swapper_var)
face_swapper_checkbox.pack()
face_enhancer_var = tk.IntVar()
face_enhancer_checkbox = tk.Checkbutton(app, text="face_enhancer", variable=face_enhancer_var)
face_enhancer_checkbox.pack()

# DirectML - dml , CUDA - cuda, OpenVino - openvino
tk.Label(app, text="Execution Provider:").pack()
processor_entry = tk.Entry(app)
processor_entry.insert(0, "dml")
processor_entry.pack()

tk.Label(app, text="Similar Face Distance:").pack()
distance_entry = tk.Entry(app)
distance_entry.insert(0, "2.0")
distance_entry.pack()

tk.Label(app, text="Others:").pack()
all_faces_var = tk.IntVar()
all_faces_checkbox = tk.Checkbutton(app, text="all-faces", variable=all_faces_var)
all_faces_checkbox.pack()
many_faces_var = tk.IntVar()
many_faces_checkbox = tk.Checkbutton(app, text="many-faces", variable=many_faces_var)
many_faces_checkbox.pack()
skip_audio_var = tk.IntVar()
skip_audio_checkbox = tk.Checkbutton(app, text="skip-audio", variable=skip_audio_var)
skip_audio_checkbox.pack()
keep_fps_var = tk.IntVar()
keep_fps_checkbox = tk.Checkbutton(app, text="keep-fps", variable=keep_fps_var)
keep_fps_checkbox.pack()
only_swapped_frames_var = tk.IntVar()
only_swapped_frames_checkbox = tk.Checkbutton(app, text="only-swapped-frames", variable=only_swapped_frames_var)
only_swapped_frames_checkbox.pack()
use_temp_var = tk.IntVar()
use_temp_checkbox = tk.Checkbutton(app, text="use-temp", variable=use_temp_var)
use_temp_checkbox.pack()

tk.Label(app, text="From Frame:").pack()
from_entry = tk.Entry(app)
from_entry.insert(0, "start")
from_entry.pack()

tk.Label(app, text="To Frame:").pack()
to_entry = tk.Entry(app)
to_entry.insert(0, "end")
to_entry.pack()

# Create a button to run the command
run_button = tk.Button(app, text="Run Command", command=run_command)
run_button.pack()

app.mainloop()