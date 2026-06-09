# LPR-Sentinel: A High-Speed Neural Vision System for Mexican License Plate Recognition

<div align="center">
  <strong>Primer Concurso de Innovación. Programación y Sistemas Inteligentes 2026</strong><br>
  <strong>Category: B-LPR | Team: LPR-Sentinel</strong>
</div>

LPR-Sentinel is a system for synthetic data generation, augmentation, detection, and recognition of license plates for Mexican private vehicles. It is explicitly designed to comply with the guidelines established in the first version of [NOM-001-SCT-2-2016](https://www.dof.gob.mx/nota_detalle.php?codigo=5442476&fecha=24/06/2016#gsc.tab=0) standard.

The project adopts a "synthetic-data-first" philosophy, training its main neural network entirely on procedurally generated data to avoid the ethical and legal complexities of real-world vehicle images. Its purpose is to demonstrate how synthetic data pipelines can enable ethical, low-cost, and reproducible machine learning solutions for real-world challenges in Mexico.

## System Requirements
The system is primarily developed in Python [3.11.9](https://www.python.org/downloads/release/python-3119/) and leverages the ONNX Runtime for high‑performance inference on edge devices.
The minimum requirements to replicate the project are listed below:

|Component | Requirement |
|-|-|
|Edge Device | Raspberry Pi 4B |
|Capture Device | Conventional USB camera (minimum 720p resolution)|
|Operating System | Raspberry Pi OS Lite (Debian 13, Trixie)|
|Python | ```3.11.9``` |
|Core Libraries | ```onnxruntime```, ```opencv-python```, ```numpy```|
|Hardware (CPU) | x86_64 or ARM64 architecture with at least 4 cores|
|Memory (RAM) | Minimum 8 GB (16 GB recommended for training) |
|Storage | At least 10 GB free disk space for datasets and model checkpoints |
|Dependencies | Build tools (```pip```, ```setuptools```, ```build-essential```, ```git```) installed

## Installation Guide
The following instructions explain how to set up LPR-Sentinel on different platforms. Choose the section that matches your environment.

<details>
<summary>Linux / Ubuntu (bash)</summary>

**Update system packages**
```bash
sudo apt update && sudo apt upgrade -y
```

**Clone the repository**
```bash
git clone https://github.com/MurilloLog/LPR-Sentinel.git
cd LPR-Sentinel
```

**Create and activate virtual environment (Optional)**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install LPR-Sentinel dependencies**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
</details>

<details>
<summary>Windows (PowerShell)</summary>

**Clone the repository**
```bash
git clone https://github.com/MurilloLog/LPR-Sentinel.git
cd LPR-Sentinel
```

**Create and activate virtual environment (Optional)**
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```
<details>
<summary>PowerShell Execution Policy Error</summary>
If you recive the error:

```bash
Activate.ps1 cannot be loaded because running scripts is disabled on this system...
```

when trying to activate the virtual environment, open **PowerShell as Administrator** and run the following command:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

</details>
  
**Install LPR-Sentinel dependencies**
```bash
pip install -r requirements.txt
```
</details>

<details>
<summary>Raspberry Pi OS (ARM64)</summary>

**Update system packages**
```bash
sudo apt update && sudo apt upgrade -y
```

**Clone the repository**
```bash
git clone https://github.com/MurilloLog/LPR-Sentinel.git
cd LPR-Sentinel
```

**Create and activate virtual environment (Optional)**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install LPR-Sentinel dependencies**
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
</details>

## Project Structure

After cloning the repository and installing dependencies, the directory tree is organized as follows:
```
LPR-Sentinel/
├── docs/                  # White-paper (pre-print)
├── tests/                 # Tests scripts for device capture
├── venv/                  # Virtual environment (optional)
├── requirements.txt       # Python dependencies
├── src/
|   ├── MLP-Generator/     # Synthetic data generation module
│   ├── MLP-Augmentator/   # Synthetic data augmentation module
│   ├── MLP-Detector/      # Plate detection module
│   ├── MLP-Recognizer/    # OCR module
│   ├── MLP-Register/      # DB module
│   └── MLP-Pipeline/      # LPR-Sentinel pipeline
│       └── main_rt.py     # Entry point script
├── requirements.txt       # All LPR-Sentinel dependencies
├── README.md              # This documentation
├── .gitignore
└── LICENSE
```

## Usage Guide
The system can be executed in three main modes: ```Image Mode```, ```Video Mode```, and ```Real‑time Camera Mode```. Each mode is designed to handle different input sources and provides flexible options for output and debugging.

Before running any command, ensure that:
- All commands must be executed inside the repository root, with the virtual environment activated (if created).
- The command‑line interface (CLI) should look similar to the following when the environment is active:

```bash
(venv) user@machine:~/LPR-Sentinel$
```

This prefix ```(venv)``` indicates that the virtual environment is correctly activated.

- If you only want to execute the pipeline (image, video, or camera modes) without retraining models, navigate to the pipeline directory:

```bash
cd src/MLP-Pipeline
```

- If you intend to retrain or fine‑tune models, refer to the dedicated training documentation ([README](src/MLP-Recognizer/README.md) module in the respective section), which explains dataset preparation, configuration files, and training commands.

### Image Mode
This mode processes a single image file and displays the detection and recognition results directly in the terminal.
```bash
python main_rt.py --image custom_image_path.png --output custom_output_dir
```
- ```custom_image_path.png```: Replace with the path to the image you want to process (supported formats: .png or .jpg).
- **Sample images**: You can find several example images in the ```input/``` directory.
- ```custom_output_dir```: The processed image with annotations will be saved in the specified output folder. If not provided, results are stored in the current directory.

### Video Mode
This mode processes a video file frame by frame and generates a new video with license plate annotations.

```bash
python main_rt.py --video input.mp4 --output-video output.mp4 
```

- ```input.mp4```: Replace with the path to the video you want to process.
- **Sample videos**: Example files can be placed in the ```input/``` directory for testing.
- ```output.mp4```: The processed video with annotations will be saved under the name you specify. If not provided, results will not be saved.

### Real-time Camera Mode
This mode processes a live camera feed and displays detection and recognition results directly in an OpenCV window.
```bash
# Default camera
python main_rt.py --camera

# Specific camera
python main_rt.py --camera --camera-id 1
```

- **Default camera**: If no ```--camera-id``` is provided, the system uses the default camera (ID 0).
- ```--camera-id```: Use this option to select a specific camera device connected to your system.

## Benchmarks
### Raspberry Pi
|Stage | Mean (ms) | p50(ms) | p95(ms) | p99(ms) |
|-|-|-|-|-|
|Detection|568.69|534.8|665.15|678.17|
|Recognition|55.06|54.85|59.32|61.24|
|DB access|1.68|1.64|1.98|2.83|


### Ryzen 7 5700G
|Stage | Mean (ms) | p50(ms) | p95(ms) | p99(ms) |
|-|-|-|-|-|
|Detection|51.46|45.90|73.78|75.67|
|Recognition|4.51|4.47|5.18|6.26|
|DB access|0.68|0.68|0.72|1.04|

### Average Performance
|Metric|Raspberry Pi 4B|
|-|-|
|Global Accuracy|82%|
|Daytime Accuracy|88%|
|Nighttime Accuracy|76%|
|False Positives|0%|
|False Negatives|18%|
|CPU Usage|64.79%|
|RAM per Inference (avg)|199.90 MB|
|RAM Peak|203.6 MB|
|Throughput (img/s)|1.21|
|Disk Size|13.65 MB|

## Limitations
Despite its portability and reproducibility, LPR‑Sentinel has several constraints that should be considered when deploying or extending the system:

- Pre‑trained Models Required  
The pipeline depends on pre‑trained ONNX models for both detection and OCR. Retraining is possible but requires additional datasets and configuration files.

- Sensitivity to Environmental Conditions  
Performance is influenced by external factors such as lighting quality, weather conditions, and the resolution of the capture device. Daytime accuracy is consistently higher than nighttime accuracy.

- Camera Quality Dependency  
A conventional USB camera is sufficient, but low‑resolution or poorly calibrated devices may reduce detection reliability.

- Database Integration  
The system assumes that the connected database contains relevant license plate records. Without proper indexing and coverage, recognition results cannot be validated or cross‑referenced.

- Format Assumptions  
Current implementation is tailored to Mexican license plate formats (alphanumeric with optional hyphens). Plates from other regions may require additional training or configuration.

## Acknowledgements
This project builds upon open‑source foundations such as YOLO (You Only Look Once) and FastPlateOCR, which provided the baseline architectures for detection and recognition. While these frameworks did not sponsor or directly support this work, their availability was essential for the development of LPR‑Sentinel. We acknowledge the contributions of their respective communities.

## Citation
If you find our work helpful for your research or projects, please consider citing the following BibTeX entry to give proper credit:

```bibtex
@misc{lprsentinel,
author       = {Murillo Gutierrez, Gustavo Adolfo},
title        = {LPR-Sentinel: A High-Speed Neural Vision System for Mexican License Plate Recognition},
year         = {2026},
publisher    = {GitHub},
journal      = {GitHub Repository},
howpublished = {\url{https://github.com/MurilloLog/LPR-Sentinel}}
}
```

## Contribute
We welcome and appreciate all contributions!
If you notice any issues or bugs, have questions, or would like to suggest new features, please open an issue or submit a pull request. By sharing your ideas and improvements, you help strengthen the project and expand its impact.

## Demonstration Video
For a practical demonstration of LPR‑Sentinel in action, please visit our official YouTube video: [Watch the demo on YouTube](https://youtu.be/tQm2vJjAT2A)
