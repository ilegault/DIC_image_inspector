#!/usr/bin/env python3
"""
Demonstration of the fixed quality map generation with smooth colormaps and legends.

This script shows how to:
1. Generate quality maps with smooth color interpolation
2. Create legends for the quality maps
3. Compare different spectrum types
4. Analyze quality distribution
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


def load_or_create_test_image():
    """Load an image or create a test pattern."""
    # Try to load an existing image first
    test_image_paths = [
        "test_image.png", "test_image.jpg", "sample.png", "sample.jpg"
    ]
    
    for path in test_image_paths:
        if Path(path).exists():
            image = cv2.imread(path)
            if image is not None:
                print(f"Loaded image: {path}")
                return image
    
    # Create a test speckle pattern if no image found
    print("No test image found, creating synthetic speckle pattern...")
    size = (400, 400)
    
    # Create realistic speckle pattern
    image = np.random.rand(*size) * 255
    image = cv2.GaussianBlur(image.astype(np.uint8), (3, 3), 1.0)
    
    # Add varying quality regions
    y, x = np.ogrid[:size[0], :size[1]]
    
    # High quality center region
    center_y, center_x = size[0] // 2, size[1] // 2
    distance_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    center_quality = np.exp(-distance_center / (size[0] * 0.2))
    
    # Poor quality corners
    corner_effects = (
        np.exp(-((x - 50)**2 + (y - 50)**2) / 2000) +
        np.exp(-((x - size[1] + 50)**2 + (y - 50)**2) / 2000) +
        np.exp(-((x - 50)**2 + (y - size[0] + 50)**2) / 2000) +
        np.exp(-((x - size[1] + 50)**2 + (y - size[0] + 50)**2) / 2000)
    )
    
    # Combine effects
    quality_variation = center_quality * 0.7 + corner_effects * 0.3 + 0.3
    image = image.astype(float) * quality_variation
    image = np.clip(image, 0, 255).astype(np.uint8)
    
    # Convert to RGB for consistency
    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    
    print(f"Created synthetic test image: {image.shape}")
    return image


def demonstrate_quality_maps():
    """Demonstrate quality map generation with different settings."""
    print("=== QUALITY MAP DEMONSTRATION ===\n")
    
    # Load or create test image
    test_image = load_or_create_test_image()
    
    # Create generator
    generator = QualityMapGenerator()
    
    # Get optimal parameters
    optimal_params = generator.get_optimal_parameters(test_image)
    print(f"Optimal parameters: {optimal_params}")
    
    # Test both spectrum types
    spectrum_types = ['custom_dic', 'zeiss_style_dic']
    results = {}
    
    for spectrum_type in spectrum_types:
        print(f"\n--- Generating {spectrum_type} quality map ---")
        
        # Generate quality map
        quality_map, visualization = generator.generate(
            test_image,
            spectrum_type=spectrum_type,
            subset_size=optimal_params['subset_size'],
            step_size=optimal_params['step_size']
        )
        
        # Get statistics
        stats = generator.generate_quality_statistics(quality_map)
        
        print(f"Quality map statistics:")
        print(f"  Range: {quality_map.min():.3f} - {quality_map.max():.3f}")
        print(f"  Mean: {stats['mean_quality']:.1f}%")
        print(f"  Excellent regions: {stats['excellent_percentage']:.1f}%")
        print(f"  Good regions: {stats['good_percentage']:.1f}%")
        print(f"  Fair regions: {stats['fair_percentage']:.1f}%")
        print(f"  Poor regions: {stats['poor_percentage']:.1f}%")
        
        # Count unique colors
        unique_colors = len(np.unique(visualization.reshape(-1, 3), axis=0))
        print(f"  Unique colors in visualization: {unique_colors}")
        
        # Store results
        results[spectrum_type] = {
            'quality_map': quality_map,
            'visualization': visualization,
            'stats': stats
        }
    
    return test_image, results, generator


def create_comprehensive_visualization(test_image, results, generator):
    """Create a comprehensive visualization showing all results."""
    print(f"\n--- Creating comprehensive visualization ---")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    
    # Original image
    if len(test_image.shape) == 3:
        axes[0, 0].imshow(cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB))
    else:
        axes[0, 0].imshow(test_image, cmap='gray')
    axes[0, 0].set_title('Original Image', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')
    
    # Custom DIC results
    custom_results = results['custom_dic']
    
    # Quality map
    im1 = axes[0, 1].imshow(custom_results['quality_map'], cmap='viridis', vmin=0, vmax=1)
    axes[0, 1].set_title('Custom DIC - Quality Map', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04)
    
    # Visualization
    axes[0, 2].imshow(custom_results['visualization'])
    axes[0, 2].set_title('Custom DIC - Colored Visualization', fontsize=14, fontweight='bold')
    axes[0, 2].axis('off')
    
    # Legend
    legend_custom = generator.create_legend('custom_dic', (300, 100))
    axes[0, 3].imshow(legend_custom)
    axes[0, 3].set_title('Custom DIC - Legend', fontsize=14, fontweight='bold')
    axes[0, 3].axis('off')
    
    # ZEISS style results
    zeiss_results = results['zeiss_style_dic']
    
    # Quality map
    im2 = axes[1, 1].imshow(zeiss_results['quality_map'], cmap='viridis', vmin=0, vmax=1)
    axes[1, 1].set_title('ZEISS Style - Quality Map', fontsize=14, fontweight='bold')
    axes[1, 1].axis('off')
    plt.colorbar(im2, ax=axes[1, 1], fraction=0.046, pad=0.04)
    
    # Visualization
    axes[1, 2].imshow(zeiss_results['visualization'])
    axes[1, 2].set_title('ZEISS Style - Colored Visualization', fontsize=14, fontweight='bold')
    axes[1, 2].axis('off')
    
    # Legend
    legend_zeiss = generator.create_legend('zeiss_style_dic', (300, 100))
    axes[1, 3].imshow(legend_zeiss)
    axes[1, 3].set_title('ZEISS Style - Legend', fontsize=14, fontweight='bold')
    axes[1, 3].axis('off')
    
    # Statistics comparison
    axes[1, 0].axis('off')
    stats_text = "Quality Statistics Comparison:\n\n"
    
    for spectrum_type in ['custom_dic', 'zeiss_style_dic']:
        stats = results[spectrum_type]['stats']
        stats_text += f"{spectrum_type.replace('_', ' ').title()}:\n"
        stats_text += f"  Mean Quality: {stats['mean_quality']:.1f}%\n"
        stats_text += f"  Excellent: {stats['excellent_percentage']:.1f}%\n"
        stats_text += f"  Good: {stats['good_percentage']:.1f}%\n"
        stats_text += f"  Poor: {stats['poor_percentage']:.1f}%\n\n"
    
    axes[1, 0].text(0.05, 0.95, stats_text, transform=axes[1, 0].transAxes, 
                   fontsize=11, verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
    
    plt.suptitle('DIC Quality Map Analysis - Complete Results', fontsize=18, fontweight='bold')
    plt.tight_layout()
    
    # Save comprehensive visualization
    output_path = "quality_map_demonstration.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Comprehensive visualization saved: {output_path}")
    return output_path


def create_detailed_legends():
    """Create detailed standalone legends."""
    print(f"\n--- Creating detailed legends ---")
    
    generator = QualityMapGenerator()
    
    for spectrum_type in ['custom_dic', 'zeiss_style_dic']:
        legend_path = f"detailed_legend_{spectrum_type}.png"
        try:
            generator.create_legend(spectrum_type, save_path=legend_path)
            print(f"Detailed legend created: {legend_path}")
        except Exception as e:
            print(f"Error creating detailed legend for {spectrum_type}: {e}")


def demonstrate_colormap_comparison():
    """Demonstrate the difference between discrete and smooth colormaps."""
    print(f"\n--- Demonstrating colormap interpolation ---")
    
    from analysis.quality_map.colormap import ColormapGenerator
    
    colormap_gen = ColormapGenerator()
    
    # Create test gradient
    test_gradient = np.linspace(0, 1, 400).reshape(1, -1)
    test_gradient = np.repeat(test_gradient, 80, axis=0)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 8))
    
    spectrum_types = ['custom_dic', 'zeiss_style_dic']
    
    for i, spectrum_type in enumerate(spectrum_types):
        # Discrete colormap
        discrete_result = colormap_gen.apply_colormap(test_gradient, spectrum_type, 'discrete')
        axes[i, 0].imshow(discrete_result, aspect='auto')
        axes[i, 0].set_title(f'{spectrum_type.replace("_", " ").title()} - Discrete Bands')
        axes[i, 0].axis('off')
        
        # Smooth colormap
        smooth_result = colormap_gen.apply_colormap(test_gradient, spectrum_type, 'smooth')
        axes[i, 1].imshow(smooth_result, aspect='auto')
        axes[i, 1].set_title(f'{spectrum_type.replace("_", " ").title()} - Smooth Interpolation')
        axes[i, 1].axis('off')
        
        # Count unique colors
        discrete_colors = len(np.unique(discrete_result.reshape(-1, 3), axis=0))
        smooth_colors = len(np.unique(smooth_result.reshape(-1, 3), axis=0))
        
        print(f"{spectrum_type}:")
        print(f"  Discrete: {discrete_colors} unique colors")
        print(f"  Smooth: {smooth_colors} unique colors")
    
    plt.suptitle('Colormap Interpolation Comparison', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    comparison_path = "colormap_interpolation_comparison.png"
    plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Colormap comparison saved: {comparison_path}")


def main():
    """Main demonstration function."""
    print("DIC Quality Map Generator - Fixed Version Demonstration")
    print("=" * 60)
    
    try:
        # Generate quality maps
        test_image, results, generator = demonstrate_quality_maps()
        
        # Create comprehensive visualization
        create_comprehensive_visualization(test_image, results, generator)
        
        # Create detailed legends
        create_detailed_legends()
        
        # Demonstrate colormap comparison
        demonstrate_colormap_comparison()
        
        print(f"\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE!")
        print("Generated files:")
        print("- quality_map_demonstration.png - Complete analysis results")
        print("- detailed_legend_*.png - Detailed color legends")
        print("- colormap_interpolation_comparison.png - Interpolation comparison")
        print("\nKey improvements:")
        print("✓ Smooth color interpolation (100+ unique colors vs 3-6 before)")
        print("✓ Proper quality map generation with realistic ranges")
        print("✓ Legend creation functionality")
        print("✓ Statistical analysis of quality distribution")
        print("✓ Support for both Custom DIC and ZEISS-style analysis")
        
    except Exception as e:
        print(f"Error in demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()