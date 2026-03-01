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

#region resize()
def resize_image(image, target_size, keep_aspect_ratio=True, padding_color=(255, 255, 255)):
    """
    Resize image to target dimensions with optional aspect ratio preservation.
    
    Args:
        image: Input image (numpy array)
        target_size: Tuple of (width, height) for output image
        keep_aspect_ratio: If True, maintains aspect ratio and adds padding
                          If False, stretches image to target size
        padding_color: RGB color for padding areas when keep_aspect_ratio=True
    
    Returns:
        Resized image with target dimensions
    """
    target_w, target_h = target_size
    
    if keep_aspect_ratio:
        # Get original dimensions
        h, w = image.shape[:2]
        
        # Calculate scaling factor to fit within target size
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize image maintaining aspect ratio
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Create canvas with target size and padding color
        canvas = np.full((target_h, target_w, 3), padding_color, dtype=np.uint8)
        
        # Calculate position to center the image
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        
        # Place resized image on canvas
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
    else:
        # Simple stretch to target size
        return cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
#endregion

#region perspective()
def rotation_perspective(image, angle=None, tilt=None, swing=None):
    """
    Creates perspective distortions by directly manipulating corner points
    with controlled randomness.
    
    Args:
        image: Input image (numpy array)
    
    Returns:
        Transformed image with perspective distortion
    """
    h, w = image.shape[:2]
    
    # Generate random perspective parameters
    tilt_forward = random.uniform(-0.35, 0.35) # Effect of forward/backward tilt
    tilt_side = random.uniform(-0.35, 0.35) # Effect of side tilt
    
    # Calculate corner displacements based on tilt parameters
    top_left = [
        random.uniform(-20, 0) + tilt_side * w * 0.1,
        random.uniform(-20, 0) + tilt_forward * h * 0.1
    ]
    
    top_right = [
        w + random.uniform(0, 20) - tilt_side * w * 0.1,
        random.uniform(-20, 0) - tilt_forward * h * 0.1
    ]
    
    bottom_left = [
        random.uniform(-20, 0) - tilt_side * w * 0.1,
        h + random.uniform(0, 20) - tilt_forward * h * 0.1
    ]
    
    bottom_right = [
        w + random.uniform(0, 20) + tilt_side * w * 0.1,
        h + random.uniform(0, 20) + tilt_forward * h * 0.1
    ]
    
    # Define source and destination points
    src_points = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    dst_points = np.float32([top_left, top_right, bottom_left, bottom_right])
    
    try:
        # Calculate and apply perspective transform
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        result = cv2.warpPerspective(
            image, 
            matrix, 
            (w, h),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255)
        )
        return result
        
    except cv2.error:
        # If transform fails, return original image
        return image
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
def process_image(image_path, output_dir, transforms, num_variations=1,
                  target_size=None, keep_aspect_ratio=True, padding_color=(255, 255, 255)):
    """
    Process a single image by applying all transformations and resizing.
    
    Args:
        image_path: Path to input image
        output_dir: Output directory path
        transforms: Dictionary of transformation functions
        num_variations: Number of variations per transformation
        target_size: Tuple of (width, height) for output images. If None, no resizing
        keep_aspect_ratio: Maintain aspect ratio when resizing
        padding_color: Color for padding when keep_aspect_ratio=True
    
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
    variation_counter = 1
    
    # Apply each transformation multiple times
    for transform_name, transform_func in transforms.items():
        for variation in range(num_variations):
            # Apply rotation/perspective first
            transformed = rotation_perspective(image)
            
            # Apply specific transformation
            transformed = transform_func(transformed)
            
            # Resize if target size is specified
            if target_size is not None:
                transformed = resize_image(
                    transformed, 
                    target_size, 
                    keep_aspect_ratio=keep_aspect_ratio,
                    padding_color=padding_color
                )
            
            # Generate sequential filename
            output_filename = f"{filename}_{variation_counter:03d}{extension}"
            output_path = output_dir / output_filename
            
            # Save image
            cv2.imwrite(str(output_path), transformed)
            generated_files.append(output_path)
            
            variation_counter += 1
    
    return generated_files
#endregion

#region main()
# run this script from the command line as follows:
# python .\augmentator.py --input_dir ../MLP-Generator/dataset --output_dir ./augmented_data --target_width 94 --target_height 24
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
    parser.add_argument(
        "--target_width", 
        type=int, 
        default=None,
        help="Target width for output images (if not specified, original size is kept)"
    )
    parser.add_argument(
        "--target_height", 
        type=int, 
        default=None,
        help="Target height for output images (if not specified, original size is kept)"
    )
    parser.add_argument(
        "--keep_aspect_ratio", 
        action='store_true',
        default=True,
        help="Maintain aspect ratio when resizing (adds padding if necessary)"
    )
    parser.add_argument(
        "--stretch", 
        action='store_true',
        help="Stretch image to target size without keeping aspect ratio"
    )
    parser.add_argument(
        "--padding_color", 
        type=str, 
        default="white",
        choices=['white', 'black', 'gray'],
        help="Padding color when keeping aspect ratio (default: white)"
    )
    
    args = parser.parse_args()
    
    # Determine target size
    target_size = None
    if args.target_width is not None and args.target_height is not None:
        target_size = (args.target_width, args.target_height)
        print(f"Images will be resized to: {target_size[0]}x{target_size[1]}")
        
        # Set keep_aspect_ratio based on stretch flag
        keep_aspect_ratio = not args.stretch
        
        # Set padding color
        padding_colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'gray': (128, 128, 128)
        }
        padding_color = padding_colors[args.padding_color]
    else:
        keep_aspect_ratio = True
        padding_color = (255, 255, 255)
        print("Images will keep original size")

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
                args.num_variations,
                target_size=target_size,
                keep_aspect_ratio=keep_aspect_ratio,
                padding_color=padding_color
            )
            total_images += len(generated)
    
    print(f"\nProcessing complete!")
    print(f"Total augmented images generated: {total_images}")
    print(f"Results saved in: {output_dir}")


if __name__ == "__main__":
    main()
#endregion