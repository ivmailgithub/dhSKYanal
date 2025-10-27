# got to do a python -m pip install opencv-python   before cv2 imports
import cv2
import numpy as np
import os
import zipfile
import json
from pathlib import Path
import argparse
from datetime import datetime
import tempfile
import shutil
import math

class StellariumLandscapeCreator:
    def __init__(self, video_path, output_dir="stellarium_landscape", landscape_name="CustomHorizon"):
        """
        Initialize the Stellarium landscape creator.
        
        Args:
            video_path (str): Path to the input video file
            output_dir (str): Directory to save the output landscape
            landscape_name (str): Name for the landscape
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.landscape_name = landscape_name
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Landscape directory structure
        self.landscape_dir = self.output_dir / landscape_name
        self.landscape_dir.mkdir(exist_ok=True)
        
    def extract_frames(self, max_frames=25, quality=0.8):
        """
        try 25 instead of 100 max_frames which produces 50 slots for my video and does not stitch them just concats
        Extract frames from the video for panorama stitching.
        
        Args:
            max_frames (int): Maximum number of frames to extract
            quality (float): JPEG quality (0-1)
        """
        print(f"Extracting frames from {self.video_path}...")
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames in video: {total_frames}")
        
        # Calculate frame interval to get evenly distributed frames
        if total_frames > max_frames:
            interval = total_frames // max_frames
        else:
            interval = 1
            
        frame_count = 0
        extracted_count = 0
        frames_dir = self.temp_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % interval == 0:
                # Resize frame for faster processing
                height, width = frame.shape[:2]
                if width > 1920:
                    scale = 1920 / width
                    frame = cv2.resize(frame, None, fx=scale, fy=scale)
                
                frame_path = frames_dir / f"frame_{extracted_count:04d}.jpg"
                cv2.imwrite(str(frame_path), frame, 
                           [int(cv2.IMWRITE_JPEG_QUALITY), int(quality * 100)])
                extracted_count += 1
                
                if extracted_count >= max_frames:
                    break
                    
            frame_count += 1
            
        cap.release()
        print(f"Extracted {extracted_count} frames")
        return frames_dir
    

    def create_panorama(self, frames_dir):
        """
        Create a panoramic image from extracted frames.
        
        Args:
            frames_dir (Path): Directory containing frame images
        """
        print("Creating panorama from frames...")
        
        # Get all frame paths
        frame_paths = sorted(frames_dir.glob("*.jpg"))
        if len(frame_paths) < 2:
            raise ValueError("Need at least 2 frames to create panorama")
        
        # Read images
        images = []
        for frame_path in frame_paths:
            img = cv2.imread(str(frame_path))
            if img is not None:
                images.append(img)
        
        print(f"Processing {len(images)} images for panorama...")
        
        # Initialize OpenCV's stitcher
        stitcher = cv2.Stitcher_create() if hasattr(cv2, 'Stitcher_create') else cv2.createStitcher()
        
        # Try to stitch images
        status, panorama = stitcher.stitch(images)
        
        if status != cv2.Stitcher_OK:
            print(f"Panorama stitching failed with status: {status}")
            print("Trying alternative approach...stitching fails for 50 frames")
            
            # Alternative: simple horizontal concatenation if stitching fails
            panorama = self.simple_horizontal_stitch(images)
        
        # Resize panorama to reasonable dimensions for Stellarium
        height, width = panorama.shape[:2]
        if width > 8192:  # Stellarium recommended max width
            scale = 8192 / width
            panorama = cv2.resize(panorama, None, fx=scale, fy=scale)
        
        # Save panorama
        panorama_path = self.landscape_dir / "panorama.png"
        cv2.imwrite(str(panorama_path), panorama)
        
        print(f"Panorama saved to: {panorama_path}")
        print(f"Panorama dimensions: {panorama.shape[1]}x{panorama.shape[0]}")
        
        return panorama_path
    
    def simple_horizontal_stitch(self, images):
        """
        Simple horizontal concatenation as fallback for panorama creation.
        
        Args:
            images (list): List of images to stitch
        """
        print("Using simple horizontal stitching...")
        
        # Resize all images to same height
        target_height = min(img.shape[0] for img in images)
        resized_images = []
        
        for img in images:
            height, width = img.shape[:2]
            if height != target_height:
                scale = target_height / height
                new_width = int(width * scale)
                img = cv2.resize(img, (new_width, target_height))
            resized_images.append(img)
        
        # Concatenate horizontally
        panorama = np.hstack(resized_images)
        
        # Make it 360° by duplicating and blending edges
        if panorama.shape[1] < 2048:  # Minimum width for decent panorama
            repeat_factor = 2048 // panorama.shape[1] + 1
            panorama = np.tile(panorama, (1, repeat_factor, 1))
            panorama = panorama[:, :2048, :]
        
        return panorama
    
    def create_horizon_file(self, panorama_path):
        """
        Create a horizon.txt file from the panorama image.
        """
        print("Creating horizon.txt file...")
        try:
            panorama = cv2.imread(str(panorama_path))
            if panorama is None:
                print("Could not read panorama image for horizon detection.")
                return

            height, width = panorama.shape[:2]
            gray = cv2.cvtColor(panorama, cv2.COLOR_BGR2GRAY)
            
            # Use Sobel to find edges
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
            
            horizon_points = []
            for x in range(width):
                # Find the y with the max sobel response
                column = sobel_y[:, x]
                if np.max(column) > 0:
                    y = np.argmax(column)
                else:
                    y = height // 2 # fallback to center
                
                # Convert pixel coordinates to azimuth and altitude
                # Azimuth: mapping so North is at the center of the image
                azimuth = ((x / width) * 360 + 180) % 360
                
                # Altitude: 90 at top, -90 at bottom
                altitude = 90 - (y / height) * 180
                
                horizon_points.append((azimuth, altitude))

            horizon_file_path = self.landscape_dir / "horizon.txt"
            with open(horizon_file_path, 'w') as f:
                for az, alt in horizon_points:
                    f.write(f"{az:.2f} {alt:.2f}\n")
            
            print(f"horizon.txt created at: {horizon_file_path}")
            return horizon_file_path

        except Exception as e:
            print(f"Could not create horizon file: {e}")
            return None

    def create_landscape_ini(self, panorama_path):
        """
        Create the landscape.ini file required by Stellarium.
        
        Args:
            panorama_path (Path): Path to the panorama image
        """
        print("Creating landscape.ini configuration...")
        
        ini_content = f"""[landscape]
name = {self.landscape_name}
type = spherical
author = Generated from video
description = Custom landscape created from phone video
maptex = {panorama_path.name}
maptex_top = 90
maptex_bottom = -90
maptex_fog = fog.png
maptex_fog_altitude = 200
maptex_fog_thickness = 0.2
maptex_ambient = 0.2
minimal_altitude = -15
minimal_brightness = 0.1
polygonal_horizon_line = true
polygonal_horizon_list = horizon.txt
location = 
"""
        
        ini_path = self.landscape_dir / "landscape.ini"
        with open(ini_path, 'w') as f:
            f.write(ini_content)
        
        print(f"landscape.ini created at: {ini_path}")
        return ini_path
    
    def create_fog_image(self):
        """
        Create a simple fog texture for the landscape.
        """
        print("Creating fog texture...")
        
        # Create a simple gradient fog image
        width, height = 512, 256
        fog_img = np.zeros((height, width, 3), dtype=np.uint8)
        
        for y in range(height):
            intensity = int(255 * (1 - y / height) * 0.3)  # Gradient from top to bottom
            fog_img[y, :] = [intensity, intensity, intensity]
        
        fog_path = self.landscape_dir / "fog.png"
        cv2.imwrite(str(fog_path), fog_img)
        
        print(f"Fog texture created at: {fog_path}")
        return fog_path
    
    def create_package(self):
        """
        Create a zip package of the landscape for easy installation in Stellarium.
        """
        print("Creating landscape package...")
        
        zip_path = self.output_dir / f"{self.landscape_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.landscape_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.landscape_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Landscape package created: {zip_path}")
        print(f"Package size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return zip_path
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_landscape(self, max_frames=75):
        """
        try max_frames 75 instead of 50
        Main method to create the complete Stellarium landscape.
        
        Args:
            max_frames (int): Maximum number of frames to extract from video
        """
        try:
            # Extract frames from video
            frames_dir = self.extract_frames(max_frames=max_frames)
            
            # Create panorama
            panorama_path = self.create_panorama(frames_dir)
            
            # Create fog texture
            self.create_fog_image()
            
            # Create horizon file
            self.create_horizon_file(panorama_path)
            
            # Create landscape.ini
            self.create_landscape_ini(panorama_path)
            
            # Create package
            package_path = self.create_package()
            
            print("\n" + "="*50)
            print("STELLARIUM LANDSCAPE CREATION COMPLETE!")
            print("="*50)
            print(f"Landscape name: {self.landscape_name}")
            print(f"Output directory: {self.output_dir}")
            print(f"Package file: {package_path}")
            print("\nTo install in Stellarium:")
            print("1. Copy the zip file to Stellarium's landscapes directory")
            print("   (usually: ~/.stellarium/landscapes/ on Linux)")
            print("   (usually: C:\\Program Files\\Stellarium\\landscapes\\ on Windows)")
            print("2. Extract the zip file in that directory")
            print("3. Restart Stellarium and select your landscape from the Sky View menu")
            print("="*50)
            
            return package_path
            
        except Exception as e:
            print(f"Error creating landscape: {e}")
            raise
        finally:
            self.cleanup()

def main():
    parser = argparse.ArgumentParser(
        description="Create a Stellarium landscape from a phone video of the local horizon"
    )
    parser.add_argument("video_path", help="Path to the input video file")
    parser.add_argument("-o", "--output", default="stellarium_landscape", 
                       help="Output directory (default: stellarium_landscape)")
    parser.add_argument("-n", "--name", default="CustomHorizon", 
                       help="Name for the landscape (default: CustomHorizon)")
    parser.add_argument("-f", "--frames", type=int, default=75,
                       help="Maximum frames to extract (default: 75)")
    
    args = parser.parse_args()
    
    # Validate input video
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        return
    
    # Create landscape
    creator = StellariumLandscapeCreator(
        video_path=args.video_path,
        output_dir=args.output,
        landscape_name=args.name
    )

    try:
        creator.create_landscape(max_frames=args.frames)
    except Exception as e:
        print(f"Failed to create landscape: {e}")
        return

if __name__ == "__main__":
    main()