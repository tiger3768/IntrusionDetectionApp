import os
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from database_operations import MongoDBOperations
from motion_detection import MotionDetection
from io import BytesIO
from PIL import Image, ImageTk
import hashlib

class IDSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IDS")
        self.root.attributes('-fullscreen', True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.login_frame = tk.Frame(self.root)
        self.register_frame = tk.Frame(self.root)
        self.stream_frame = tk.Frame(self.root)

        self.current_frame = self.login_frame
        self.current_frame.pack(expand=True, fill=tk.BOTH)

        self.create_login_widgets()
        self.create_register_widgets()
        self.create_stream_widgets()

        self.video_label = tk.Label(self.stream_frame)
        self.video_label.pack()

        self.streams_data = {}

        self.db_operations = MongoDBOperations()
        self.users_collection = self.db_operations.get_users_collection()
        self.alerts_collection = self.db_operations.get_alerts_collection()

        self.view_streams_button = tk.Button(root, text="View Streams Data", command=self.view_streams_data, state=tk.DISABLED)
        self.view_streams_button.pack()

        self.motion_detection = MotionDetection()

    def create_login_widgets(self):
        login_label = tk.Label(self.login_frame, text="Login", font=("Arial Bold", 20))
        login_label.pack()

        username_label = tk.Label(self.login_frame, text="Username:", font=("Arial", 14))
        username_label.pack()
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 14))
        self.username_entry.pack()

        password_label = tk.Label(self.login_frame, text="Password:", font=("Arial", 14))
        password_label.pack()
        self.password_entry = tk.Entry(self.login_frame, show="*", font=("Arial", 14))
        self.password_entry.pack()

        login_button = tk.Button(self.login_frame, text="Login", command=self.login_user, font=("Arial", 14))
        login_button.pack()

        switch_to_register_button = tk.Button(self.login_frame, text="Switch to Register", command=self.switch_to_register, font=("Arial", 14))
        switch_to_register_button.pack()

    def create_register_widgets(self):
        register_label = tk.Label(self.register_frame, text="Register", font=("Arial Bold", 20))
        register_label.pack()

        new_username_label = tk.Label(self.register_frame, text="Username:", font=("Arial", 14))
        new_username_label.pack()
        self.new_username_entry = tk.Entry(self.register_frame, font=("Arial", 14))
        self.new_username_entry.pack()

        new_password_label = tk.Label(self.register_frame, text="Password:", font=("Arial", 14))
        new_password_label.pack()
        self.new_password_entry = tk.Entry(self.register_frame, show="*", font=("Arial", 14))
        self.new_password_entry.pack()

        register_button = tk.Button(self.register_frame, text="Register", command=self.register_user, font=("Arial", 14))
        register_button.pack()

        switch_to_login_button = tk.Button(self.register_frame, text="Switch to Login", command=self.switch_to_login, font=("Arial", 14))
        switch_to_login_button.pack()

    def create_stream_widgets(self):
        stream_label = tk.Label(self.stream_frame, text="Enter Phone Number and Choose Stream Option", font=("Arial Bold", 16))
        stream_label.pack()

        phone_label = tk.Label(self.stream_frame, text="Phone Number:", font=("Arial", 14))
        phone_label.pack()
        self.phone_entry = tk.Entry(self.stream_frame, font=("Arial", 14))
        self.phone_entry.pack()

        self.stream_option = tk.StringVar()
        self.stream_option.set("Webcam")
        stream_link_radio = ttk.Radiobutton(self.stream_frame, text="Stream Link", variable=self.stream_option, value="Stream Link", command=self.enable_stream_link_entry)
        stream_link_radio.pack()

        webcam_radio = ttk.Radiobutton(self.stream_frame, text="Webcam", variable=self.stream_option, value="Webcam", command=self.disable_stream_link_entry)
        webcam_radio.pack()

        self.stream_link_entry = tk.Entry(self.stream_frame, state=tk.DISABLED, font=("Arial", 14))
        self.stream_link_entry.pack()

        process_button = tk.Button(self.stream_frame, text="Process Stream", command=self.process_stream, font=("Arial", 14))
        process_button.pack()

    def enable_stream_link_entry(self):
        self.stream_link_entry.config(state=tk.NORMAL)

    def disable_stream_link_entry(self):
        self.stream_link_entry.delete(0, tk.END)
        self.stream_link_entry.config(state=tk.DISABLED)

    def process_stream(self):
        try:
            self.validate_data()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        stream_option = self.stream_option.get()
        phone_number = self.phone_entry.get()
        stream_link = self.stream_link_entry.get() if stream_option == "Stream Link" else "Webcam"

        if stream_option not in ["Stream Link", "Webcam"]:
            messagebox.showerror("Error", "Invalid stream option selected.")
            return
        
        stream_source = 0 if stream_option == "Webcam" else stream_link
        
        if not phone_number:
            messagebox.showerror("Error", "Please set a receiver number in the settings.")
            return

        self.motion_detection.start_motion_detection(stream_source, self.username_entry.get(),
                                                      phone_number, stream_option,
                                                      stream_link,
                                                      self.db_operations.save_alert_data, self.db_operations.get_gridfs())
        
    def login_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        user = self.users_collection.find_one({"username": username})

        if user:
            stored_password = user["password"]
            salt = user["salt"]
            entered_password = hashlib.sha256(password.encode() + salt).hexdigest()

            if stored_password == entered_password:
                messagebox.showinfo("Success", "Login successful!")
                self.switch_to_stream()
            else:
                messagebox.showerror("Error", "Invalid username or password.")
        else:
            messagebox.showerror("Error", "Invalid username or password.")


    def register_user(self):
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        existing_user = self.users_collection.find_one({"username": username})

        if existing_user:
            messagebox.showerror("Error", "Username already exists. Please choose a different username.")
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Passwords should be at least 6 characters long.")
            return

        salt = os.urandom(32)
        hashed_password = hashlib.sha256(password.encode() + salt).hexdigest()

        self.users_collection.insert_one({"username": username, "password": hashed_password, "salt": salt})
        messagebox.showinfo("Success", "Registration successful!")

        self.new_username_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)

    

    def view_streams_data(self):
        username = self.username_entry.get()
        try:
            self.streams_data = self.db_operations.fetch_streams_data(username)
        except Exception as e:
            messagebox.showerror("Error while loading data")

        if username in self.streams_data:
            stream_data = self.streams_data[username]
            stream_data_window = tk.Toplevel(self.root)
            stream_data_window.title(f"Stream Data for {username}")

            text_area = scrolledtext.ScrolledText(stream_data_window, width=100, height=40)
            text_area.pack()

            photo_images = []

            for date, data_list in stream_data.items():
                text_area.insert(tk.END, f"Date: {date}\n\n")
                for data in data_list:
                    text_area.insert(tk.END, f"Stream Type: {data['stream_option']}\n")
                    text_area.insert(tk.END, f"Stream Link: {data['stream_link']}\n")
                    text_area.insert(tk.END, "Alerts:\n")
                    for alert in data['alerts']:
                        text_area.insert(tk.END, f"\tTimestamp: {alert['timestamp']}\n")
                        screenshot_id = alert['screenshot']
                        if screenshot_id:
                            try:
                                image_data = self.db_operations.get_image_data(screenshot_id)
                                img = Image.open(BytesIO(image_data))
                                img = img.resize((500, 500), Image.LANCZOS)
                                photo = ImageTk.PhotoImage(img)
                                text_area.image_create(tk.END, image=photo)
                                text_area.insert(tk.END, '\n')
                                photo_images.append(photo)
                            except Exception as e:
                                print(f"Error loading image: {e}")
                                text_area.insert(tk.END, "Error loading image\n")
                        else:
                            text_area.insert(tk.END, "No screenshot available\n")
                    text_area.insert(tk.END, "\n")
                text_area.insert(tk.END, "\n\n")

            self.photo_images = photo_images

        else:
            messagebox.showinfo("Info", "No stream data available.")


    def validate_data(self):
        phone_number = self.phone_entry.get()
        stream_option = self.stream_option.get()

        if not phone_number:
            raise ValueError("Please enter a phone number.")

        if stream_option == "Stream Link":
            stream_link = self.stream_link_entry.get()
            if not stream_link:
                raise ValueError("Please enter a stream link.")
            
    def switch_frame(self, new_frame):
        self.current_frame.pack_forget()
        self.current_frame = new_frame
        self.current_frame.pack(expand=True, fill=tk.BOTH)

    def switch_to_register(self):
        self.switch_frame(self.register_frame)

    def switch_to_login(self):
        self.switch_frame(self.login_frame)

    def switch_to_stream(self):
        self.switch_frame(self.stream_frame)
        self.view_streams_button.config(state=tk.NORMAL)

    def on_closing(self):
        self.motion_detection.stop_motion_detection()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = IDSApp(root)
    root.mainloop()