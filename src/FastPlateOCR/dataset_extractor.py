"""
Image Resizing and Dataset Splitting for License Plate Recognition

This script processes images from an augmented dataset, resizes them to a target
dimension (140x70 pixels), and creates train/val/test splits with corresponding
CSV annotation files.

The script expects images in subdirectories under the input folder, with filenames
following the pattern: {plate_text}_[anything].jpg (e.g., ABC123_variation_001.jpg)
"""

import os
import cv2
import csv
import random
from tqdm import tqdm

def main():
    """
    Main execution function that processes images and creates dataset splits.
    
    The function performs the following steps:
    1. Defines input/output directories and target image size
    2. Recursively walks through input directory to find all images
    3. Resizes each image to target dimensions
    4. Saves resized images maintaining folder structure
    5. Creates train/val/test splits (80/10/10)
    6. Generates CSV annotation files for each split with relative paths
    """
    
    # Get the directory where the script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input directory containing augmented images
    # Relative path: ../MLP-Augmentator/augmented_dataset/
    img_root = os.path.join(base_dir, "../MLP-Augmentator/augmented_dataset/")
    
    # Output directory for resized images
    resized_root = os.path.join(base_dir, "140x70_dataset")
    os.makedirs(resized_root, exist_ok=True)
    
    # Target dimensions as specified in config.yaml
    target_size = (140, 70)  # width, height
    
    # Dataset split proportions
    train_split = 0.8
    val_split = 0.1
    test_split = 0.1
    
    # List to store all annotations
    annotations = []
    
    # Validate input directory exists
    if not os.path.exists(img_root):
        print(f"Error: Input directory does not exist: {img_root}")
        return
    
    # First, count total images for progress bar
    total_images = 0
    for _, _, files in os.walk(img_root):
        total_images += len([f for f in files if f.lower().endswith((".jpg", ".png", ".jpeg"))])
    
    print(f"Found {total_images} images to process")
    print(f"Resizing images to {target_size[0]}x{target_size[1]} pixels...")
    
    # Recursively walk through input directory
    with tqdm(total=total_images, desc="Processing images", unit="img") as pbar:
        for root, _, files in os.walk(img_root):
            for img_name in files:
                if img_name.lower().endswith((".jpg", ".png", ".jpeg")):
                    # Extract license plate text (everything before first underscore)
                    plate = img_name.split("_")[0]
                    
                    # Read and resize image
                    img_path = os.path.join(root, img_name)
                    img = cv2.imread(img_path)
                    
                    if img is None:
                        tqdm.write(f"Warning: Could not read image {img_path}, skipping...")
                        pbar.update(1)
                        continue
                    
                    # Resize to target dimensions
                    resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
                    
                    # Save in output directory maintaining relative structure
                    rel_path = os.path.relpath(img_path, img_root)
                    save_path = os.path.join(resized_root, rel_path)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    cv2.imwrite(save_path, resized)
                    
                    # Store annotation with path relative to base_dir
                    # This ensures Fast Plate OCR can find images when run from the same directory
                    relative_to_base = os.path.relpath(save_path, base_dir)
                    # Normalize path separators for cross-platform compatibility
                    relative_to_base = relative_to_base.replace(os.sep, '/')
                    annotations.append([relative_to_base, plate])
                    
                    # Update progress bar
                    pbar.update(1)
    
    print(f"\nSuccessfully processed {len(annotations)} images")
    
    # Shuffle annotations randomly
    random.shuffle(annotations)
    
    # Calculate split sizes
    total = len(annotations)
    train_size = int(total * train_split)
    val_size = int(total * val_split)
    test_size = total - train_size - val_size
    
    # Split the data
    train_data = annotations[:train_size]
    val_data = annotations[train_size:train_size + val_size]
    test_data = annotations[train_size + val_size:]
    
    def write_csv(filename, data):
        """
        Write annotation data to a CSV file.
        
        Args:
            filename (str): Name of the CSV file to create
            data (list): List of [image_path, plate_text] pairs
        """
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "plate_text"])  # Write header
            writer.writerows(data)
        print(f"Generated {filename} with {len(data)} entries")
        
        # Verify first entry path exists
        if data and len(data) > 0:
            test_path = os.path.join(base_dir, data[0][0])
            if os.path.exists(test_path):
                print(f"   Verified first image exists")
            else:
                print(f"   Warning: First image path does not exist")
    
    # Generate CSV files for each split
    print("\nCreating dataset split files...")
    write_csv("train.csv", train_data)
    write_csv("val.csv", val_data)
    write_csv("test.csv", test_data)
    
    # Print summary
    print("\n" + "=" * 50)
    print("PROCESSING SUMMARY")
    print("=" * 50)
    print(f"Total images processed: {total}")
    print(f"Train set size: {len(train_data)} ({train_split*100:.0f}%)")
    print(f"Validation set size: {len(val_data)} ({val_split*100:.0f}%)")
    print(f"Test set size: {len(test_data)} ({test_split*100:.0f}%)")
    print("\nOutput files:")
    print(f"  - Resized images: {resized_root}")
    print(f"  - train.csv: {os.path.join(base_dir, 'train.csv')}")
    print(f"  - val.csv: {os.path.join(base_dir, 'val.csv')}")
    print(f"  - test.csv: {os.path.join(base_dir, 'test.csv')}")

if __name__ == "__main__":
    main()