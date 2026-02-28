"""
Mexican License Plate Image Augmentation

This script performs automated image augmentations on mexican license plate 
images to create a realistic dataset for OCR model training.

The script processes all images from an input directory structure where
each subfolder represents a class (e.g., plate state or formats).
Each augmentation is applied with random rotation, tilt, and perspective
transformations to simulate real-world capture conditions.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import random
import os
from pathlib import Path
import argparse
from tqdm import tqdm

#region perspective()
def rotation_perspective(image, angle=None):
    """
    Apply random rotation and perspective transformation to simulate
    non-ideal capture angles.
    
    Args:
        image: Input image (numpy array)
        angle: Optional specific rotation angle
    
    Returns:
        Transformed image with rotation and perspective distortion
    """
    h, w = image.shape[:2]
    if angle is None:
        angle = random.randint(-25, 25)  # Random rotation between -25 and 25 degrees
    
    # Rotation
    rotation_matrix = cv2.getRotationMatrix2D((w//2, h//2), angle, 1)
    rotated = cv2.warpAffine(image, rotation_matrix, (w, h))
    
    # Random perspective distortion
    source_points = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    target_points = np.float32([
        [random.randint(0, 20), random.randint(0, 20)],
        [w - random.randint(0, 20), random.randint(0, 20)],
        [random.randint(0, 20), h - random.randint(0, 20)],
        [w - random.randint(0, 20), h - random.randint(0, 20)]
    ])
    
    perspective_matrix = cv2.getPerspectiveTransform(source_points, target_points)
    return cv2.warpPerspective(rotated, perspective_matrix, (w, h))
#endregion

#region motion_blur()
def motion_blur(image, kernel_size=15):
    """Simulate motion blur effect."""
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size-1)/2), :] = np.ones(kernel_size)
    kernel = kernel / kernel_size
    return cv2.filter2D(image, -1, kernel)
#endregion

#region contrast()
def auto_contrast(image):
    """Apply automatic contrast enhancement."""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    pil_img = ImageOps.autocontrast(pil_img)
    np_img = np.array(pil_img)
    return cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
#endregion

#region defocus_blur()
def defocus_blur(image, kernel_size=15):
    """Simulate defocus blur using Gaussian blur."""
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
#endregion

#region color_jitter()
def color_jitter(image, brightness=1.2, contrast=1.2, saturation=1.2):
    """Apply random color adjustments."""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    pil_img = ImageEnhance.Brightness(pil_img).enhance(brightness)
    pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)
    pil_img = ImageEnhance.Color(pil_img).enhance(saturation)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
#endregion

#region channel_dropout()
def channel_dropout(image):
    """Randomly drop one color channel."""
    channels = list(cv2.split(image))
    drop_channel = random.choice([0, 1, 2])
    channels[drop_channel] = np.zeros_like(channels[drop_channel])
    return cv2.merge(channels)
#endregion

#region dithering()
def dithering(image, bits=4):
    """Simulate dithering effect by reducing color depth."""
    shift = 8 - bits
    return (image >> shift) << shift
#endregion

#region downscale()
def downscale(image, scale=0.5):
    """Simulate low resolution by downscaling and upscaling."""
    h, w = image.shape[:2]
    small = cv2.resize(image, (int(w*scale), int(h*scale)))
    return cv2.resize(small, (w, h))
#endregion

#region equalize()
def equalize(image):
    """Apply histogram equalization."""
    img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
#endregion

#region glass_blur()
def glass_blur(image, iterations=3):
    """Simulate glass blur effect."""
    h, w = image.shape[:2]
    result = image.copy()
    
    for _ in range(iterations):
        dx, dy = np.random.randint(-2, 3), np.random.randint(-2, 3)
        translation_matrix = np.float32([[1, 0, dx], [0, 1, dy]])
        result = cv2.warpAffine(result, translation_matrix, (w, h))
        result = cv2.GaussianBlur(result, (3, 3), 0)
    
    return result
#endregion

#region iso_noise()
def iso_noise(image, intensity=25):
    """Add random noise to simulate high ISO."""
    noise = np.random.normal(0, intensity, image.shape).astype(np.uint8)
    return cv2.add(image, noise)
#endregion

#region illumination()
def illumination(image, factor=0.25):
    """Simulate different lighting conditions."""
    return cv2.convertScaleAbs(image, alpha=factor, beta=0)
#endregion

#region random_fog()
def random_fog(image, fog_intensity=0.9):
    """Add fog effect to the image."""
    h, w = image.shape[:2]
    fog = np.full((h, w, 3), 255, dtype=np.uint8)
    return cv2.addWeighted(image, 1 - fog_intensity, fog, fog_intensity, 0)
#endregion

#region occlusion()
def random_occlusion(image):
    """Add random black rectangles to simulate occlusions."""
    h, w = image.shape[:2]
    x1 = random.randint(0, w//2)
    y1 = random.randint(0, h//2)
    width = random.randint(45, 100)
    height = random.randint(45, 100)
    x2 = min(x1 + width, w)
    y2 = min(y1 + height, h)
    
    result = image.copy()
    cv2.rectangle(result, (x1, y1), (x2, y2), (0, 0, 0), -1)
    return result
#endregion

#region rain()
def random_rain(image, num_drops=100):
    """Simulate rain effect on the image."""
    h, w = image.shape[:2]
    result = image.copy()
    
    for _ in range(num_drops):
        x1 = random.randint(0, w)
        y1 = random.randint(0, h)
        x2 = x1 + random.randint(-5, 5)
        y2 = y1 + random.randint(10, 20)
        cv2.line(result, (x1, y1), (x2, y2), (200, 200, 200), 1)
    
    return result
#endregion

#region shadow() 
def random_shadow(image):
    """Add random triangular shadow to the image."""
    h, w = image.shape[:2]
    result = image.copy()
    
    # Create random triangle for shadow
    points = np.array([[random.randint(0, w), random.randint(0, h)] 
                       for _ in range(3)])
    
    # Create shadow mask
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [points], 255)
    
    # Apply shadow
    shadow = cv2.bitwise_and(result, result, mask=mask)
    result = cv2.addWeighted(result, 0.7, shadow, 0.3, 0)
    
    return result
#endregion

#region snow()
def random_snow(image, intensity=0.2):
    """Simulate snow effect on the image."""
    snow = np.full_like(image, 255)
    return cv2.addWeighted(image, 1 - intensity, snow, intensity, 0)
#endregion

#region sun_flare()
def random_sun_flare(image):
    """Simulate sun flare effect."""
    h, w = image.shape[:2]
    result = image.copy()
    
    # Create random flare circle
    center_x = random.randint(0, w)
    center_y = random.randint(0, h)
    radius = random.randint(50, 150)
    
    cv2.circle(result, (center_x, center_y), radius, (255, 255, 255), -1)
    result = cv2.GaussianBlur(result, (21, 21), 0)
    
    return result
#endregion

#region spatter()
def spatter(image, num_spots=30):
    """Simulate mud or water spots."""
    h, w = image.shape[:2]
    result = image.copy()
    
    for _ in range(num_spots):
        x = random.randint(0, w)
        y = random.randint(0, h)
        radius = random.randint(5, 15)
        cv2.circle(result, (x, y), radius, (50, 50, 50), -1)
    
    return result
#endregion

#region Transformations Dict
# Dictionary of available transformations
AVAILABLE_TRANSFORMS = {
    "motion_blur": motion_blur,
    "auto_contrast": auto_contrast,
    "defocus_blur": defocus_blur,
    "color_jitter": color_jitter,
    "channel_dropout": channel_dropout,
    "dithering": dithering,
    "downscale": downscale,
    "equalize": equalize,
    "glass_blur": glass_blur,
    "iso_noise": iso_noise,
    "illumination": illumination,
    "random_fog": random_fog,
    "random_occlusion": random_occlusion,
    "random_rain": random_rain,
    "random_shadow": random_shadow,
    "random_snow": random_snow,
    "random_sun_flare": random_sun_flare,
    "spatter": spatter
}
#endregion

#region image_processing()
def process_image(image_path, output_dir, transforms, num_variations=1):
    """
    Process a single image by applying all transformations.
    
    Args:
        image_path: Path to input image
        output_dir: Output directory path
        transforms: Dictionary of transformation functions
        num_variations: Number of variations per transformation
    
    Returns:
        List of generated file paths
    """
    # Read image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Warning: Could not read image {image_path}")
        return []
    
    # Get filename without extension
    filename = image_path.stem
    extension = image_path.suffix
    
    generated_files = []
    
    # Apply each transformation multiple times
    for transform_name, transform_func in transforms.items():
        for variation in range(num_variations):
            # Apply rotation/perspective first
            transformed = rotation_perspective(image)
            # Apply specific transformation
            transformed = transform_func(transformed)
            
            # Generate output filename
            output_filename = f"{filename}_{transform_name}_v{variation+1}{extension}"
            output_path = output_dir / output_filename
            
            # Save image
            cv2.imwrite(str(output_path), transformed)
            generated_files.append(output_path)
    
    return generated_files
#endregion

#region main()
# run this script from the command line as follows:
# python .\augmentator.py --input_dir ../MLP-Generator/dataset --output_dir ./augmented_data
def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Mexican augment license plate images for OCR training"
    )
    parser.add_argument(
        "--input_dir", 
        type=str, 
        required=True,
        help="Input directory containing class subdirectories with images"
    )
    parser.add_argument(
        "--output_dir", 
        type=str, 
        default="./augmented_dataset",
        help="Output directory for augmented images (default: ./augmented_dataset)"
    )
    parser.add_argument(
        "--num_variations", 
        type=int, 
        default=1,
        help="Number of variations per transformation (default: 1)"
    )
    parser.add_argument(
        "--transforms", 
        type=str, 
        nargs="+",
        help="Specific transforms to apply (default: all)"
    )
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Validate input directory
    if not input_dir.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    # Determine which transforms to use
    transforms_to_apply = AVAILABLE_TRANSFORMS
    if args.transforms:
        transforms_to_apply = {
            name: func for name, func in AVAILABLE_TRANSFORMS.items() 
            if name in args.transforms
        }
    
    print(f"Processing images from: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Applying {len(transforms_to_apply)} transformations")
    print(f"Number of variations per transform: {args.num_variations}")
    
    # Process each class subdirectory
    class_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    
    if not class_dirs:
        print("No class directories found. Processing images directly from input directory.")
        class_dirs = [input_dir]
    
    total_images = 0
    
    for class_dir in class_dirs:
        # Create output directory for this class
        class_output_dir = output_dir / class_dir.name
        class_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all images in this class directory
        image_extensions = {'.jpg', '.jpeg', '.png'}
        images = [f for f in class_dir.iterdir() 
                  if f.is_file() and f.suffix.lower() in image_extensions]
        
        print(f"\nProcessing class: {class_dir.name}")
        print(f"Found {len(images)} images")
        
        # Process each image
        for image_path in tqdm(images, desc=f"Augmenting {class_dir.name}"):
            generated = process_image(
                image_path, 
                class_output_dir, 
                transforms_to_apply,
                args.num_variations
            )
            total_images += len(generated)
    
    print(f"\nProcessing complete!")
    print(f"Total augmented images generated: {total_images}")
    print(f"Results saved in: {output_dir}")


if __name__ == "__main__":
    main()
#endregion