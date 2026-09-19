# 🤖 ADDIX (Advanced Digital Dynamic Intelligence X-Engine)

ADDIX is a secure, 100% offline desktop robot assistant framework designed for localized Human-Robot Interaction (HRI). Operating entirely on computer hardware without cloud dependencies. ADDIX bridges standard operating system automation loops with advanced cognitive language processing.

---

## 🧠 Architectural Overview
Traditional virtual assistants require persistent internet access, introducing latency and privacy risks. ADDIX resolves this by routing deterministic system commands (such as local file searching and global encyclopedia scraping) through high-speed Python logic, while routing fluid conversational reasoning into a local Large Language Model (*Llama 3*).

### 📋 Key Subsystems
*   *Vocal Capture & Synthesis:* High-accuracy offline audio streaming using PyAudio drivers, mapped into an active signal filter to drop empty microphone background artifacts.
*   *Secure Environment Abstraction:* Complete isolation of local machine paths, directories, and email automation texts inside a protected .env file, managed via a strict .gitignore file.
*   *Automated Media Engineering:* Generation of programmatic .m3u playback script queues with automated disk cache cleanups upon application launch.

---


### ⚡ NVIDIA CUDA Optimization
To reduce conversational latency from *45 seconds down to under 15 seconds*, ADDIX uses local environment variables:
1. CUDA_VISIBLE_DEVICES = 0: Forces the Windows kernel to bypass integrated CPU rendering and use dedicated grahpic card for calculations.
2. OLLAMA_NUM_PARALLEL = 1: Dedicates 100% of the graphics VRAM to computing the active single-user conversation thread.

---

## 🚀 Setup & Local Deployment

### 1. Prerequisites
Ensure you have Python 3.12+ installed on your system. Download and install the [Ollama Windows Client](https://ollama.com).

### 2. Model Initialization
Configure Ollama's model storage path to your desired drive directory, open your standard command prompt, and download the model weights:
bash
ollama run llama3


### 3. Local Installation & Configuration
Clone this repository into your local environment directory:
bash
git clone https://github.com
cd Projects
pip install -r requirements.txt


Rename .env.example to .env and fill out your local machine directories


### 4. Run the Engine
Execute the main boot sequence script to initialize hardware pre-loading maps:
bash
python chatbot.py


---

## 🔮 Future Robotics Roadmap (Phase 2)
*   *Low-Power Standby Engine:* Integrating passive wake-word engines (such as Porcupine) to transition from silent text modes into open audio streams.
*   *Linux & ROS Integration:* Rehosting the core Python modules into Ubuntu Linux environments to execute as real-time nodes inside *ROS (Robot Operating System)*.
*   *Actuator Serial Control Loop:* Using ADDIX logic with microcontrollers (Arduino/Raspberry Pi) to drive physical electric motors and robotic arm based on human speech commands.
