#!/usr/bin/env python3
"""
Test script for debugging quality map generation issues.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from analysis.quality_map.debug_generator import DebugQualityMapGenerator
from analysis.quality_map.generator import QualityMapGenerator


def create_test_image(size=(400, 400), pattern_type='speckle'):
    """Create a test image with known characteristics."""
    print(f"Creating test image: {size}, pattern: {pattern_type}")
    
    if pattern_type == 'speckle':
        # Create speckle pattern similar to DIC
        image = np.random.rand(*size) * 255
        image = cv2.GaussianBlur(image.astype(np.uint8), (3, 3), 1.0)
        
        # Add some structure
        y, x = np.ogrid[:size[0], :size[1]]
        center_y, center_x = size[0] // 2, size[1] // 2
        
        # Add circular gradient
        distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        gradient = np.exp(-distance / (size[0] * 0.3))
        
        image = image.astype(float) * (0.5 + 0.5 * gradient)
        image = np.clip(image, 0, 255).astype(np.uint8)
        
    elif pattern_type == 'gradient':
        # Simple gradient
        image = np.zeros(size, dtype=np.uint8)
        for i in range(size[0]):
            image[i, :] = int(255 * i / size[0])
            
    elif pattern_type == 'checkerboard':
        # Checkerboard pattern
        image = np.zeros(size, dtype=np.uint8)
        square_size = 20
        for i in range(0, size[0], square_size):
            for j in range(0, size[1], square_size):
                if ((i // square_size) + (j // square_size)) % 2 == 0:
                    image[i:i+square_size, j:j+square_size] = 255
                    
    elif pattern_type == 'noise':
        # Pure noise
        image = np.random.randint(0, 256, size, dtype=np.uint8)
        
    else:  # uniform
        # Uniform gray
        image = np.full(size, 128, dtype=np.uint8)
    
    print(f"Test image created: shape={image.shape}, range={image.min()}-{image.max()}")
    return image


def test_quality_map_generation():
    """Test quality map generation with debugging."""
    print("=== QUALITY MAP DEBUG TEST ===\n")
    
    # Create debug generator
    debug_gen = DebugQualityMapGenerator()
    
    # Create regular generator for comparison
    regular_gen = QualityMapGenerator()
    
    # Test different image types
    test_patterns = ['speckle', 'gradient', 'checkerboard', 'noise', 'uniform']
    spectrum_types = ['custom_dic', 'zeiss_style_dic']
    
    results = {}
    
    for pattern in test_patterns:
        print(f"\n{'='*50}")
        print(f"TESTING PATTERN: {pattern.upper()}")
        print(f"{'='*50}")
        
        # Create test image
        test_image = create_test_image(size=(200, 200), pattern_type=pattern)
        
        for spectrum in spectrum_types:
            print(f"\n--- Testing {spectrum} spectrum ---")
            
            try:
                # Debug generation
                quality_map_debug, viz_debug, debug_info = debug_gen.generate_with_debug(
                    test_image, spectrum_type=spectrum, subset_size=21, step_size=5
                )
                
                # Regular generation for comparison
                quality_map_regular, viz_regular = regular_gen.generate(
                    test_image, spectrum_type=spectrum, subset_size=21, step_size=5
                )
                
                # Compare results
                print(f"\nCOMPARISON:")
                print(f"Debug quality map: {quality_map_debug.shape}, range: {quality_map_debug.min():.4f}-{quality_map_debug.max():.4f}")
                print(f"Regular quality map: {quality_map_regular.shape}, range: {quality_map_regular.min():.4f}-{quality_map_regular.max():.4f}")
                
                # Check if they're similar
                if quality_map_debug.shape == quality_map_regular.shape:
                    diff = np.abs(quality_map_debug - quality_map_regular)
                    print(f"Difference: mean={diff.mean():.6f}, max={diff.max():.6f}")
                
                # Store results
                key = f"{pattern}_{spectrum}"
                results[key] = {
                    'debug_quality_map': quality_map_debug,
                    'debug_visualization': viz_debug,
                    'regular_quality_map': quality_map_regular,
                    'regular_visualization': viz_regular,
                    'debug_info': debug_info,
                    'test_image': test_image
                }
                
                # Save debug report
                debug_report_path = f"debug_report_{pattern}_{spectrum}.txt"
                debug_gen.save_debug_report(debug_info, debug_report_path)
                
                print(f"✓ Test completed successfully")
                
            except Exception as e:
                print(f"✗ Test failed: {e}")
                import traceback
                traceback.print_exc()
    
    return results


def create_comparison_plots(results):
    """Create comparison plots for visual inspection."""
    print(f"\n=== CREATING COMPARISON PLOTS ===")
    
    for key, data in results.items():
        pattern, spectrum = key.split('_', 1)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle(f'Quality Map Analysis: {pattern.title()} Pattern - {spectrum}', fontsize=16)
        
        # Original image
        axes[0, 0].imshow(data['test_image'], cmap='gray')
        axes[0, 0].set_title('Original Image')
        axes[0, 0].axis('off')
        
        # Debug quality map
        im1 = axes[0, 1].imshow(data['debug_quality_map'], cmap='viridis', vmin=0, vmax=1)
        axes[0, 1].set_title('Debug Quality Map')
        axes[0, 1].axis('off')
        plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)
        
        # Regular quality map
        im2 = axes[0, 2].imshow(data['regular_quality_map'], cmap='viridis', vmin=0, vmax=1)
        axes[0, 2].set_title('Regular Quality Map')
        axes[0, 2].axis('off')
        plt.colorbar(im2, ax=axes[0, 2], fraction=0.046, pad=0.04)
        
        # Debug visualization
        axes[1, 0].imshow(data['debug_visualization'])
        axes[1, 0].set_title('Debug Visualization')
        axes[1, 0].axis('off')
        
        # Regular visualization
        axes[1, 1].imshow(data['regular_visualization'])
        axes[1, 1].set_title('Regular Visualization')
        axes[1, 1].axis('off')
        
        # Difference map
        if data['debug_quality_map'].shape == data['regular_quality_map'].shape:
            diff = np.abs(data['debug_quality_map'] - data['regular_quality_map'])
            im3 = axes[1, 2].imshow(diff, cmap='hot')
            axes[1, 2].set_title('Difference Map')
            axes[1, 2].axis('off')
            plt.colorbar(im3, ax=axes[1, 2], fraction=0.046, pad=0.04)
        else:
            axes[1, 2].text(0.5, 0.5, 'Shape Mismatch', ha='center', va='center', transform=axes[1, 2].transAxes)
            axes[1, 2].set_title('Difference Map')
            axes[1, 2].axis('off')
        
        plt.tight_layout()
        
        # Save plot
        plot_filename = f"quality_comparison_{pattern}_{spectrum}.png"
        plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
        print(f"Saved comparison plot: {plot_filename}")
        
        plt.close()


def create_legends():
    """Create legend images for both spectrum types."""
    print(f"\n=== CREATING LEGENDS ===")
    
    debug_gen = DebugQualityMapGenerator()
    
    for spectrum_type in ['custom_dic', 'zeiss_style_dic']:
        legend_path = f"legend_{spectrum_type}.png"
        legend_array = debug_gen.create_legend(spectrum_type, legend_path)
        print(f"Created legend for {spectrum_type}: {legend_array.shape}")


def analyze_subset_scores(results):
    """Analyze subset score distributions."""
    print(f"\n=== ANALYZING SUBSET SCORES ===")
    
    for key, data in results.items():
        pattern, spectrum = key.split('_', 1)
        debug_info = data['debug_info']
        
        if 'subset_scores' in debug_info:
            scores = debug_info['subset_scores']
            print(f"\n{pattern.upper()} - {spectrum}:")
            print(f"  Total subsets: {len(scores)}")
            if scores:
                print(f"  Score range: {min(scores):.4f} - {max(scores):.4f}")
                print(f"  Score mean: {np.mean(scores):.4f}")
                print(f"  Score std: {np.std(scores):.4f}")
                
                # Count zeros
                zero_count = sum(1 for s in scores if s == 0.0)
                print(f"  Zero scores: {zero_count} ({zero_count/len(scores)*100:.1f}%)")
                
                # Count very low scores
                low_count = sum(1 for s in scores if s < 0.1)
                print(f"  Very low scores (<0.1): {low_count} ({low_count/len(scores)*100:.1f}%)")


def main():
    """Main test function."""
    print("Starting Quality Map Debug Analysis...")
    
    try:
        # Test quality map generation
        results = test_quality_map_generation()
        
        # Create comparison plots
        create_comparison_plots(results)
        
        # Create legends
        create_legends()
        
        # Analyze subset scores
        analyze_subset_scores(results)
        
        print(f"\n=== DEBUG ANALYSIS COMPLETE ===")
        print("Check the generated files:")
        print("- debug_report_*.txt - Detailed debug reports")
        print("- quality_comparison_*.png - Visual comparisons")
        print("- legend_*.png - Color legends")
        
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()