# LPR-Sentinel: A High-Speed Neural Vision System for License Plate Recognition

LPR-Sentinel is a system for synthetic data generation, augmentation, detection, and recognition of license plates for Mexican private vehicles. It is explicitly designed to comply with the guidelines established in the first version of NOM-001-SCT-2-2016. This regulation, issued by the Secretariat of Communications and Transportation (SCT), defines the physical, typographic, and security specifications that license plates must meet nationwide.

For its detection module, LPR-Sentinel leverages the lightweight YOLOv8n architecture, optimized for real-time performance. For the recognition stage, it integrates FastPlateOCR, a fast and efficient OCR engine tailored for license plate text extraction.

## Features

- **Multi-mode Operation**: Process single images, video files, or real-time camera streams
- **License Plate Detection**: YOLO-based ONNX detector for accurate plate localization
- **OCR Recognition**: FastPlateOCR-based ONNX model for text extraction from license plates
- **Database Integration**: SQLite database for plate information storage and retrieval
- **Performance Optimizations**: Frame skipping, detection cooldown, and efficient processing
- **Debugging Tools**: Frame quality analysis, debug output saving, and test frame functionality
- **Logging**: Automatic detection logging with timestamps and confidence scores

## System Requirements

- Python 3.11.9
- OpenCV
- ONNX Runtime
- NumPy
- Pandas
- PyYAML
- imutils

## Installation

To install LPR-Sentinel, first install all dependencies listed in the ```requirements.txt``` file by running the following commands:

```bash
# Clone the repository
git clone https://github.com/MurilloLog/LPR-Sentinel
cd LPR-Sentinel

# Install dependencies
pip install -r requirements.txt
```

## Usage Guide

### Image Mode
Process a single image file:

```bash
python main_rt.py --image path/to/image.jpg
python main_rt.py --image image.png --output custom_output_dir
```

### Video Mode

Process a video file:

```bash
# Basic video processing
python main_rt.py --video input_video.mp4

# With custom output and frame range
python main_rt.py --video input.mp4 --output-video output.mp4 --start-frame 100 --end-frame 500

# Display video window during processing
python main_rt.py --video input.mp4 --display

# Test a specific frame for debugging
python main_rt.py --video input.mp4 --test-frame 150
```

### Real-time Camera Mode
Process live camera feed:

```bash
# Default camera (ID 0)
python main_rt.py --camera

# Specific camera with recording
python main_rt.py --camera --camera-id 1 --output-video recording.mp4
```

### Limitations

- Requires pre-trained ONNX models for detection and OCR
- Performance depends on lighting conditions and camera quality
- Database must contain relevant license plate records
- Mexican license plate format assumed (alphanumeric with optional hyphens)






