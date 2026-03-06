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
import json
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

#region geometric_transformations()
def random_rotation(image, max_angle=15):
    """
    Apply random rotation to the image.
    
    Args:
        image: Input image (numpy array)
        max_angle: Maximum rotation angle in degrees
    
    Returns:
        Rotated image
    """
    h, w = image.shape[:2]
    #angle = random.uniform(-max_angle, max_angle)
    angle = max_angle
    # Get rotation matrix
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate new image dimensions to avoid cropping
    cos = abs(rotation_matrix[0, 0])
    sin = abs(rotation_matrix[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    
    # Adjust rotation matrix for translation
    rotation_matrix[0, 2] += (new_w / 2) - center[0]
    rotation_matrix[1, 2] += (new_h / 2) - center[1]
    
    # Apply rotation
    rotated = cv2.warpAffine(
        image, 
        rotation_matrix, 
        (new_w, new_h),
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)
    )
    
    return rotated

def random_scale(image, min_scale=0.8, max_scale=1.2):
    """
    Apply random scaling to the image.
    
    Args:
        image: Input image (numpy array)
        min_scale: Minimum scale factor
        max_scale: Maximum scale factor
    
    Returns:
        Scaled image
    """
    h, w = image.shape[:2]
    scale = random.uniform(min_scale, max_scale)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    scaled = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # If scaled down, place on white canvas of original size
    if scale < 1.0:
        canvas = np.full((h, w, 3), (255, 255, 255), dtype=np.uint8)
        x_offset = (w - new_w) // 2
        y_offset = (h - new_h) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = scaled
        return canvas
    
    return scaled

def random_perspective(image, max_tilt=0.35):
    """
    Creates perspective distortions by directly manipulating corner points
    with controlled randomness.
    
    Args:
        image: Input image (numpy array)
        max_tilt: Maximum tilt factor
    
    Returns:
        Transformed image with perspective distortion
    """
    h, w = image.shape[:2]
    
    # Generate random perspective parameters
    tilt_forward = random.uniform(-max_tilt, max_tilt)
    tilt_side = random.uniform(-max_tilt, max_tilt)
    
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

def apply_random_geometric_transforms(image, rotation_params=None, scale_params=None, perspective_params=None):
    """
    Apply a random combination of rotation, scaling, and perspective transforms.
    
    Args:
        image: Input image (numpy array)
        rotation_params: Dictionary with rotation parameters
        scale_params: Dictionary with scale parameters
        perspective_params: Dictionary with perspective parameters
    
    Returns:
        Geometrically transformed image
    """
    transformed = image.copy()
    
    # Set default parameters if not provided
    if rotation_params is None:
        rotation_params = {"max_angle": 15, "probability": 0.5}
    if scale_params is None:
        scale_params = {"min_scale": 0.8, "max_scale": 1.2, "probability": 0.5}
    if perspective_params is None:
        perspective_params = {"max_tilt": 0.35, "probability": 0.5}
    
    # Randomly decide which transforms to apply
    if random.random() < rotation_params.get("probability", 0.5):
        transformed = random_rotation(transformed, max_angle=rotation_params.get("max_angle", 15))
    
    if random.random() < scale_params.get("probability", 0.5):
        transformed = random_scale(
            transformed, 
            min_scale=scale_params.get("min_scale", 0.8),
            max_scale=scale_params.get("max_scale", 1.2)
        )
    
    if random.random() < perspective_params.get("probability", 0.5):
        transformed = random_perspective(transformed, max_tilt=perspective_params.get("max_tilt", 0.35))
    
    return transformed
#endregion

#region motion_blur()
def motion_blur(image, kernel_size=15):
    """Simulate motion blur effect."""
    if isinstance(kernel_size, list):
        kernel_size = random.randint(kernel_size[0], kernel_size[1])
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size-1)/2), :] = np.ones(kernel_size)
    kernel = kernel / kernel_size
    return cv2.filter2D(image, -1, kernel)
#endregion

#region contrast()
def auto_contrast(image, cutoff=0):
    """Apply automatic contrast enhancement."""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    pil_img = ImageOps.autocontrast(pil_img, cutoff=cutoff)
    np_img = np.array(pil_img)
    return cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
#endregion

#region defocus_blur()
def defocus_blur(image, kernel_size=15):
    """Simulate defocus blur using Gaussian blur."""
    if isinstance(kernel_size, list):
        kernel_size = random.randint(kernel_size[0], kernel_size[1])
        # Ensure kernel_size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
#endregion

#region color_jitter()
def color_jitter(image, brightness=1.2, contrast=1.2, saturation=1.2, hue=0):
    """Apply random color adjustments."""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    if isinstance(brightness, list):
        brightness = random.uniform(brightness[0], brightness[1])
    if isinstance(contrast, list):
        contrast = random.uniform(contrast[0], contrast[1])
    if isinstance(saturation, list):
        saturation = random.uniform(saturation[0], saturation[1])
    
    pil_img = ImageEnhance.Brightness(pil_img).enhance(brightness)
    pil_img = ImageEnhance.Contrast(pil_img).enhance(contrast)
    pil_img = ImageEnhance.Color(pil_img).enhance(saturation)
    
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
#endregion

#region channel_dropout()
def channel_dropout(image, drop_probability=0.33):
    """Randomly drop one color channel."""
    channels = list(cv2.split(image))
    if random.random() < drop_probability:
        drop_channel = random.choice([0, 1, 2])
        channels[drop_channel] = np.zeros_like(channels[drop_channel])
    return cv2.merge(channels)
#endregion

#region dithering()
def dithering(image, bits=4):
    """Simulate dithering effect by reducing color depth."""
    if isinstance(bits, list):
        bits = random.randint(bits[0], bits[1])
    shift = 8 - bits
    return (image >> shift) << shift
#endregion

#region downscale()
def downscale(image, scale=0.5):
    """Simulate low resolution by downscaling and upscaling."""
    if isinstance(scale, list):
        scale = random.uniform(scale[0], scale[1])
    h, w = image.shape[:2]
    small = cv2.resize(image, (int(w*scale), int(h*scale)))
    return cv2.resize(small, (w, h))
#endregion

#region equalize()
def equalize(image, clip_limit=2.0, grid_size=(8,8)):
    """Apply histogram equalization."""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    l = clahe.apply(l)
    
    # Merge channels
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
#endregion

#region glass_blur()
def glass_blur(image, iterations=3, max_offset=2):
    """Simulate glass blur effect."""
    if isinstance(iterations, list):
        iterations = random.randint(iterations[0], iterations[1])
    if isinstance(max_offset, list):
        max_offset = random.randint(max_offset[0], max_offset[1])
    
    h, w = image.shape[:2]
    result = image.copy()
    
    for _ in range(iterations):
        dx, dy = np.random.randint(-max_offset, max_offset+1), np.random.randint(-max_offset, max_offset+1)
        translation_matrix = np.float32([[1, 0, dx], [0, 1, dy]])
        result = cv2.warpAffine(result, translation_matrix, (w, h))
        result = cv2.GaussianBlur(result, (3, 3), 0)
    
    return result
#endregion

#region iso_noise()
def iso_noise(image, intensity=25):
    """Add random noise to simulate high ISO."""
    if isinstance(intensity, list):
        intensity = random.uniform(intensity[0], intensity[1])
    noise = np.random.normal(0, intensity, image.shape).astype(np.uint8)
    return cv2.add(image, noise)
#endregion

#region illumination()
def illumination(image, alpha=0.25, beta=0):
    """Simulate different lighting conditions."""
    if isinstance(alpha, list):
        alpha = random.uniform(alpha[0], alpha[1])
    if isinstance(beta, list):
        beta = random.randint(beta[0], beta[1])
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
#endregion

#region random_fog()
def random_fog(image, fog_intensity=0.9):
    """Add fog effect to the image."""
    if isinstance(fog_intensity, list):
        fog_intensity = random.uniform(fog_intensity[0], fog_intensity[1])
    h, w = image.shape[:2]
    fog = np.full((h, w, 3), 255, dtype=np.uint8)
    return cv2.addWeighted(image, 1 - fog_intensity, fog, fog_intensity, 0)
#endregion

#region occlusion()
def random_occlusion(image, min_size=45, max_size=100):
    """Add random black rectangles to simulate occlusions."""
    h, w = image.shape[:2]
    
    if isinstance(min_size, list):
        min_size = random.randint(min_size[0], min_size[1])
    if isinstance(max_size, list):
        max_size = random.randint(max_size[0], max_size[1])
    
    x1 = random.randint(0, w//2)
    y1 = random.randint(0, h//2)
    width = random.randint(min_size, max_size)
    height = random.randint(min_size, max_size)
    x2 = min(x1 + width, w)
    y2 = min(y1 + height, h)
    
    result = image.copy()
    cv2.rectangle(result, (x1, y1), (x2, y2), (0, 0, 0), -1)
    return result
#endregion

#region rain()
def random_rain(image, num_drops=100, length_range=(10, 20), angle_range=(-5, 5)):
    """Simulate rain effect on the image."""
    h, w = image.shape[:2]
    
    if isinstance(num_drops, list):
        num_drops = random.randint(num_drops[0], num_drops[1])
    
    result = image.copy()
    
    for _ in range(num_drops):
        x1 = random.randint(0, w)
        y1 = random.randint(0, h)
        length = random.randint(length_range[0], length_range[1])
        angle = random.randint(angle_range[0], angle_range[1])
        x2 = x1 + angle
        y2 = y1 + length
        cv2.line(result, (x1, y1), (x2, y2), (200, 200, 200), 1)
    
    return result
#endregion

#region shadow() 
def random_shadow(image, opacity=0.3):
    """Add random triangular shadow to the image."""
    h, w = image.shape[:2]
    
    if isinstance(opacity, list):
        opacity = random.uniform(opacity[0], opacity[1])
    
    result = image.copy()
    
    # Create random triangle for shadow
    points = np.array([[random.randint(0, w), random.randint(0, h)] 
                       for _ in range(3)])
    
    # Create shadow mask
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [points], 255)
    
    # Apply shadow
    shadow = cv2.bitwise_and(result, result, mask=mask)
    result = cv2.addWeighted(result, 1 - opacity, shadow, opacity, 0)
    
    return result
#endregion

#region snow()
def random_snow(image, intensity=0.2):
    """Simulate snow effect on the image."""
    if isinstance(intensity, list):
        intensity = random.uniform(intensity[0], intensity[1])
    snow = np.full_like(image, 255)
    return cv2.addWeighted(image, 1 - intensity, snow, intensity, 0)
#endregion

#region sun_flare()
def random_sun_flare(image, radius_range=(50, 150), intensity=1.0):
    """Simulate sun flare effect."""
    h, w = image.shape[:2]
    
    if isinstance(radius_range[0], list):
        radius_range = (random.randint(radius_range[0][0], radius_range[0][1]),
                       random.randint(radius_range[1][0], radius_range[1][1]))
    
    result = image.copy()
    
    # Create random flare circle
    center_x = random.randint(0, w)
    center_y = random.randint(0, h)
    radius = random.randint(radius_range[0], radius_range[1])
    
    cv2.circle(result, (center_x, center_y), radius, (255, 255, 255), -1)
    result = cv2.GaussianBlur(result, (21, 21), 0)
    
    return result
#endregion

#region spatter()
def spatter(image, num_spots=30, radius_range=(5, 15), color=(50, 50, 50)):
    """Simulate mud or water spots."""
    h, w = image.shape[:2]
    
    if isinstance(num_spots, list):
        num_spots = random.randint(num_spots[0], num_spots[1])
    
    result = image.copy()
    
    for _ in range(num_spots):
        x = random.randint(0, w)
        y = random.randint(0, h)
        radius = random.randint(radius_range[0], radius_range[1])
        cv2.circle(result, (x, y), radius, color, -1)
    
    return result
#endregion

#region Transformations Dict with Parameters
# Dictionary of available transformations with configurable parameters
AVAILABLE_TRANSFORMS = {
    "motion_blur": {
        "func": motion_blur,
        "params": {"kernel_size": 15},
        "description": "Simulates motion blur"
    },
    "auto_contrast": {
        "func": auto_contrast,
        "params": {"cutoff": 0},
        "description": "Enhances image contrast automatically"
    },
    "defocus_blur": {
        "func": defocus_blur,
        "params": {"kernel_size": 15},
        "description": "Simulates out-of-focus blur"
    },
    "color_jitter": {
        "func": color_jitter,
        "params": {"brightness": 1.2, "contrast": 1.2, "saturation": 1.2},
        "description": "Randomly adjusts brightness, contrast, and saturation"
    },
    "channel_dropout": {
        "func": channel_dropout,
        "params": {"drop_probability": 0.33},
        "description": "Randomly drops one color channel"
    },
    "dithering": {
        "func": dithering,
        "params": {"bits": 4},
        "description": "Reduces color depth to create dithering effect"
    },
    "downscaleX5": {
        "func": downscale,
        "params": {"scale": 0.5},
        "description": "Simulates low resolution by downscaling and upscaling"
    },
    "downscaleX75": {
        "func": downscale,
        "params": {"scale": 0.75},
        "description": "Simulates low resolution by downscaling and upscaling"
    },
    "downscaleX25": {
        "func": downscale,
        "params": {"scale": 0.25},
        "description": "Simulates low resolution by downscaling and upscaling"
    },
    "equalize": {
        "func": equalize,
        "params": {"clip_limit": 2.0, "grid_size": (8, 8)},
        "description": "Applies histogram equalization"
    },
    "glass_blur": {
        "func": glass_blur,
        "params": {"iterations": 3, "max_offset": 2},
        "description": "Simulates looking through glass"
    },
    "iso_noise": {
        "func": iso_noise,
        "params": {"intensity": 25},
        "description": "Adds random noise to simulate high ISO"
    },
    "illumination": {
        "func": illumination,
        "params": {"alpha": 0.25, "beta": 0},
        "description": "Simulates different lighting conditions"
    },
    "random_fog": {
        "func": random_fog,
        "params": {"fog_intensity": 0.9},
        "description": "Adds fog effect"
    },
    "random_occlusion": {
        "func": random_occlusion,
        "params": {"min_size": 45, "max_size": 100},
        "description": "Adds random occlusions"
    },
    "random_rain": {
        "func": random_rain,
        "params": {"num_drops": 100, "length_range": (10, 20), "angle_range": (-5, 5)},
        "description": "Simulates rain"
    },
    "random_shadow": {
        "func": random_shadow,
        "params": {"opacity": 0.3},
        "description": "Adds random shadows"
    },
    "random_snow": {
        "func": random_snow,
        "params": {"intensity": 0.2},
        "description": "Simulates snow"
    },
    "random_sun_flare": {
        "func": random_sun_flare,
        "params": {"radius_range": (50, 150), "intensity": 1.0},
        "description": "Simulates sun flare"
    },
    "spatter": {
        "func": spatter,
        "params": {"num_spots": 30, "radius_range": (5, 15), "color": (50, 50, 50)},
        "description": "Simulates mud or water spots"
    }
}

# Geometric transformations with parameters
GEOMETRIC_TRANSFORMS = {
    "rotationx25": {
        "func": random_rotation,
        "params": {"max_angle": 25, "probability": 1.0},
        "description": "Rotation to 25"
    },
    "rotationx50": {
        "func": random_rotation,
        "params": {"max_angle": 50, "probability": 1.0},
        "description": "Rotation to 50"
    },
    "rotationx75": {
        "func": random_rotation,
        "params": {"max_angle": 75, "probability": 1.0},
        "description": "Rotation to 75"
    },
    "scaleX25": {
        "func": random_scale,
        "params": {"min_scale": 0.25, "max_scale": 0.25, "probability": 1.0},
        "description": "0.25 scaling"
    },
    "scaleX50": {
        "func": random_scale,
        "params": {"min_scale": 0.5, "max_scale": 0.5, "probability": 1.0},
        "description": "0.5 scaling"
    },
    "scaleX75": {
        "func": random_scale,
        "params": {"min_scale": 0.75, "max_scale": 0.75, "probability": 1.0},
        "description": "0.75 scaling"
    },
    "perspectiveX35": {
        "func": random_perspective,
        "params": {"max_tilt": 0.35, "probability": 1.0},
        "description": "0.35 perspective distortion"
    },
    "perspectiveX50": {
        "func": random_perspective,
        "params": {"max_tilt": 0.5, "probability": 1.0},
        "description": "0.5 perspective distortion"
    },
    "perspectiveX70": {
        "func": random_perspective,
        "params": {"max_tilt": 0.7, "probability": 1.0},
        "description": "0.7 perspective distortion"
    }
}
#endregion

#region load_config()
def load_config(config_file):
    """
    Load transformation configuration from JSON file.
    
    Args:
        config_file: Path to JSON configuration file
    
    Returns:
        Dictionary with transformation parameters
    """
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config
#endregion

#region image_processing()
def process_image(image_path, output_dir, transforms_config, num_variations=1,
                  target_size=None, keep_aspect_ratio=True, padding_color=(255, 255, 255),
                  geometric_params=None, geometric_transforms=None):
    """
    Process a single image by applying specified transformations with custom parameters.
    
    Args:
        image_path: Path to input image
        output_dir: Output directory path
        transforms_config: Dictionary with transformation names and their parameters
        num_variations: Number of variations per transformation
        target_size: Tuple of (width, height) for output images. If None, no resizing
        keep_aspect_ratio: Maintain aspect ratio when resizing
        padding_color: Color for padding when keep_aspect_ratio=True
        geometric_params: Parameters for geometric transformations (legacy)
        geometric_transforms: Dictionary with geometric transformations to apply independently
    
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
    
    # First, process geometric transformations as independent variations if specified
    if geometric_transforms:
        for geom_name, geom_config in geometric_transforms.items():
            if geom_name not in GEOMETRIC_TRANSFORMS:
                print(f"Warning: Unknown geometric transform '{geom_name}', skipping")
                continue
            
            geom_info = GEOMETRIC_TRANSFORMS[geom_name]
            geom_func = geom_info["func"]
            base_params = geom_info["params"]
            
            # Merge with user-provided parameters
            user_params = geom_config.get("params", {})
            merged_params = {**base_params, **user_params}
            
            # Get number of variations for this geometric transform
            geom_variations = geom_config.get("num_variations", num_variations)
            
            for variation in range(geom_variations):
                # Start with original image
                transformed = image.copy()
                
                # Prepare parameters for this variation (handle range parameters)
                variation_params = {}
                for param_name, param_value in merged_params.items():
                    if param_name != "probability":  # Exclude probability for independent variations
                        if isinstance(param_value, list) and len(param_value) == 2:
                            # Parameter is a range, select random value
                            if isinstance(param_value[0], (int, float)):
                                if isinstance(param_value[0], int):
                                    variation_params[param_name] = random.randint(param_value[0], param_value[1])
                                else:
                                    variation_params[param_name] = random.uniform(param_value[0], param_value[1])
                            else:
                                variation_params[param_name] = param_value
                        else:
                            variation_params[param_name] = param_value
                
                # Apply geometric transformation
                transformed = geom_func(transformed, **variation_params)
                
                # Resize if target size is specified
                if target_size is not None:
                    transformed = resize_image(
                        transformed, 
                        target_size, 
                        keep_aspect_ratio=keep_aspect_ratio,
                        padding_color=padding_color
                    )
                
                # Generate filename
                param_suffix = "_".join([f"{k}{v}" for k, v in variation_params.items() if not isinstance(v, (list, dict))])
                if param_suffix:
                    output_filename = f"{filename}_{geom_name}_{param_suffix}_{variation+1:03d}{extension}"
                else:
                    output_filename = f"{filename}_{geom_name}_{variation+1:03d}{extension}"
                
                output_path = output_dir / output_filename
                
                # Save image
                cv2.imwrite(str(output_path), transformed)
                generated_files.append(output_path)
    
    # Then process image transformations (AVAILABLE_TRANSFORMS)
    for transform_name, transform_config in transforms_config.items():
        if transform_name not in AVAILABLE_TRANSFORMS:
            print(f"Warning: Unknown transform '{transform_name}', skipping")
            continue
        
        # Get transform function and base parameters
        transform_info = AVAILABLE_TRANSFORMS[transform_name]
        transform_func = transform_info["func"]
        base_params = transform_info["params"]
        
        # Merge with user-provided parameters
        user_params = transform_config.get("params", {})
        merged_params = {**base_params, **user_params}
        
        # Get number of variations for this specific transform
        transform_variations = transform_config.get("num_variations", num_variations)
        
        for variation in range(transform_variations):
            # Start with original image
            transformed = image.copy()
            
            # Apply geometric transformations as preprocessing if specified (legacy support)
            if geometric_params and not geometric_transforms:
                transformed = apply_random_geometric_transforms(
                    transformed,
                    rotation_params=geometric_params.get("rotation"),
                    scale_params=geometric_params.get("scale"),
                    perspective_params=geometric_params.get("perspective")
                )
            
            # Prepare parameters for this variation (handle range parameters)
            variation_params = {}
            for param_name, param_value in merged_params.items():
                if isinstance(param_value, list) and len(param_value) == 2:
                    # Parameter is a range, select random value
                    if isinstance(param_value[0], (int, float)):
                        if isinstance(param_value[0], int):
                            variation_params[param_name] = random.randint(param_value[0], param_value[1])
                        else:
                            variation_params[param_name] = random.uniform(param_value[0], param_value[1])
                    else:
                        variation_params[param_name] = param_value
                else:
                    variation_params[param_name] = param_value
            
            # Apply specific transformation
            transformed = transform_func(transformed, **variation_params)
            
            # Resize if target size is specified
            if target_size is not None:
                transformed = resize_image(
                    transformed, 
                    target_size, 
                    keep_aspect_ratio=keep_aspect_ratio,
                    padding_color=padding_color
                )
            
            # Generate filename with parameters info
            param_suffix = "_".join([f"{k}{v}" for k, v in variation_params.items() if not isinstance(v, (list, dict))])
            if param_suffix:
                output_filename = f"{filename}_{transform_name}_{param_suffix}_{variation+1:03d}{extension}"
            else:
                output_filename = f"{filename}_{transform_name}_{variation+1:03d}{extension}"
            
            output_path = output_dir / output_filename
            
            # Save image
            cv2.imwrite(str(output_path), transformed)
            generated_files.append(output_path)
    
    return generated_files
#endregion

# Run this script as:
# python augmentator.py --input_dir ../MLP-Generator/dataset --output_dir ./augmented_dataset
#region main()
def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Mexican license plate image augmentation for OCR training"
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
        help="Default number of variations per transformation (default: 1)"
    )
    parser.add_argument(
        "--transforms", 
        type=str, 
        nargs="+",
        help="Specific transforms to apply (e.g., motion_blur color_jitter rotation scale). If not specified, all transforms are applied."
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="JSON configuration file for transformation parameters"
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
    parser.add_argument(
        "--geometric", 
        type=str,
        help="[DEPRECATED] Geometric transformations parameters as JSON string or file. Use geometric_transforms in config file instead."
    )
    parser.add_argument(
        "--list_transforms", 
        action='store_true',
        help="List all available transformations with their parameters"
    )
    parser.add_argument(
        "--geometric_only", 
        action='store_true',
        help="Apply only geometric transformations (rotation, scale, perspective)"
    )
    parser.add_argument(
        "--no_geometric", 
        action='store_true',
        help="Disable all geometric transformations"
    )
    
    args = parser.parse_args()
    
    # List transforms if requested
    if args.list_transforms:
        print("\n" + "="*80)
        print("AVAILABLE TRANSFORMATIONS")
        print("="*80)
        
        print("\nGEOMETRIC TRANSFORMATIONS (Independent Variations):")
        print("-"*80)
        for name, info in GEOMETRIC_TRANSFORMS.items():
            print(f"\n{name}:")
            print(f"     Description: {info['description']}")
            print(f"     Default parameters: {info['params']}")
            print(f"     Example: --transforms {name}")
        
        print("\nIMAGE TRANSFORMATIONS:")
        print("-"*80)
        for name, info in AVAILABLE_TRANSFORMS.items():
            print(f"\n {name}:")
            print(f"     Description: {info['description']}")
            print(f"     Default parameters: {info['params']}")
            print(f"     Example: --transforms {name}")
        
        print("\n" + "="*80)
        print("USAGE EXAMPLES:")
        print("="*80)
        print("\n1. Generate independent geometric variations:")
        print("   python augmentator.py --input_dir ./dataset --transforms rotation scale perspective --num_variations 5")
        
        print("\n2. Generate combined variations with custom parameters:")
        print("   python augmentator.py --input_dir ./dataset --config my_config.json")
        
        print("\n3. Generate all transformations with default parameters:")
        print("   python augmentator.py --input_dir ./dataset --target_width 94 --target_height 24")
        
        print("\n4. Generate only geometric transformations:")
        print("   python augmentator.py --input_dir ./dataset --geometric_only --num_variations 10")
        
        return
    
    # Determine target size
    target_size = None
    if args.target_width is not None and args.target_height is not None:
        target_size = (args.target_width, args.target_height)
        print(f"\nImages will be resized to: {target_size[0]}x{target_size[1]}")
        
        # Set keep_aspect_ratio based on stretch flag
        keep_aspect_ratio = not args.stretch
        
        # Set padding color
        padding_colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'gray': (128, 128, 128)
        }
        padding_color = padding_colors[args.padding_color]
        print(f"   Padding color: {args.padding_color}")
        print(f"   Keep aspect ratio: {keep_aspect_ratio}")
    else:
        keep_aspect_ratio = True
        padding_color = (255, 255, 255)
        print("\nImages will keep original size")
    
    # Initialize configuration dictionaries
    transforms_config = {}
    geometric_transforms = {}
    geometric_params = None
    
    # Load configuration
    if args.config:
        # Load from JSON file
        print(f"\nLoading configuration from: {args.config}")
        config = load_config(args.config)
        transforms_config = config.get("transforms", {})
        geometric_transforms = config.get("geometric_transforms", {})
        geometric_params = config.get("geometric", None)  # Legacy support
        
        # Override num_variations if specified in config
        if "num_variations" in config:
            args.num_variations = config["num_variations"]
            print(f"   Default variations per transform: {args.num_variations}")
        
        print(f"   Loaded {len(transforms_config)} image transformations")
        print(f"   Loaded {len(geometric_transforms)} geometric transformations")
        
    else:
        # Build configuration from command line arguments
        
        # Handle geometric_only flag
        if args.geometric_only:
            # Apply only geometric transformations
            for geom_name in GEOMETRIC_TRANSFORMS:
                geometric_transforms[geom_name] = {
                    "num_variations": args.num_variations,
                    "params": {}
                }
            print("\nGeometric-only mode: Applying only geometric transformations")
            
        elif args.no_geometric:
            # Apply only image transformations, no geometric
            if args.transforms:
                for transform_name in args.transforms:
                    if transform_name in AVAILABLE_TRANSFORMS:
                        transforms_config[transform_name] = {
                            "num_variations": args.num_variations,
                            "params": {}
                        }
            else:
                # Use all image transforms
                for transform_name in AVAILABLE_TRANSFORMS:
                    transforms_config[transform_name] = {
                        "num_variations": args.num_variations,
                        "params": {}
                    }
            print("\nGeometric transformations disabled")
            
        elif args.transforms:
            # User specified specific transforms
            for transform_name in args.transforms:
                if transform_name in GEOMETRIC_TRANSFORMS:
                    # This is a geometric transformation
                    geometric_transforms[transform_name] = {
                        "num_variations": args.num_variations,
                        "params": {}
                    }
                    print(f"Added geometric transform: {transform_name}")
                elif transform_name in AVAILABLE_TRANSFORMS:
                    # This is an image transformation
                    transforms_config[transform_name] = {
                        "num_variations": args.num_variations,
                        "params": {}
                    }
                    print(f"Added image transform: {transform_name}")
                else:
                    print(f"Warning: Unknown transform '{transform_name}', skipping")
        else:
            # No transforms specified, use all (both geometric and image)
            print("\nNo transforms specified, applying all available transformations")
            
            # Add all geometric transforms
            for geom_name in GEOMETRIC_TRANSFORMS:
                geometric_transforms[geom_name] = {
                    "num_variations": args.num_variations,
                    "params": {}
                }
            
            # Add all image transforms
            for transform_name in AVAILABLE_TRANSFORMS:
                transforms_config[transform_name] = {
                    "num_variations": args.num_variations,
                    "params": {}
                }
        
        # Parse legacy geometric parameters if provided
        if args.geometric:
            print("\nNote: --geometric parameter is deprecated. Use geometric_transforms in config file instead.")
            try:
                # Try to parse as JSON
                geometric_params = json.loads(args.geometric)
                print("Loaded legacy geometric parameters")
            except:
                # Try to load from file
                if os.path.exists(args.geometric):
                    with open(args.geometric, 'r') as f:
                        geometric_params = json.load(f)
                    print(f"Loaded legacy geometric parameters from file: {args.geometric}")
                else:
                    print(f"Warning: Could not parse geometric parameters: {args.geometric}")
    
    # Validate that at least one transformation is selected
    if not transforms_config and not geometric_transforms:
        print("\nError: No transformations selected. Use --list_transforms to see available options.")
        return
    
    # Convert paths to Path objects
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Validate input directory
    if not input_dir.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    # Print execution summary
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    print(f"\nInput directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"\nTransformations to apply:")
    print(f"Image transformations: {len(transforms_config)}")
    if transforms_config:
        for t in transforms_config.keys():
            print(f"     - {t}")
    print(f"\nGeometric transformations (independent): {len(geometric_transforms)}")
    if geometric_transforms:
        for g in geometric_transforms.keys():
            print(f"     - {g}")
    print(f"\nDefault variations per transform: {args.num_variations}")
    
    # Calculate estimated output
    total_input_images = 0
    class_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    if not class_dirs:
        class_dirs = [input_dir]
    
    for class_dir in class_dirs:
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        images = [f for f in class_dir.iterdir() 
                  if f.is_file() and f.suffix.lower() in image_extensions]
        total_input_images += len(images)
    
    total_variations = len(transforms_config) + len(geometric_transforms)
    estimated_output = total_input_images * total_variations * args.num_variations
    print(f"\nEstimated output images: ~{estimated_output}")
    
    # Ask for confirmation if too many images
    if estimated_output > 10000:
        response = input(f"\nThis will generate approximately {estimated_output} images. Continue? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Process each class subdirectory
    total_images = 0
    start_time = cv2.getTickCount()
    
    print("\n" + "="*80)
    print("PROCESSING IMAGES")
    print("="*80)
    
    for class_dir in class_dirs:
        # Create output directory for this class
        class_output_dir = output_dir / class_dir.name
        class_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all images in this class directory
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        images = [f for f in class_dir.iterdir() 
                  if f.is_file() and f.suffix.lower() in image_extensions]
        
        if not images:
            print(f"\nNo images found in {class_dir.name}, skipping...")
            continue
        
        print(f"\nProcessing class: {class_dir.name}")
        print(f"   Found {len(images)} images")
        
        # Process each image with progress bar
        for image_path in tqdm(images, desc=f"   Augmenting", unit="img"):
            try:
                generated = process_image(
                    image_path, 
                    class_output_dir, 
                    transforms_config,
                    args.num_variations,
                    target_size=target_size,
                    keep_aspect_ratio=keep_aspect_ratio,
                    padding_color=padding_color,
                    geometric_params=geometric_params,
                    geometric_transforms=geometric_transforms
                )
                total_images += len(generated)
                
                # Update progress bar description with count
                if len(generated) > 0:
                    tqdm.write(f"Generated {len(generated)} variations for {image_path.name}")
                    
            except Exception as e:
                print(f"Error processing {image_path.name}: {str(e)}")
                continue
    
    # Calculate execution time
    end_time = cv2.getTickCount()
    execution_time = (end_time - start_time) / cv2.getTickFrequency()
    
    # Print final summary
    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"\nTotal augmented images generated: {total_images}")
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Results saved in: {output_dir}")
    
    # Print statistics per transformation type if detailed info available
    if geometric_transforms:
        print(f"\nGeometric transformations generated:")
        for geom_name in geometric_transforms.keys():
            print(f"{geom_name}: {len(geometric_transforms)} variations per image")
    
    if transforms_config:
        print(f"\nImage transformations generated:")
        for trans_name in transforms_config.keys():
            variations = transforms_config[trans_name].get("num_variations", args.num_variations)
            print(f"{trans_name}: {variations} variations per image")
    
    print("\n" + "="*80)
#endregion

if __name__ == "__main__":
    main()