import cv2
import mediapipe as mp
import customtkinter as ctk
import math
import time
import subprocess
import threading
import queue
from tkinter import messagebox


# ==========================================================
# BASIC SETUP
# ==========================================================

mp_pose = mp.solutions.pose


# ==========================================================
# WINDOWS VOICE SYSTEM
# ==========================================================

voice_queue = queue.Queue()

last_voice = ""
last_voice_time = 0


def windows_speak(text):

    try:

        safe_text = text.replace("'", "''")

        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$voice.Rate = 0; "
            "$voice.Volume = 100; "
            f"$voice.Speak('{safe_text}'); "
            "$voice.Dispose()"
        )

        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:

        print("VOICE ERROR:", e)


def voice_worker():

    while True:

        text = voice_queue.get()

        if text is None:
            break

        print("SPEAKING:", text)

        windows_speak(text)

        voice_queue.task_done()


voice_thread = threading.Thread(
    target=voice_worker,
    daemon=True
)

voice_thread.start()


def speak(text):

    global last_voice
    global last_voice_time

    now = time.time()

    # Prevent same message from repeating too quickly
    if text == last_voice and now - last_voice_time < 3:
        return

    print("VOICE:", text)

    voice_queue.put(text)

    last_voice = text
    last_voice_time = now


# ==========================================================
# ANGLE CALCULATION
# ==========================================================

def calculate_angle(a, b, c):

    angle = math.degrees(
        math.atan2(c.y - b.y, c.x - b.x)
        -
        math.atan2(a.y - b.y, a.x - b.x)
    )

    angle = abs(angle)

    if angle > 180:
        angle = 360 - angle

    return angle


# ==========================================================
# DRAW SELECTED LANDMARKS
# ==========================================================

def draw_connection(frame, a, b):

    h, w, _ = frame.shape

    x1 = int(a.x * w)
    y1 = int(a.y * h)

    x2 = int(b.x * w)
    y2 = int(b.y * h)

    cv2.line(
        frame,
        (x1, y1),
        (x2, y2),
        (0, 255, 255),
        3
    )


def draw_point(frame, point):

    h, w, _ = frame.shape

    x = int(point.x * w)
    y = int(point.y * h)

    cv2.circle(
        frame,
        (x, y),
        7,
        (0, 255, 255),
        -1
    )


# ==========================================================
# WORKOUT
# ==========================================================

def workout(exercise, username):

    global last_voice
    global last_voice_time

    last_voice = ""
    last_voice_time = 0

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        messagebox.showerror(
            "Camera Error",
            "Camera could not be opened."
        )

        return

    pose = mp_pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )

    # ======================================================
    # WORKOUT VARIABLES
    # ======================================================

    counter = 0
    stage = None

    good_reps = 0
    bad_reps = 0

    form_status = "READY"
    feedback = "Start exercise"

    # Starting voice
    speak(f"Starting {exercise}")

    # ======================================================
    # CAMERA LOOP
    # ======================================================

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # Mirror camera
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB
        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # MediaPipe
        result = pose.process(rgb)

        angle = 0

        # ==================================================
        # PERSON DETECTED
        # ==================================================

        if result.pose_landmarks:

            lm = result.pose_landmarks.landmark

            # ==================================================
            # SQUAT
            # ==================================================

            if exercise == "Squat":

                lh = lm[
                    mp_pose.PoseLandmark.LEFT_HIP
                ]

                lk = lm[
                    mp_pose.PoseLandmark.LEFT_KNEE
                ]

                la = lm[
                    mp_pose.PoseLandmark.LEFT_ANKLE
                ]

                rh = lm[
                    mp_pose.PoseLandmark.RIGHT_HIP
                ]

                rk = lm[
                    mp_pose.PoseLandmark.RIGHT_KNEE
                ]

                ra = lm[
                    mp_pose.PoseLandmark.RIGHT_ANKLE
                ]

                # Calculate both knee angles
                left_angle = calculate_angle(
                    lh,
                    lk,
                    la
                )

                right_angle = calculate_angle(
                    rh,
                    rk,
                    ra
                )

                angle = (
                    left_angle + right_angle
                ) / 2

                # Draw squat landmarks
                for a, b in [
                    (lh, lk),
                    (lk, la),
                    (rh, rk),
                    (rk, ra)
                ]:

                    draw_connection(
                        frame,
                        a,
                        b
                    )

                for point in [
                    lh,
                    lk,
                    la,
                    rh,
                    rk,
                    ra
                ]:

                    draw_point(
                        frame,
                        point
                    )

                # ------------------------------------------
                # SQUAT DOWN
                # ------------------------------------------

                if angle < 100:

                    stage = "DOWN"

                    if angle < 75:

                        form_status = "FIX FORM"

                        feedback = (
                            "Do not go too low"
                        )

                        speak(
                            "Do not go too low"
                        )

                    else:

                        form_status = "GOOD FORM"

                        feedback = (
                            "Good squat position"
                        )

                # ------------------------------------------
                # SQUAT UP
                # ------------------------------------------

                if angle > 160:

                    if stage == "DOWN":

                        counter += 1

                        if form_status == "GOOD FORM":

                            good_reps += 1

                            feedback = "Good squat"

                            speak(
                                f"Good. {counter} squat"
                            )

                        else:

                            bad_reps += 1

                            feedback = (
                                "Fix your squat form"
                            )

                            speak(
                                "Fix your squat form"
                            )

                    stage = "UP"

            # ==================================================
            # BICEP CURL
            # ==================================================

            elif exercise == "Bicep Curl":

                ls = lm[
                    mp_pose.PoseLandmark.LEFT_SHOULDER
                ]

                le = lm[
                    mp_pose.PoseLandmark.LEFT_ELBOW
                ]

                lw = lm[
                    mp_pose.PoseLandmark.LEFT_WRIST
                ]

                rs = lm[
                    mp_pose.PoseLandmark.RIGHT_SHOULDER
                ]

                re = lm[
                    mp_pose.PoseLandmark.RIGHT_ELBOW
                ]

                rw = lm[
                    mp_pose.PoseLandmark.RIGHT_WRIST
                ]

                # Calculate elbow angles
                left_angle = calculate_angle(
                    ls,
                    le,
                    lw
                )

                right_angle = calculate_angle(
                    rs,
                    re,
                    rw
                )

                angle = (
                    left_angle + right_angle
                ) / 2

                # Draw arm connections
                for a, b in [
                    (ls, le),
                    (le, lw),
                    (rs, re),
                    (re, rw)
                ]:

                    draw_connection(
                        frame,
                        a,
                        b
                    )

                # Draw arm points
                for point in [
                    ls,
                    le,
                    lw,
                    rs,
                    re,
                    rw
                ]:

                    draw_point(
                        frame,
                        point
                    )

                # ------------------------------------------
                # ARM DOWN
                # ------------------------------------------

                if angle > 150:

                    stage = "DOWN"

                    form_status = "GOOD FORM"

                    feedback = (
                        "Ready to curl"
                    )

                # ------------------------------------------
                # ARM MIDDLE
                # ------------------------------------------

                elif 60 <= angle <= 150:

                    form_status = "FIX FORM"

                    feedback = (
                        "Curl your arm properly"
                    )

                    speak(
                        "Curl your arm properly"
                    )

                # ------------------------------------------
                # ARM UP
                # ------------------------------------------

                if angle < 60:

                    if stage == "DOWN":

                        # Rep completed
                        counter += 1

                        # Correct curl angle
                        good_reps += 1

                        form_status = "GOOD FORM"

                        feedback = "Good curl"

                        speak(
                            f"Good. {counter} curl"
                        )

                    stage = "UP"

            # ==================================================
            # SHOULDER RAISE
            # ==================================================

            elif exercise == "Shoulder Raise":

                lh = lm[
                    mp_pose.PoseLandmark.LEFT_HIP
                ]

                ls = lm[
                    mp_pose.PoseLandmark.LEFT_SHOULDER
                ]

                le = lm[
                    mp_pose.PoseLandmark.LEFT_ELBOW
                ]

                rh = lm[
                    mp_pose.PoseLandmark.RIGHT_HIP
                ]

                rs = lm[
                    mp_pose.PoseLandmark.RIGHT_SHOULDER
                ]

                re = lm[
                    mp_pose.PoseLandmark.RIGHT_ELBOW
                ]

                # Calculate shoulder angles
                left_angle = calculate_angle(
                    lh,
                    ls,
                    le
                )

                right_angle = calculate_angle(
                    rh,
                    rs,
                    re
                )

                angle = (
                    left_angle + right_angle
                ) / 2

                # Draw upper body
                for a, b in [
                    (lh, ls),
                    (ls, le),
                    (rh, rs),
                    (rs, re)
                ]:

                    draw_connection(
                        frame,
                        a,
                        b
                    )

                for point in [
                    lh,
                    ls,
                    le,
                    rh,
                    rs,
                    re
                ]:

                    draw_point(
                        frame,
                        point
                    )

                # ------------------------------------------
                # ARM DOWN
                # ------------------------------------------

                if angle < 40:

                    stage = "DOWN"

                    form_status = "GOOD FORM"

                    feedback = (
                        "Ready to raise"
                    )

                # ------------------------------------------
                # ARM MIDDLE
                # ------------------------------------------

                elif 40 <= angle <= 70:

                    form_status = "FIX FORM"

                    feedback = (
                        "Raise your arms higher"
                    )

                    speak(
                        "Raise your arms higher"
                    )

                # ------------------------------------------
                # ARM UP
                # ------------------------------------------

                if angle > 70:

                    if stage == "DOWN":

                        counter += 1

                        if form_status == "GOOD FORM":

                            good_reps += 1

                            feedback = "Good raise"

                            speak(
                                f"Good. {counter} raise"
                            )

                        else:

                            bad_reps += 1

                            feedback = (
                                "Fix your raise form"
                            )

                            speak(
                                "Fix your raise form"
                            )

                    stage = "UP"

        # ==================================================
        # INFORMATION PANEL
        # ==================================================

        cv2.rectangle(
            frame,
            (10, 10),
            (430, 245),
            (15, 25, 40),
            -1
        )

        cv2.putText(
            frame,
            f"HI: {username}",
            (25, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Exercise: {exercise}",
            (25, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Reps: {counter}",
            (25, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Good: {good_reps}    Bad: {bad_reps}",
            (25, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Angle: {int(angle)}",
            (25, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Status: {form_status}",
            (25, 190),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            feedback,
            (25, 220),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        # ==================================================
        # CAMERA WINDOW
        # ==================================================

        cv2.imshow(
            "AI Workout Assistant",
            frame
        )

        # Q = Exit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # ======================================================
    # CLEANUP
    # ======================================================

    cap.release()

    pose.close()

    cv2.destroyAllWindows()

    # ======================================================
    # FINAL WORKOUT SUMMARY
    # ======================================================

    messagebox.showinfo(
        "Workout Complete",
        f"Workout Complete!\n\n"
        f"Name: {username}\n"
        f"Exercise: {exercise}\n\n"
        f"Total Reps: {counter}\n"
        f"Good Reps: {good_reps}\n"
        f"Bad Reps: {bad_reps}"
    )


# ==========================================================
# MODERN GUI
# ==========================================================

ctk.set_appearance_mode("dark")

ctk.set_default_color_theme("blue")


app = ctk.CTk()


app.title(
    "AI Workout Assistant"
)


app.geometry(
    "950x650"
)


app.resizable(
    False,
    False
)


selected_exercise = ctk.StringVar(
    value="Squat"
)


# ==========================================================
# START WORKOUT FUNCTION
# ==========================================================

def start_selected_workout():

    exercise = selected_exercise.get()

    username = name_entry.get()

    if username.strip() == "":
        username = "User"

    app.withdraw()

    workout(
        exercise,
        username
    )

    app.deiconify()


# ==========================================================
# TITLE
# ==========================================================

title = ctk.CTkLabel(
    app,
    text="AI WORKOUT ASSISTANT",
    font=ctk.CTkFont(
        size=34,
        weight="bold"
    )
)

title.pack(
    pady=(45, 5)
)


subtitle = ctk.CTkLabel(
    app,
    text="COMPUTER VISION FITNESS SYSTEM",
    font=ctk.CTkFont(
        size=15
    ),
    text_color="#8FA3BF"
)

subtitle.pack(
    pady=(0, 35)
)


# ==========================================================
# PROFILE
# ==========================================================

profile_frame = ctk.CTkFrame(
    app,
    width=800,
    height=120
)

profile_frame.pack(
    padx=50,
    pady=10
)

profile_frame.pack_propagate(False)


name_entry = ctk.CTkEntry(
    profile_frame,
    placeholder_text="Name",
    width=200,
    height=42
)

name_entry.grid(
    row=0,
    column=0,
    padx=20,
    pady=38
)


age_entry = ctk.CTkEntry(
    profile_frame,
    placeholder_text="Age",
    width=150,
    height=42
)

age_entry.grid(
    row=0,
    column=1,
    padx=20
)


height_entry = ctk.CTkEntry(
    profile_frame,
    placeholder_text="Height (cm)",
    width=180,
    height=42
)

height_entry.grid(
    row=0,
    column=2,
    padx=20
)


# ==========================================================
# EXERCISE TITLE
# ==========================================================

exercise_title = ctk.CTkLabel(
    app,
    text="SELECT EXERCISE",
    font=ctk.CTkFont(
        size=22,
        weight="bold"
    )
)

exercise_title.pack(
    pady=(30, 15)
)


# ==========================================================
# EXERCISE FRAME
# ==========================================================

exercise_frame = ctk.CTkFrame(
    app,
    fg_color="transparent"
)

exercise_frame.pack()


# ==========================================================
# EXERCISE SELECTION
# ==========================================================

def choose_exercise(name):

    selected_exercise.set(name)

    squat_button.configure(
        fg_color="#1f6aa5"
        if name == "Squat"
        else "#263449"
    )

    curl_button.configure(
        fg_color="#1f6aa5"
        if name == "Bicep Curl"
        else "#263449"
    )

    shoulder_button.configure(
        fg_color="#1f6aa5"
        if name == "Shoulder Raise"
        else "#263449"
    )


# ==========================================================
# SQUAT BUTTON
# ==========================================================

squat_button = ctk.CTkButton(
    exercise_frame,
    text="SQUAT\n\n🏋",
    width=230,
    height=140,
    font=ctk.CTkFont(
        size=18,
        weight="bold"
    ),
    fg_color="#1f6aa5",
    command=lambda: choose_exercise("Squat")
)

squat_button.grid(
    row=0,
    column=0,
    padx=12
)


# ==========================================================
# BICEP CURL BUTTON
# ==========================================================

curl_button = ctk.CTkButton(
    exercise_frame,
    text="BICEP CURL\n\n💪",
    width=230,
    height=140,
    font=ctk.CTkFont(
        size=18,
        weight="bold"
    ),
    fg_color="#263449",
    command=lambda: choose_exercise("Bicep Curl")
)

curl_button.grid(
    row=0,
    column=1,
    padx=12
)


# ==========================================================
# SHOULDER RAISE BUTTON
# ==========================================================

shoulder_button = ctk.CTkButton(
    exercise_frame,
    text="SHOULDER RAISE\n\n🙆",
    width=230,
    height=140,
    font=ctk.CTkFont(
        size=18,
        weight="bold"
    ),
    fg_color="#263449",
    command=lambda: choose_exercise("Shoulder Raise")
)

shoulder_button.grid(
    row=0,
    column=2,
    padx=12
)


# ==========================================================
# START BUTTON
# ==========================================================

start_button = ctk.CTkButton(
    app,
    text="START WORKOUT",
    width=500,
    height=55,
    font=ctk.CTkFont(
        size=18,
        weight="bold"
    ),
    command=start_selected_workout
)

start_button.pack(
    pady=45
)


# ==========================================================
# FOOTER
# ==========================================================

footer = ctk.CTkLabel(
    app,
    text=(
        "AI Pose Estimation • "
        "Real-Time Rep Counting • "
        "Voice Feedback"
    ),
    text_color="#667892"
)

footer.pack(
    pady=5
)


# ==========================================================
# RUN APPLICATION
# ==========================================================

app.mainloop()