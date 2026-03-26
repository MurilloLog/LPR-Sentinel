"""
Image Resizing and Dataset Splitting for License Plate Recognition

This script processes images from an augmented dataset, resizes them to a target
dimension (140x70 pixels), and creates train/val/test splits with corresponding
CSV annotation files. Images are organized into train/val/test subfolders.

The script expects images in subdirectories under the input folder, with filenames
following the pattern: {plate_text}_[anything].jpg (e.g., ABC123_variation_001.jpg)
"""

import os
import cv2
import csv
import random
import shutil
from tqdm import tqdm

def main():
    """
    Main execution function that processes images and creates dataset splits.
    
    The function performs the following steps:
    1. Defines input/output directories and target image size
    2. Recursively walks through input directory to find all images
    3. Resizes each image to target dimensions
    4. Saves resized images in train/val/test subfolders based on split
    5. Creates train/val/test splits (80/10/10)
    6. Generates CSV annotation files for each split with paths to the subfolders
    """
    
    # Get the directory where the script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input directory containing augmented images
    # Relative path: ../MLP-Augmentator/augmented_dataset/
    img_root = os.path.join(base_dir, "../MLP-Augmentator/augmented_dataset/")
    
    # Output directory for resized images
    resized_root = os.path.join(base_dir, "140x70_dataset")
    
    # Create train/val/test subdirectories
    train_dir = os.path.join(resized_root, "train")
    val_dir = os.path.join(resized_root, "val")
    test_dir = os.path.join(resized_root, "test")
    
    # Create all directories
    for dir_path in [resized_root, train_dir, val_dir, test_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    # Target dimensions as specified in config.yaml
    target_size = (140, 70)  # width, height
    
    # Dataset split proportions
    train_split = 0.8
    val_split = 0.1
    test_split = 0.1
    
    # List to store all annotations with their original paths
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
    
    # Recursively walk through input directory to collect all images
    for root, _, files in os.walk(img_root):
        for img_name in files:
            if img_name.lower().endswith((".jpg", ".png", ".jpeg")):
                # Extract license plate text (everything before first underscore)
                plate = img_name.split("_")[0]
                
                # Store full path and plate text
                img_path = os.path.join(root, img_name)
                annotations.append([img_path, plate])
    
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
    
    def process_split(data, split_name, output_dir):
        """
        Process images for a specific split (train/val/test).
        
        Args:
            data (list): List of [image_path, plate_text] pairs
            split_name (str): Name of the split ('train', 'val', or 'test')
            output_dir (str): Directory to save the processed images
        """
        split_annotations = []
        
        print(f"\nProcessing {split_name} split ({len(data)} images)...")
        
        for img_path, plate in tqdm(data, desc=f"  {split_name}", unit="img"):
            # Read and resize image
            img = cv2.imread(img_path)
            
            if img is None:
                tqdm.write(f"Warning: Could not read image {img_path}, skipping...")
                continue
            
            # Resize to target dimensions
            resized = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
            
            # Generate output filename
            # Get original filename without path
            original_filename = os.path.basename(img_path)
            # Add a prefix to avoid collisions if needed
            output_filename = original_filename
            
            # Save in split-specific directory
            save_path = os.path.join(output_dir, output_filename)
            
            # Handle filename collisions by adding a number if file exists
            counter = 1
            while os.path.exists(save_path):
                name, ext = os.path.splitext(original_filename)
                output_filename = f"{name}_{counter}{ext}"
                save_path = os.path.join(output_dir, output_filename)
                counter += 1
            
            # Save the resized image
            cv2.imwrite(save_path, resized)
            
            # Store annotation with path relative to base_dir
            relative_to_base = os.path.relpath(save_path, base_dir)
            relative_to_base = relative_to_base.replace(os.sep, '/')
            split_annotations.append([relative_to_base, plate])
        
        return split_annotations
    
    def write_csv(filename, data, split_name):
        """
        Write annotation data to a CSV file.
        
        Args:
            filename (str): Name of the CSV file to create
            data (list): List of [image_path, plate_text] pairs
            split_name (str): Name of the split for reporting
        """
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "plate_text"])  # Write header
            writer.writerows(data)
        print(f"Generated {filename} with {len(data)} entries for {split_name} set")
        
        # Verify first entry path exists
        if data and len(data) > 0:
            test_path = os.path.join(base_dir, data[0][0])
            if os.path.exists(test_path):
                print(f"   Verified first image exists")
            else:
                print(f"   Warning: First image path does not exist")
    
    # Process each split
    print("\n" + "=" * 50)
    print("PROCESSING IMAGES BY SPLIT")
    print("=" * 50)
    
    train_annotations = process_split(train_data, "train", train_dir)
    val_annotations = process_split(val_data, "val", val_dir)
    test_annotations = process_split(test_data, "test", test_dir)
    
    # Generate CSV files for each split
    print("\n" + "=" * 50)
    print("CREATING CSV FILES")
    print("=" * 50)
    
    write_csv("train.csv", train_annotations, "train")
    write_csv("val.csv", val_annotations, "val")
    write_csv("test.csv", test_annotations, "test")
    
    # Print summary
    print("\n" + "=" * 50)
    print("PROCESSING SUMMARY")
    print("=" * 50)
    print(f"Total images processed: {total}")
    print(f"Train set size: {len(train_annotations)} ({train_split*100:.0f}%)")
    print(f"Validation set size: {len(val_annotations)} ({val_split*100:.0f}%)")
    print(f"Test set size: {len(test_annotations)} ({test_split*100:.0f}%)")
    print("\nOutput directories:")
    print(f"  - Train images: {train_dir}")
    print(f"  - Validation images: {val_dir}")
    print(f"  - Test images: {test_dir}")
    print("\nOutput files:")
    print(f"  - train.csv: {os.path.join(base_dir, 'train.csv')}")
    print(f"  - val.csv: {os.path.join(base_dir, 'val.csv')}")
    print(f"  - test.csv: {os.path.join(base_dir, 'test.csv')}")

if __name__ == "__main__":
    main()