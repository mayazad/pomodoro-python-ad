import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import pygame
import os
import sys
from datetime import datetime
import csv
import matplotlib.pyplot as plt
from collections import defaultdict

# === Default Times (will be updated) ===
WORK_SEC = 25 * 60
SHORT_BREAK_SEC = 5 * 60
LONG_BREAK_SEC = 15 * 60
ALERT_FILE = "alert.mp3"

# === App State ===
reps = 0
pomodoro_count = 0
paused = False
timer_running = False
timer_thread = None
pause_event = threading.Event()
dark_mode = False

# === Theme Data ===
themes = {
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "btn_bg": "#f0f0f0",
        "btn_fg": "#000000",
        "progress": "#4caf50"
    },
    "dark": {
        "bg": "#121212",
        "fg": "#ffffff",
        "btn_bg": "#1f1f1f",
        "btn_fg": "#ffffff",
        "progress": "#76ff03"
    }
}

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02}:{secs:02}"

def play_sound():
    sound_path = resource_path(ALERT_FILE)
    if os.path.exists(sound_path):
        pygame.mixer.init()
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

def start_timer():
    global reps, timer_running, timer_thread, paused, WORK_SEC, SHORT_BREAK_SEC, LONG_BREAK_SEC
    if timer_running:
        return

    try:
        WORK_SEC = int(work_entry.get()) * 60
        SHORT_BREAK_SEC = int(short_entry.get()) * 60
        LONG_BREAK_SEC = int(long_entry.get()) * 60
    except ValueError:
        messagebox.showerror("Invalid input", "Enter valid numbers for durations.")
        return

    reps += 1
    paused = False
    pause_event.set()

    if reps % 8 == 0:
        session_time = LONG_BREAK_SEC
        session_label.config(text="Long Break", fg="#03a9f4")
    elif reps % 2 == 0:
        session_time = SHORT_BREAK_SEC
        session_label.config(text="Break", fg="#4caf50")
    else:
        session_time = WORK_SEC
        current_name = session_entry.get().strip() or "Unnamed"
        session_label.config(text=f"{current_name}", fg="#f44336")

    timer_running = True
    timer_thread = threading.Thread(target=countdown, args=(session_time,))
    timer_thread.start()

def countdown(seconds):
    global timer_running, pomodoro_count
    total = seconds
    while seconds > 0 and timer_running:
        pause_event.wait()
        if not timer_running:
            return
        timer_display.config(text=format_time(seconds))
        progress['value'] = 100 * (1 - seconds / total)
        time.sleep(1)
        seconds -= 1

    if timer_running:
        timer_display.config(text="00:00")
        progress['value'] = 100
        play_sound()

        if reps % 2 == 1:
            pomodoro_count += 1
            update_pomodoro_counter()
            save_to_log()

        messagebox.showinfo("Pomodoro", "Time's up!")
        start_timer()

def save_to_log():
    session_name = session_entry.get().strip() or "Untitled"
    duration_min = int(work_entry.get())
    now = datetime.now()
    log_data = [now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), session_name, duration_min]

    with open("pomodoro_log.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        if file.tell() == 0:
            writer.writerow(["Date", "Time", "Session Name", "Duration (min)"])
        writer.writerow(log_data)

def pause_resume_timer():
    global paused
    if not timer_running:
        return
    if paused:
        paused = False
        pause_event.set()
        pause_btn.config(text="Pause")
    else:
        paused = True
        pause_event.clear()
        pause_btn.config(text="Resume")

def reset_timer():
    global reps, timer_running, paused
    timer_running = False
    paused = False
    pause_event.set()
    reps = 0
    timer_display.config(text="00:00")
    session_label.config(text="Timer", fg=themes["dark" if dark_mode else "light"]["fg"])
    progress['value'] = 0
    pause_btn.config(text="Pause")

def update_pomodoro_counter():
    pomodoro_label.config(text=f"🍅 Pomodoros today: {pomodoro_count}")

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    theme_btn.config(text="🌙" if not dark_mode else "☀️")
    apply_theme()
    


def show_weekly_chart():
    if not os.path.exists("pomodoro_log.csv"):
        messagebox.showwarning("No data", "No Pomodoro log file found.")
        return

    week_counts = defaultdict(int)

    with open("pomodoro_log.csv", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                date_obj = datetime.strptime(row["Date"], "%Y-%m-%d")
                weekday = date_obj.strftime("%a")
                week_counts[weekday] += 1
            except Exception:
                continue

    weekdays_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    counts = [week_counts.get(day, 0) for day in weekdays_order]

    plt.figure(figsize=(8, 4))
    plt.bar(weekdays_order, counts, color="#4caf50")
    plt.title("Pomodoros Completed (This Week)")
    plt.ylabel("Count")
    plt.xlabel("Day of Week")
    plt.tight_layout()
    plt.show()

def apply_theme():
    theme = themes["dark" if dark_mode else "light"]
    root.configure(bg=theme["bg"])
    for widget in [session_label, timer_display, credit, pomodoro_label, session_name_label]:
        widget.config(bg=theme["bg"], fg=theme["fg"])
    for btn in [start_btn, pause_btn, reset_btn, theme_btn, exit_btn]:
        btn.config(bg=theme["btn_bg"], fg=theme["btn_fg"], activebackground=theme["btn_bg"], activeforeground=theme["btn_fg"])
    for entry in [work_entry, short_entry, long_entry, session_entry]:
        entry.config(bg=theme["btn_bg"], fg=theme["fg"], insertbackground=theme["fg"])

    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", troughcolor=theme["bg"], background=theme["progress"], thickness=20)
    progress.config(style="TProgressbar")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === GUI SETUP ===
root = tk.Tk()
root.title("Pomodoro Timer")
root.geometry("390x580")
root.resizable(False, False)

# Icon
icon_path = resource_path("icon.ico")
if os.path.exists(icon_path):
    root.iconbitmap(icon_path)

# Fonts
font_large = ("Arial", 36, "bold")
font_medium = ("Arial", 14)
font_small = ("Arial", 10)

# UI Elements
session_label = tk.Label(root, text="Timer", font=font_medium)
session_label.pack(pady=6)

timer_display = tk.Label(root, text="00:00", font=font_large)
timer_display.pack(pady=6)

progress = ttk.Progressbar(root, length=250, mode="determinate")
progress.pack(pady=6)

# Duration Inputs
input_frame = tk.Frame(root)
tk.Label(input_frame, text="Work (min):").grid(row=0, column=0, padx=5)
tk.Label(input_frame, text="Short Break:").grid(row=0, column=2, padx=5)
tk.Label(input_frame, text="Long Break:").grid(row=0, column=4, padx=5)

work_entry = tk.Entry(input_frame, width=4)
work_entry.insert(0, "25")
work_entry.grid(row=0, column=1)

short_entry = tk.Entry(input_frame, width=4)
short_entry.insert(0, "5")
short_entry.grid(row=0, column=3)

long_entry = tk.Entry(input_frame, width=4)
long_entry.insert(0, "15")
long_entry.grid(row=0, column=5)
input_frame.pack(pady=6)

# Session Name
session_name_label = tk.Label(root, text="Session Name:", font=font_small)
session_name_label.pack(pady=2)

session_entry = tk.Entry(root, width=30)
session_entry.insert(0, "Study / Task Name")
session_entry.pack(pady=4)

# Buttons
start_btn = tk.Button(root, text="Start", font=font_medium, command=start_timer)
start_btn.pack(pady=4)

pause_btn = tk.Button(root, text="Pause", font=font_medium, command=pause_resume_timer)
pause_btn.pack(pady=4)

reset_btn = tk.Button(root, text="Reset", font=font_medium, command=reset_timer)
reset_btn.pack(pady=4)

theme_btn = tk.Button(root, text="🌙", font=("Arial", 12), width=4, command=toggle_theme)
theme_btn.pack(pady=4)

stats_btn = tk.Button(root, text="📊 Weekly Stats", font=font_medium, command=show_weekly_chart)
stats_btn.pack(pady=4)

exit_btn = tk.Button(root, text="Exit", font=font_medium, command=root.destroy)
exit_btn.pack(pady=6)

pomodoro_label = tk.Label(root, text="🍅 Pomodoros today: 0", font=font_small)
pomodoro_label.pack(pady=6)

credit = tk.Label(root, text="GitHub 'mayazad'", font=font_small)
credit.pack(pady=6)

apply_theme()
root.mainloop()