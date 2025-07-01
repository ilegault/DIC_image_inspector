#!/usr/bin/env python3
"""
Test script to verify ROI-based analysis functionality.
"""

import numpy as np
import time
from models.roi_data import ROIData
from core.image_analyzer import ImageAnalyzer

def test_roi_analysis():
    """Test ROI-based vs full image analysis."""
    
    # Create a test image
    print("Creating test image...")
    test_image = np.random.randint(0, 255, (1000, 1000), dtype=np.uint8)
    
    # Add some texture to make it more realistic
    for i in range(0, 1000, 50):
        for j in range(0, 1000, 50):
            test_image[i:i+25, j:j+25] = np.random.randint(100, 200)
    
    # Create a small ROI (10% of image)
    roi_coords = [(200, 200), (400, 200), (400, 400), (200, 400)]
    roi = ROIData(coordinates=roi_coords, roi_type='rectangle')
    
    print(f"Test image shape: {test_image.shape}")
    print(f"ROI area: {roi.calculate_area():.0f} pixels")
    print(f"ROI percentage: {roi.get_percentage_of_image(test_image.shape):.1f}%")
    
    # Initialize analyzer
    analyzer = ImageAnalyzer()
    
    # Test full image analysis
    print("\n--- Full Image Analysis ---")
    start_time = time.time()
    full_result = analyzer.analyze_image(test_image, roi=None)
    full_time = time.time() - start_time
    print(f"Full image analysis time: {full_time:.2f} seconds")
    print(f"Full image score: {full_result.overall_score:.1f}")
    
    # Test ROI-based analysis
    print("\n--- ROI-Based Analysis ---")
    start_time = time.time()
    roi_result = analyzer.analyze_image(test_image, roi=roi)
    roi_time = time.time() - start_time
    print(f"ROI analysis time: {roi_time:.2f} seconds")
    print(f"ROI score: {roi_result.overall_score:.1f}")
    
    # Compare results
    print(f"\n--- Performance Comparison ---")
    print(f"Speed improvement: {full_time / roi_time:.1f}x faster")
    print(f"Analysis method: {roi_result.analysis_method}")
    
    # Check quality map dimensions
    print(f"\n--- Quality Map Info ---")
    print(f"Full quality map shape: {full_result.quality_map.shape}")
    print(f"ROI quality map shape: {roi_result.quality_map.shape}")
    
    # Check if ROI quality map has values only in ROI region
    roi_mask = roi.create_mask(test_image.shape)
    roi_pixels = roi_mask > 0
    non_roi_pixels = roi_mask == 0
    
    roi_quality_in_roi = np.sum(roi_result.quality_map[roi_pixels] > 0)
    roi_quality_outside_roi = np.sum(roi_result.quality_map[non_roi_pixels] > 0)
    
    print(f"Quality values in ROI region: {roi_quality_in_roi}")
    print(f"Quality values outside ROI: {roi_quality_outside_roi}")
    
    if roi_quality_outside_roi == 0:
        print("✓ SUCCESS: Analysis correctly limited to ROI region!")
    else:
        print("⚠ WARNING: Analysis may not be properly limited to ROI")
    
    return roi_time < full_time

if __name__ == "__main__":
    try:
        success = test_roi_analysis()
        if success:
            print("\n✓ ROI functionality test PASSED")
        else:
            print("\n✗ ROI functionality test FAILED")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()