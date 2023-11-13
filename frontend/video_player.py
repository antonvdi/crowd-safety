import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.geometry("720x1280")
        self.root.title("Video Player")

        self.front_page()

    def front_page(self):
        self.title_label = tk.Label(self.root, text="Crowd Safety Management Video Player", font=("Helvetica", 16))
        self.title_label.pack(pady=20)

        self.upload_button = tk.Button(self.root, text="Upload New Video", command=self.upload_video)
        self.upload_button.pack()

        # Video player components
        self.play_button = None
        self.canvas = None

        self.video_path = None
        self.video_capture = None

    def upload_video(self):
        print("I made it here")
        file_path = filedialog.askopenfilename()
        if file_path.lower().endswith(('.mp4')):
            self.process_upload(file_path)
        else:
            print("Invalid file type. Please select an .mp4 file")

    def process_upload(self, file_path):
        if file_path:
            self.video_path = file_path
            self.video_capture = cv2.VideoCapture(self.video_path)

            # Set window size to 1920x1080
            self.root.geometry("1920x1080")

            # Remove front page components
            self.title_label.pack_forget()
            self.upload_button.pack_forget()

            # Show video player components
            self.play_button = tk.Button(self.root, text="Play", command=self.play_video)
            self.play_button.pack()

            self.canvas = tk.Canvas(self.root, width=1920, height=1080)  # Set canvas size to 1920x1080
            self.canvas.pack()

    def play_video(self):
        if self.video_path:
            while True:
                ret, frame = self.video_capture.read()
                if not ret:
                    break

                # Process the frame if needed

                # Display the frame on the Tkinter window
                self.display_frame(frame)

                # Add scrolling logic here

                # Update the Tkinter window
                self.root.update()

            # Release the video capture object
            self.video_capture.release()

    def display_frame(self, frame):
        # Get the original frame dimensions
        original_height, original_width, _ = frame.shape

        # Scale the frame to fit 1920x1080
        ratio = min(1920 / original_width, 1080 / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        resized_frame = cv2.resize(frame, (new_width, new_height))

        # Convert OpenCV frame to Tkinter-compatible image
        img = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = ImageTk.PhotoImage(img)

        # Update the canvas with the new image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.canvas.image = img

if __name__ == "__main__":
    root = tk.Tk()
    player = VideoPlayer(root)
    root.mainloop()
