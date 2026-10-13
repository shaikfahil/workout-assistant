# AI Workout Assistant 🏋️‍♂️

An intelligent, real-time computer vision fitness coach that monitors exercise form, counts repetitions, tracks good vs. bad reps, and gives auditory feedback using AI pose estimation.

---

## 🌟 Features

- **Real-Time Pose Tracking**: Utilizes **MediaPipe Pose** to detect and track key bodily joints at high frame rates.
- **Accurate Form Validation**:
  - **Squats**: Calculates hip-knee-ankle joint angles and tracks squat depth and posture.
  - **Bicep Curls**: Measures shoulder-elbow-wrist flexion, counting complete reps while detecting incomplete ranges of motion.
  - **Shoulder Raises**: Assesses arm elevation angle to guide safe and effective deltoid exercises.
- **Auditory Coaching**: Integrated Windows speech synthesizer provides instant voice prompts, correction alerts, and encouragement.
- **Modern Dark GUI**: Built using **CustomTkinter** for an intuitive and sleek user experience.
- **Rep & Performance Tracking**: Differentiates between correct (good) reps and faulty (bad) form repetitions in real-time.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **OpenCV (`cv2`)**: Video stream ingestion and on-screen metrics overlay.
- **MediaPipe**: 33-point body landmark detection and kinematic tracking.
- **CustomTkinter**: Modern GUI framework.
- **Windows System.Speech**: Real-time asynchronous text-to-speech feedback.

---

## 🚀 Getting Started

### 1. Prerequisites

Ensure you have Python installed (Python 3.10 to 3.12 recommended).

### 2. Clone the Repository

```bash
git clone https://github.com/shaikfahil/workout-assistant.git
cd workout-assistant
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python miniproject1_aiml_final.py
```

---

## 📌 Usage Guide

1. Enter your name in the input field.
2. Select an exercise:
   - **Squat**
   - **Bicep Curl**
   - **Shoulder Raise**
3. Click **START WORKOUT**.
4. Position yourself so your body is clearly visible in the webcam frame.
5. Follow the visual skeleton overlay and auditory feedback as you complete your sets!
6. Press `q` or close the camera window when finished to view your summary.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
