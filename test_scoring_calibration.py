#!/usr/bin/env python3
"""
Test script for the updated MIG and Ef scoring calibration.

This script demonstrates:
1. The updated MIG normalization (divide by 50 instead of 255)
2. The configurable Ef normalization for empirical calibration
3. Methods to calibrate Ef based on sample images
"""

import numpy as np
import cv2
import logging
from core.quality_calculator import QualityCalculator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_speckle_pattern(size=(256, 256), speckle_density=0.3, noise_level=0.1):
    """Create a synthetic speckle pattern for testing."""
    # Create base pattern
    pattern = np.random.random(size).astype(np.float32)
    
    # Add speckle-like features
    kernel = cv2.getGaussianKernel(5, 1.5)
    kernel = kernel @ kernel.T
    pattern = cv2.filter2D(pattern, -1, kernel)
    
    # Add some noise
    noise = np.random.normal(0, noise_level, size).astype(np.float32)
    pattern += noise
    
    # Normalize to 0-255 range
    pattern = ((pattern - pattern.min()) / (pattern.max() - pattern.min()) * 255).astype(np.uint8)
    
    return pattern

def test_scoring_calibration():
    """Test the updated scoring calibration."""
    print("=== Testing Updated MIG and Ef Scoring Calibration ===\n")
    
    # Create quality calculator
    calc = QualityCalculator()
    
    # Show current calibration parameters
    calibration = calc.get_scoring_calibration()
    print("Current scoring calibration parameters:")
    for key, value in calibration.items():
        print(f"  {key}: {value}")
    print()
    
    # Create test images with different quality levels
    test_images = {
        'good_speckle': create_test_speckle_pattern(speckle_density=0.4, noise_level=0.05),
        'medium_speckle': create_test_speckle_pattern(speckle_density=0.2, noise_level=0.1),
        'poor_speckle': create_test_speckle_pattern(speckle_density=0.1, noise_level=0.2),
    }
    
    print("Testing quality calculation with updated calibration:")
    print("-" * 60)
    
    for name, image in test_images.items():
        # Calculate quality
        result = calc.calculate_quality_score(image)
        gradient_metrics = result['gradient_metrics']
        
        print(f"\n{name.upper()}:")
        print(f"  Overall Score: {result['overall_score']:.1f}")
        print(f"  MIG (raw): {gradient_metrics['mig']:.2f}")
        print(f"  MIG (normalized): {gradient_metrics['normalized_mig']:.3f}")
        print(f"  MIG Score: {gradient_metrics['mig_score']:.3f}")
        print(f"  Ef (raw): {gradient_metrics['ef']:.2f}")
        print(f"  Ef (normalized): {gradient_metrics['normalized_ef']:.3f}")
        print(f"  Ef Score: {gradient_metrics['ef_score']:.3f}")
        print(f"  Gradient Score: {gradient_metrics['score']:.3f}")
    
    print("\n" + "=" * 60)
    print("EMPIRICAL CALIBRATION DEMONSTRATION")
    print("=" * 60)
    
    # Demonstrate empirical calibration
    sample_images = [test_images['good_speckle'], test_images['medium_speckle']]
    
    print(f"\nBefore Ef calibration:")
    print(f"  Ef normalization factor: {calc.ef_normalization_factor:.2f}")
    
    # Calibrate Ef based on sample images
    calc.calibrate_ef_from_samples(sample_images, target_ef_range=(0.4, 0.7))
    
    print(f"\nAfter Ef calibration:")
    print(f"  Ef normalization factor: {calc.ef_normalization_factor:.2f}")
    
    # Test with updated calibration
    print("\nQuality scores after Ef calibration:")
    print("-" * 40)
    
    for name, image in test_images.items():
        result = calc.calculate_quality_score(image)
        gradient_metrics = result['gradient_metrics']
        
        print(f"{name}: Overall={result['overall_score']:.1f}, "
              f"Ef_norm={gradient_metrics['normalized_ef']:.3f}, "
              f"Ef_score={gradient_metrics['ef_score']:.3f}")
    
    print("\n" + "=" * 60)
    print("MANUAL CALIBRATION DEMONSTRATION")
    print("=" * 60)
    
    # Demonstrate manual calibration adjustment
    print("\nTesting manual calibration adjustment...")
    
    # Set custom calibration parameters
    calc.set_scoring_calibration(
        ef_normalization_factor=80.0,  # Custom Ef normalization
        ef_score_multiplier=1.2        # Custom Ef score multiplier
    )
    
    print("Quality scores with custom calibration:")
    print("-" * 40)
    
    for name, image in test_images.items():
        result = calc.calculate_quality_score(image)
        gradient_metrics = result['gradient_metrics']
        
        print(f"{name}: Overall={result['overall_score']:.1f}, "
              f"Ef_norm={gradient_metrics['normalized_ef']:.3f}, "
              f"Ef_score={gradient_metrics['ef_score']:.3f}")

def compare_old_vs_new_normalization():
    """Compare old (255) vs new (50) MIG normalization."""
    print("\n" + "=" * 60)
    print("COMPARING OLD vs NEW MIG NORMALIZATION")
    print("=" * 60)
    
    # Create a test image
    test_image = create_test_speckle_pattern()
    
    # Calculate gradients manually
    grad_x = cv2.Sobel(test_image, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(test_image, cv2.CV_64F, 0, 1, ksize=3)
    first_order_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
    mig = np.mean(first_order_magnitude)
    
    # Compare normalizations
    old_normalized = mig / 255.0
    new_normalized = mig / 50.0
    
    old_score = min(1.0, old_normalized * 6)
    new_score = min(1.0, new_normalized * 1.2)
    
    print(f"Raw MIG value: {mig:.2f}")
    print(f"Old normalization (÷255): {old_normalized:.4f} → score: {old_score:.4f}")
    print(f"New normalization (÷50):  {new_normalized:.4f} → score: {new_score:.4f}")
    print(f"Score ratio (new/old): {new_score/old_score:.2f}")

if __name__ == "__main__":
    test_scoring_calibration()
    compare_old_vs_new_normalization()
    
    print("\n" + "=" * 60)
    print("CALIBRATION UPDATE COMPLETE")
    print("=" * 60)
    print("\nKey changes made:")
    print("1. MIG normalization: 255 → 50 (based on typical range for good speckle patterns)")
    print("2. MIG score multiplier: 6 → 1.2 (adjusted for new normalization)")
    print("3. Ef normalization: 255 → 100 (initial estimate, configurable)")
    print("4. Ef score multiplier: 4 → 1.0 (initial value, configurable)")
    print("5. Added methods for empirical calibration of Ef metric")
    print("\nNext steps:")
    print("- Test with your actual speckle pattern images")
    print("- Use calibrate_ef_from_samples() with good quality images")
    print("- Fine-tune Ef parameters based on empirical results")