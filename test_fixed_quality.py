#!/usr/bin/env python3
"""
Test script for the fixed quality map generation.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from analysis.quality_map.generator import QualityMapGenerator


def create_test_image(size=(300, 300)):
    """Create a test speckle pattern image."""
    # Create speckle pattern similar to DIC
    image = np.random.rand(*size) * 255
    image = cv2.GaussianBlur(image.astype(np.uint8), (3, 3), 1.0)
    
    # Add some structure
    y, x = np.ogrid[:size[0], :size[1]]
    center_y, center_x = size[0] // 2, size[1] // 2
    
    # Add circular gradient for varying quality
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    gradient = np.exp(-distance / (size[0] * 0.3))
    
    image = image.astype(float) * (0.5 + 0.5 * gradient)
    image = np.clip(image, 0, 255).astype(np.uint8)
    
    return image


def test_quality_map_with_legend():
    """Test quality map generation with legend creation."""
    print("=== TESTING FIXED QUALITY MAP GENERATION ===\n")
    
    # Create generator
    generator = QualityMapGenerator()
    
    # Create test image
    test_image = create_test_image()
    print(f"Test image created: {test_image.shape}, range: {test_image.min()}-{test_image.max()}")
    
    # Test both spectrum types
    spectrum_types = ['custom_dic', 'zeiss_style_dic']
    
    for spectrum_type in spectrum_types:
        print(f"\n--- Testing {spectrum_type} ---")
        
        try:
            # Generate quality map
            quality_map, visualization = generator.generate(
                test_image, 
                spectrum_type=spectrum_type, 
                subset_size=21, 
                step_size=5
            )
            
            print(f"Quality map: {quality_map.shape}, range: {quality_map.min():.4f}-{quality_map.max():.4f}")
            print(f"Visualization: {visualization.shape}, range: {visualization.min()}-{visualization.max()}")
            
            # Count unique colors in visualization
            unique_colors = len(np.unique(visualization.reshape(-1, visualization.shape[-1]), axis=0))
            print(f"Unique colors in visualization: {unique_colors}")
            
            # Create legend
            legend_path = f"legend_{spectrum_type}_fixed.png"
            legend_array = generator.create_legend(spectrum_type, save_path=legend_path)
            print(f"Legend created: {legend_array.shape}")
            
            # Create comparison plot
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            # Original image
            axes[0].imshow(test_image, cmap='gray')
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            # Quality map
            im1 = axes[1].imshow(quality_map, cmap='viridis', vmin=0, vmax=1)
            axes[1].set_title('Quality Map')
            axes[1].axis('off')
            plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
            
            # Visualization
            axes[2].imshow(visualization)
            axes[2].set_title(f'Colored Visualization ({spectrum_type})')
            axes[2].axis('off')
            
            plt.suptitle(f'Quality Map Analysis - {spectrum_type}', fontsize=16)
            plt.tight_layout()
            
            # Save comparison
            comparison_path = f"quality_test_{spectrum_type}_fixed.png"
            plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Comparison saved: {comparison_path}")
            print("✓ Test completed successfully")
            
        except Exception as e:
            print(f"✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n=== TESTING COMPLETE ===")
    print("Generated files:")
    print("- legend_*_fixed.png - Color legends")
    print("- quality_test_*_fixed.png - Quality map comparisons")


def test_colormap_interpolation():
    """Test the colormap interpolation specifically."""
    print(f"\n=== TESTING COLORMAP INTERPOLATION ===")
    
    from analysis.quality_map.colormap import ColormapGenerator
    
    colormap_gen = ColormapGenerator()
    
    # Create test gradient
    test_gradient = np.linspace(0, 1, 256).reshape(1, -1)
    test_gradient = np.repeat(test_gradient, 50, axis=0)
    
    for spectrum_type in ['custom_dic', 'zeiss_style_dic']:
        print(f"\nTesting {spectrum_type} interpolation:")
        
        # Test discrete vs smooth
        discrete_result = colormap_gen.apply_colormap(test_gradient, spectrum_type, 'discrete')
        smooth_result = colormap_gen.apply_colormap(test_gradient, spectrum_type, 'smooth')
        
        discrete_colors = len(np.unique(discrete_result.reshape(-1, 3), axis=0))
        smooth_colors = len(np.unique(smooth_result.reshape(-1, 3), axis=0))
        
        print(f"  Discrete colormap: {discrete_colors} unique colors")
        print(f"  Smooth colormap: {smooth_colors} unique colors")
        
        # Create comparison
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 4))
        
        ax1.imshow(discrete_result, aspect='auto')
        ax1.set_title(f'{spectrum_type} - Discrete Bands')
        ax1.axis('off')
        
        ax2.imshow(smooth_result, aspect='auto')
        ax2.set_title(f'{spectrum_type} - Smooth Interpolation')
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(f"colormap_comparison_{spectrum_type}.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  Comparison saved: colormap_comparison_{spectrum_type}.png")


if __name__ == "__main__":
    test_quality_map_with_legend()
    test_colormap_interpolation()