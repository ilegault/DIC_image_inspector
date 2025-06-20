# enhanced_debug_integration.py
# This enhances your existing debug functionality instead of creating new buttons

import cv2
import numpy as np
from pathlib import Path
import datetime


def enhance_existing_debug_functionality(main_window):
    """Enhance the existing debug button with comprehensive speckle analysis"""
    
    # Store the original debug function
    original_save_debug = main_window.image_display.save_debug_visualizations
    
    def enhanced_debug_visualizations():
        """Enhanced version of save_debug_visualizations with comprehensive analysis"""
        print("\n" + "="*60)
        print("ENHANCED DEBUG ANALYSIS ACTIVATED")
        print("="*60)
        
        try:
            # First run the original debug function
            print("Running original debug visualizations...")
            original_save_debug()
            print("Original debug completed successfully")
            
            # Now add our comprehensive speckle analysis
            print("Starting comprehensive speckle analysis...")
            
            if main_window.original_image is None:
                print("ERROR: No image loaded")
                return
            
            # Get ROI or full image
            if hasattr(main_window, 'roi_handler') and main_window.roi_handler.roi_coords:
                roi_coords = main_window.roi_handler.roi_coords
                x1, y1, x2, y2 = roi_coords
                roi_image = main_window.original_image[y1:y2, x1:x2].copy()
                print(f"Using ROI: {roi_coords}")
                print(f"ROI dimensions: {x2-x1} x {y2-y1}")
            else:
                roi_image = main_window.original_image.copy()
                print("Using full image")
                print(f"Image dimensions: {roi_image.shape}")
            
            # Run comprehensive analysis
            analyzer = ComprehensiveSpeckleAnalyzer()
            results = analyzer.analyze_roi_safely(roi_image)
            
            # Show results in messagebox
            from tkinter import messagebox
            message = f"""Enhanced Debug Analysis Complete!

Original Debug: ✓ Completed successfully
Comprehensive Analysis: ✓ Completed

SPECKLE ANALYSIS RESULTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Speckles: {results['total_speckles']}
Quality Score: {results['quality_score']:.1f}/100
Analysis Method: {results['method']}

SIZE BREAKDOWN:
• Small (1-50px): {results['small_count']}
• Medium (51-200px): {results['medium_count']} 
• Large (200+px): {results['large_count']}

DEBUG FILES SAVED:
• debug_output/ - Original debug files
• enhanced_debug/ - Comprehensive analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Check both folders for detailed analysis!"""

            messagebox.showinfo("Enhanced Debug Complete", message)
            
            # Update status
            main_window.status_var.set(
                f"Enhanced debug: {results['total_speckles']} speckles, Quality: {results['quality_score']:.1f}/100"
            )
            
            print("="*60)
            print("ENHANCED DEBUG ANALYSIS COMPLETED SUCCESSFULLY")
            print("="*60)
            
        except Exception as e:
            print(f"ERROR in enhanced debug: {e}")
            import traceback
            traceback.print_exc()
            
            from tkinter import messagebox
            messagebox.showerror("Enhanced Debug Error", 
                               f"Enhanced debug failed: {str(e)}\n\nOriginal debug may have completed successfully.\nCheck console for details.")
    
    # Replace the debug button command with our enhanced version
    main_window.debug_btn.config(command=enhanced_debug_visualizations)
    main_window.debug_btn.config(text="🔬 Enhanced Debug")
    
    print("Successfully enhanced existing debug button!")


class ComprehensiveSpeckleAnalyzer:
    """Safe, comprehensive speckle analyzer that avoids array boolean issues"""
    
    def __init__(self):
        self.debug_dir = Path("enhanced_debug")
        self.debug_dir.mkdir(exist_ok=True)
        self.clear_debug_folder()
    
    def clear_debug_folder(self):
        """Clear previous debug files safely"""
        try:
            for file in self.debug_dir.glob("*.png"):
                file.unlink()
            for file in self.debug_dir.glob("*.txt"):
                file.unlink()
        except:
            pass
    
    def analyze_roi_safely(self, roi_image):
        """Comprehensive but safe ROI analysis"""
        print(f"Input image shape: {roi_image.shape}")
        print(f"Input image dtype: {roi_image.dtype}")
        
        try:
            # Step 1: Convert to grayscale safely
            if len(roi_image.shape) == 3:
                print("Converting to grayscale...")
                gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)
            else:
                print("Image already grayscale")
                gray = roi_image.copy()
            
            print(f"Grayscale shape: {gray.shape}")
            print(f"Intensity range: {np.min(gray)} to {np.max(gray)}")
            
            # Save original
            cv2.imwrite(str(self.debug_dir / "01_original_roi.png"), gray)
            
            # Step 2: Multiple thresholding methods
            print("Trying multiple thresholding methods...")
            
            # Method 1: Otsu normal
            thresh_val1, binary1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            print(f"Otsu normal threshold: {thresh_val1}")
            
            # Method 2: Otsu inverted  
            thresh_val2, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            print(f"Otsu inverted threshold: {thresh_val2}")
            
            # Method 3: Adaptive
            binary3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            print("Adaptive threshold completed")
            
            # Save all binary images
            cv2.imwrite(str(self.debug_dir / "02_binary_otsu_normal.png"), binary1)
            cv2.imwrite(str(self.debug_dir / "03_binary_otsu_inverted.png"), binary2)
            cv2.imwrite(str(self.debug_dir / "04_binary_adaptive.png"), binary3)
            
            # Step 3: Analyze each method safely
            results = []
            
            for i, (name, binary) in enumerate([
                ("otsu_normal", binary1),
                ("otsu_inverted", binary2), 
                ("adaptive", binary3)
            ]):
                print(f"Analyzing {name}...")
                result = self.analyze_binary_safely(binary, name)
                results.append(result)
                print(f"{name}: {result['speckle_count']} speckles")
            
            # Step 4: Choose best result
            best_result = max(results, key=lambda x: x['speckle_count'])
            print(f"Best method: {best_result['method']} with {best_result['speckle_count']} speckles")
            
            # Step 5: Create comprehensive visualization
            self.create_comprehensive_visualization(gray, best_result)
            
            # Step 6: Generate report
            self.generate_comprehensive_report(gray, results, best_result)
            
            # Return formatted results
            return {
                'total_speckles': best_result['speckle_count'],
                'method': best_result['method'],
                'quality_score': min(100, best_result['speckle_count'] * 2),  # Simple quality score
                'small_count': best_result['size_breakdown']['small'],
                'medium_count': best_result['size_breakdown']['medium'],
                'large_count': best_result['size_breakdown']['large'],
                'all_methods': results
            }
            
        except Exception as e:
            print(f"ERROR in safe analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_speckles': 0,
                'method': 'error',
                'quality_score': 0,
                'small_count': 0,
                'medium_count': 0,
                'large_count': 0,
                'error': str(e)
            }
    
    def analyze_binary_safely(self, binary, method_name):
        """Analyze binary image safely without boolean array issues"""
        try:
            # Connected components
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
            print(f"  {method_name}: Found {num_labels-1} components")
            
            # Safe filtering - avoid numpy boolean operations
            valid_speckles = []
            size_breakdown = {'small': 0, 'medium': 0, 'large': 0}
            
            for i in range(1, num_labels):  # Skip background
                area = int(stats[i, cv2.CC_STAT_AREA])  # Convert to Python int
                
                # Safe size filtering
                if area >= 2 and area <= 10000:  # Very permissive
                    valid_speckles.append({
                        'id': i,
                        'area': area,
                        'centroid': [float(centroids[i][0]), float(centroids[i][1])]
                    })
                    
                    # Size categorization
                    if area <= 50:
                        size_breakdown['small'] += 1
                    elif area <= 200:
                        size_breakdown['medium'] += 1
                    else:
                        size_breakdown['large'] += 1
            
            return {
                'method': method_name,
                'speckle_count': len(valid_speckles),
                'speckles': valid_speckles,
                'size_breakdown': size_breakdown,
                'labels': labels,
                'stats': stats,
                'centroids': centroids
            }
            
        except Exception as e:
            print(f"  ERROR in {method_name}: {e}")
            return {
                'method': method_name,
                'speckle_count': 0,
                'speckles': [],
                'size_breakdown': {'small': 0, 'medium': 0, 'large': 0},
                'error': str(e)
            }
    
    def create_comprehensive_visualization(self, gray, best_result):
        """Create visualization of the best result"""
        try:
            print("Creating comprehensive visualization...")
            
            # Create color visualization
            vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
            # Draw speckles with size-based colors
            for speckle in best_result['speckles']:
                try:
                    x, y = int(speckle['centroid'][0]), int(speckle['centroid'][1])
                    area = speckle['area']
                    
                    # Color coding by size
                    if area <= 50:
                        color = (0, 255, 0)    # Green for small
                        radius = 2
                    elif area <= 200:
                        color = (0, 255, 255)  # Yellow for medium
                        radius = 3
                    else:
                        color = (0, 0, 255)    # Red for large
                        radius = 4
                    
                    cv2.circle(vis, (x, y), radius, color, -1)
                    
                except Exception as e:
                    print(f"Error drawing speckle: {e}")
                    continue
            
            # Add legend
            cv2.putText(vis, f"Method: {best_result['method']}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(vis, f"Total: {best_result['speckle_count']}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(vis, "Green=Small, Yellow=Medium, Red=Large", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Save visualization
            cv2.imwrite(str(self.debug_dir / "05_comprehensive_visualization.png"), vis)
            print("Visualization saved")
            
        except Exception as e:
            print(f"Error creating visualization: {e}")
    
    def generate_comprehensive_report(self, gray, all_results, best_result):
        """Generate comprehensive text report"""
        try:
            print("Generating comprehensive report...")
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.debug_dir / "comprehensive_report.txt", 'w') as f:
                f.write("ENHANCED DEBUG SPECKLE ANALYSIS REPORT\n")
                f.write("="*50 + "\n\n")
                f.write(f"Analysis Time: {timestamp}\n")
                f.write(f"Image Dimensions: {gray.shape[1]} x {gray.shape[0]}\n")
                f.write(f"Image Area: {gray.shape[0] * gray.shape[1]} pixels\n\n")
                
                f.write("METHOD COMPARISON:\n")
                f.write("-"*30 + "\n")
                for result in all_results:
                    f.write(f"{result['method']:15}: {result['speckle_count']:4} speckles\n")
                
                f.write(f"\nBEST METHOD: {best_result['method']}\n")
                f.write("-"*30 + "\n")
                f.write(f"Total Speckles: {best_result['speckle_count']}\n")
                f.write(f"Small (≤50px):  {best_result['size_breakdown']['small']}\n")
                f.write(f"Medium (51-200px): {best_result['size_breakdown']['medium']}\n")
                f.write(f"Large (>200px):  {best_result['size_breakdown']['large']}\n")
                
                density = best_result['speckle_count'] / (gray.shape[0] * gray.shape[1]) * 10000
                f.write(f"\nSpeckle Density: {density:.2f} per 10,000 pixels\n")
                
                if best_result['speckle_count'] > 50:
                    f.write("\nASSESSMENT: Good speckle density for DIC analysis\n")
                elif best_result['speckle_count'] > 20:
                    f.write("\nASSESSMENT: Moderate speckle density\n")
                else:
                    f.write("\nASSESSMENT: Low speckle density - consider optimization\n")
            
            print("Report generated successfully")
            
        except Exception as e:
            print(f"Error generating report: {e}")


# Integration function - call this from your main_window.py
def integrate_enhanced_debug(main_window):
    """Integrate enhanced debug functionality into existing debug button"""
    print("Integrating enhanced debug functionality...")
    enhance_existing_debug_functionality(main_window)
    print("Enhanced debug integration complete!")


if __name__ == "__main__":
    print("Enhanced Debug Integration")
    print("="*40)
    print("This enhances your existing debug button with comprehensive speckle analysis.")
    print()
    print("Integration:")
    print("1. Save this as 'enhanced_debug_integration.py'")
    print("2. In your main_window.py, add at the top:")
    print("   from enhanced_debug_integration import integrate_enhanced_debug")
    print("3. At the end of your __init__ method, add:")
    print("   integrate_enhanced_debug(self)")
    print()
    print("Your existing 'Debug ROI' button will be enhanced with comprehensive analysis!")
