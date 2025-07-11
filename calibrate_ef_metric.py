#!/usr/bin/env python3
"""
Utility script for empirical calibration of the Ef metric.

This script helps you calibrate the Ef normalization factor based on your actual
speckle pattern images. Run this with a set of good quality speckle images to
determine the optimal Ef normalization parameters.

Usage:
    python calibrate_ef_metric.py path/to/speckle/images/
    python calibrate_ef_metric.py image1.jpg image2.png image3.tiff
"""

import os
import sys
import glob
import argparse
import numpy as np
import cv2
import logging
from pathlib import Path
from core.quality_calculator import QualityCalculator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_image(image_path):
    """Load and validate an image."""
    try:
        image = cv2.imread(str(image_path))
        if image is None:
            logger.warning(f"Could not load image: {image_path}")
            return None
        
        # Convert BGR to RGB if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    except Exception as e:
        logger.warning(f"Error loading {image_path}: {e}")
        return None

def collect_images(paths):
    """Collect all valid images from the given paths."""
    images = []
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
    
    for path in paths:
        path = Path(path)
        
        if path.is_file():
            # Single file
            if path.suffix.lower() in image_extensions:
                img = load_image(path)
                if img is not None:
                    images.append((str(path), img))
                    logger.info(f"Loaded: {path.name}")
            else:
                logger.warning(f"Unsupported file type: {path}")
                
        elif path.is_dir():
            # Directory - find all images
            for ext in image_extensions:
                pattern = str(path / f"*{ext}")
                for img_path in glob.glob(pattern):
                    img = load_image(img_path)
                    if img is not None:
                        images.append((img_path, img))
                        logger.info(f"Loaded: {Path(img_path).name}")
        else:
            logger.warning(f"Path not found: {path}")
    
    return images

def analyze_ef_distribution(images):
    """Analyze the distribution of Ef values in the image set."""
    logger.info("Analyzing Ef value distribution...")
    
    ef_values = []
    mig_values = []
    
    for img_path, image in images:
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # Calculate gradients
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            grad_xx = cv2.Sobel(grad_x, cv2.CV_64F, 1, 0, ksize=3)
            grad_yy = cv2.Sobel(grad_y, cv2.CV_64F, 0, 1, ksize=3)
            grad_xy = cv2.Sobel(grad_x, cv2.CV_64F, 0, 1, ksize=3)
            
            # Calculate MIG and Ef
            first_order_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)
            second_order_magnitude = np.sqrt(grad_xx ** 2 + grad_yy ** 2 + 2 * grad_xy ** 2)
            
            mig = np.mean(first_order_magnitude)
            
            alpha = 0.7
            beta = 0.3
            ef = alpha * np.mean(first_order_magnitude) + beta * np.mean(second_order_magnitude)
            
            ef_values.append(ef)
            mig_values.append(mig)
            
            logger.info(f"  {Path(img_path).name}: MIG={mig:.2f}, Ef={ef:.2f}")
            
        except Exception as e:
            logger.warning(f"Error processing {img_path}: {e}")
            continue
    
    return np.array(ef_values), np.array(mig_values)

def recommend_calibration(ef_values, mig_values, target_range=(0.3, 0.8)):
    """Recommend calibration parameters based on the analysis."""
    if len(ef_values) == 0:
        logger.error("No valid Ef values to analyze")
        return None
    
    # Calculate statistics
    ef_stats = {
        'min': np.min(ef_values),
        'max': np.max(ef_values),
        'mean': np.mean(ef_values),
        'median': np.median(ef_values),
        'std': np.std(ef_values),
        'p25': np.percentile(ef_values, 25),
        'p75': np.percentile(ef_values, 75),
        'p90': np.percentile(ef_values, 90)
    }
    
    mig_stats = {
        'min': np.min(mig_values),
        'max': np.max(mig_values),
        'mean': np.mean(mig_values),
        'median': np.median(mig_values),
        'std': np.std(mig_values),
        'p25': np.percentile(mig_values, 25),
        'p75': np.percentile(mig_values, 75),
        'p90': np.percentile(mig_values, 90)
    }
    
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\nEf Statistics (n={len(ef_values)}):")
    print(f"  Min:    {ef_stats['min']:.2f}")
    print(f"  25th:   {ef_stats['p25']:.2f}")
    print(f"  Median: {ef_stats['median']:.2f}")
    print(f"  Mean:   {ef_stats['mean']:.2f}")
    print(f"  75th:   {ef_stats['p75']:.2f}")
    print(f"  90th:   {ef_stats['p90']:.2f}")
    print(f"  Max:    {ef_stats['max']:.2f}")
    print(f"  Std:    {ef_stats['std']:.2f}")
    
    print(f"\nMIG Statistics (n={len(mig_values)}):")
    print(f"  Min:    {mig_stats['min']:.2f}")
    print(f"  25th:   {mig_stats['p25']:.2f}")
    print(f"  Median: {mig_stats['median']:.2f}")
    print(f"  Mean:   {mig_stats['mean']:.2f}")
    print(f"  75th:   {mig_stats['p75']:.2f}")
    print(f"  90th:   {mig_stats['p90']:.2f}")
    print(f"  Max:    {mig_stats['max']:.2f}")
    print(f"  Std:    {mig_stats['std']:.2f}")
    
    # Recommend calibration parameters
    print("\n" + "="*60)
    print("CALIBRATION RECOMMENDATIONS")
    print("="*60)
    
    # For Ef normalization, use different strategies
    target_mid = (target_range[0] + target_range[1]) / 2
    
    strategies = {
        'Conservative (75th percentile)': ef_stats['p75'] / target_mid,
        'Balanced (median)': ef_stats['median'] / target_mid,
        'Aggressive (mean)': ef_stats['mean'] / target_mid,
    }
    
    print(f"\nEf Normalization Factor Recommendations:")
    print(f"Target normalized range: {target_range[0]:.1f} - {target_range[1]:.1f}")
    
    for strategy, factor in strategies.items():
        print(f"  {strategy}: {factor:.1f}")
    
    # Check MIG range
    print(f"\nMIG Range Analysis:")
    if mig_stats['max'] <= 50:
        print(f"  ✓ MIG values are within expected range (max: {mig_stats['max']:.1f} ≤ 50)")
        print(f"  ✓ Current MIG normalization factor (50.0) is appropriate")
    else:
        print(f"  ⚠ MIG values exceed expected range (max: {mig_stats['max']:.1f} > 50)")
        recommended_mig_factor = mig_stats['p90'] / 0.8  # Map 90th percentile to 0.8
        print(f"  → Consider increasing MIG normalization factor to {recommended_mig_factor:.1f}")
    
    # Provide code snippet
    recommended_ef_factor = ef_stats['p75'] / target_mid
    
    print(f"\n" + "="*60)
    print("IMPLEMENTATION")
    print("="*60)
    
    print(f"\nTo apply the recommended calibration, use:")
    print(f"```python")
    print(f"from core.quality_calculator import QualityCalculator")
    print(f"")
    print(f"calc = QualityCalculator()")
    print(f"calc.set_scoring_calibration(")
    print(f"    ef_normalization_factor={recommended_ef_factor:.1f}")
    if mig_stats['max'] > 50:
        recommended_mig_factor = mig_stats['p90'] / 0.8
        print(f"    mig_normalization_factor={recommended_mig_factor:.1f}")
    print(f")")
    print(f"```")
    
    return {
        'ef_stats': ef_stats,
        'mig_stats': mig_stats,
        'recommended_ef_factor': recommended_ef_factor,
        'recommended_mig_factor': mig_stats['p90'] / 0.8 if mig_stats['max'] > 50 else 50.0
    }

def main():
    parser = argparse.ArgumentParser(
        description="Calibrate Ef metric based on sample speckle images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python calibrate_ef_metric.py /path/to/speckle/images/
  python calibrate_ef_metric.py image1.jpg image2.png image3.tiff
  python calibrate_ef_metric.py --target-range 0.4 0.7 /path/to/images/
        """
    )
    
    parser.add_argument('paths', nargs='+', help='Image files or directories containing speckle images')
    parser.add_argument('--target-range', nargs=2, type=float, default=[0.3, 0.8],
                       metavar=('MIN', 'MAX'), help='Target range for normalized Ef values (default: 0.3 0.8)')
    parser.add_argument('--test-calibration', action='store_true',
                       help='Test the recommended calibration on the sample images')
    
    args = parser.parse_args()
    
    if not args.paths:
        parser.print_help()
        return
    
    # Collect images
    logger.info("Collecting images...")
    images = collect_images(args.paths)
    
    if not images:
        logger.error("No valid images found")
        return
    
    logger.info(f"Found {len(images)} valid images")
    
    # Analyze Ef distribution
    ef_values, mig_values = analyze_ef_distribution(images)
    
    if len(ef_values) == 0:
        logger.error("No valid Ef values calculated")
        return
    
    # Get recommendations
    results = recommend_calibration(ef_values, mig_values, tuple(args.target_range))
    
    if args.test_calibration and results:
        print(f"\n" + "="*60)
        print("TESTING CALIBRATION")
        print("="*60)
        
        # Test the calibration
        calc = QualityCalculator()
        calc.set_scoring_calibration(
            ef_normalization_factor=results['recommended_ef_factor'],
            mig_normalization_factor=results['recommended_mig_factor']
        )
        
        print(f"\nQuality scores with recommended calibration:")
        print("-" * 50)
        
        for img_path, image in images[:5]:  # Test first 5 images
            result = calc.calculate_quality_score(image)
            gradient_metrics = result['gradient_metrics']
            
            print(f"{Path(img_path).name}:")
            print(f"  Overall: {result['overall_score']:.1f}")
            print(f"  Ef (normalized): {gradient_metrics['normalized_ef']:.3f}")
            print(f"  MIG (normalized): {gradient_metrics['normalized_mig']:.3f}")

if __name__ == "__main__":
    main()