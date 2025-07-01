#!/usr/bin/env python3
"""
Test script to verify ROI analysis optimization.
This script tests the performance improvement when analyzing ROI vs full image.
"""

import numpy as np
import time
import cv2
from core.image_analyzer import ImageAnalyzer
from models.roi_data import ROIData

def create_test_image(size=(2000, 2000)):
    """Create a test image with speckle pattern."""
    # Create base image
    image = np.random.randint(0, 256, size, dtype=np.uint8)
    
    # Add some structure with Gaussian blur
    image = cv2.GaussianBlur(image, (5, 5), 1.0)
    
    # Add some high-frequency content
    noise = np.random.randint(-50, 50, size, dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return image

def create_small_roi(image_shape, roi_size_fraction=0.1):
    """Create a small ROI in the center of the image."""
    h, w = image_shape
    
    # Calculate ROI size (fraction of image)
    roi_h = int(h * roi_size_fraction)
    roi_w = int(w * roi_size_fraction)
    
    # Center the ROI
    center_y, center_x = h // 2, w // 2
    y1 = center_y - roi_h // 2
    y2 = center_y + roi_h // 2
    x1 = center_x - roi_w // 2
    x2 = center_x + roi_w // 2
    
    # Create rectangular ROI
    coordinates = [
        (x1, y1), (x2, y1), (x2, y2), (x1, y2)
    ]
    
    return ROIData(coordinates=coordinates, roi_type='rectangle')

def test_analysis_performance():
    """Test the performance difference between full image and ROI analysis."""
    print("Creating test image...")
    image = create_test_image((2000, 2000))
    print(f"Test image size: {image.shape}")
    
    # Create small ROI (10% of image area)
    roi = create_small_roi(image.shape, roi_size_fraction=0.1)
    roi_area = roi.calculate_area()
    total_area = image.shape[0] * image.shape[1]
    roi_percentage = (roi_area / total_area) * 100
    print(f"ROI size: {roi_area:.0f} pixels ({roi_percentage:.1f}% of image)")
    
    analyzer = ImageAnalyzer()
    
    print("\n" + "="*50)
    print("Testing FULL IMAGE analysis...")
    start_time = time.time()
    result_full = analyzer.analyze_image(image, roi=None)
    full_time = time.time() - start_time
    print(f"Full image analysis time: {full_time:.2f} seconds")
    print(f"Overall score: {result_full.overall_score:.1f}")
    
    print("\n" + "="*50)
    print("Testing ROI analysis...")
    start_time = time.time()
    result_roi = analyzer.analyze_image(image, roi=roi)
    roi_time = time.time() - start_time
    print(f"ROI analysis time: {roi_time:.2f} seconds")
    print(f"Overall score: {result_roi.overall_score:.1f}")
    
    print("\n" + "="*50)
    print("PERFORMANCE COMPARISON:")
    print(f"Full image time: {full_time:.2f}s")
    print(f"ROI analysis time: {roi_time:.2f}s")
    if roi_time > 0:
        speedup = full_time / roi_time
        print(f"Speedup: {speedup:.1f}x faster")
        print(f"Time reduction: {((full_time - roi_time) / full_time * 100):.1f}%")
    
    # Verify that ROI analysis is working correctly
    print(f"\nROI area: {roi_percentage:.1f}% of image")
    print(f"Expected speedup should be significant for such a small ROI")
    
    return full_time, roi_time

if __name__ == "__main__":
    try:
        test_analysis_performance()
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()