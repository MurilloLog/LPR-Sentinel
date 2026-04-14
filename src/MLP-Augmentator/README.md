# Mexican License Plate Image Augmentation
A comprehensive Python tool for automated image augmentation of Mexican license plate images, designed to create realistic and diverse datasets for training OCR (Optical Character Recognition) and license plate recognition models.

## Overview
This script applies various image transformations to license plate images, simulating real-world capture conditions such as different lighting, weather effects, camera imperfections, and geometric distortions. The tool processes images organized in class-based directory structures and generates multiple augmented variations per input image.

## Key Features
- Comprehensive Transformations: 20+ image transformations including geometric, lighting, weather, and quality effects
- Class-Aware Processing: Maintains directory structure with class-based organization
- Flexible Configuration: JSON-based configuration or command-line arguments
- Independent Geometric Variations: Apply rotation, scaling, and perspective as separate variations
- Real-World Simulations: Weather effects (rain, snow, fog), lighting variations, camera artifacts
- Progress Tracking: Visual progress bars with tqdm
- Resize Options: Target size specification with aspect ratio preservation
- Extensible Architecture: Easy to add new transformations

## Project Structure
```
/MLP-Augmentator
|---- /augmented_dataset      # Created after running augmentator.py 
|     |-- /ags                # State-specific folders (Aguascalientes)
|     |-- /bc                 # Baja California
|     |-- /bcs                # Baja California Sur
|     |-- /...                # All 32 state folders
|---- augmentator.py          # Main generation script
└── README.md
```

## Usage
Basic Example:

```
python augmentator.py --input_dir ../MLP-Generator/dataset --output_dir ./augmented_dataset
```
