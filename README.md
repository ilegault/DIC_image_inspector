# DIC Image Quality Inspector

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

## Overview

**DIC Image Quality Inspector** is a sophisticated Python application designed to evaluate and optimize speckle pattern quality for Digital Image Correlation (DIC) applications. It provides a comprehensive analysis of speckle patterns, helping researchers and engineers determine if their specimens are properly prepared for mechanical testing with DIC systems.

The tool analyzes critical quality metrics including gradient content, contrast distribution, speckle morphology, information entropy, and noise characteristics to provide scientifically-based recommendations for optimal DIC correlation parameters.

## Key Features

### Core Analysis Capabilities
- **Advanced Quality Metrics**: Mean Intensity Gradient (MIG), Enhanced Feature (Ef) calculation, entropy analysis
- **Real-time Quality Visualization**: Color-mapped quality overlays with multiple spectrum options
- **Region of Interest (ROI) Selection**: Polygon-based ROI for focused analysis
- **DIC Parameter Optimization**: Automatic subset size and step size recommendations
- **Multiple Input Methods**: File loading, screenshot capture, live camera feed (Windows)

### Technical Features
- **Multi-threaded Processing**: Responsive UI during analysis operations
- **Adaptive Algorithms**: Dynamic parameter adjustment based on pattern characteristics
- **Scientific Validation**: Based on peer-reviewed DIC literature and established metrics
- **Comprehensive Reporting**: Detailed analysis reports with statistical summaries
- **Dark/Light Theme Support**: Modern UI with theme persistence

### Special Features
- **SpinView Camera Integration** (Windows only): Real-time quality analysis from FLIR/Point Grey cameras
- **Batch Processing Support**: Analyze multiple images sequentially
- **Export Capabilities**: Reports in TXT/PDF/HTML, quality maps in PNG/TIFF
- **Performance Modes**: Fast, Balanced, and Accurate analysis options

## Screenshots

<img width="1006" height="804" alt="image" src="https://github.com/user-attachments/assets/33e2e2fb-7b92-4c9f-bb44-a55b68ca078b" />


## Understanding Quality Scores

### Quality Assessment Scale

| Score Range | DIC Suitability | Description |
|-------------|----------------|-------------|
| 90-100 | Excellent | Ideal for high-precision DIC measurements |
| 75-89 | Very Good | Suitable for most DIC applications |
| 60-74 | Good | Acceptable for standard DIC analysis |
| 45-59 | Fair | May work with careful parameter selection |
| 30-44 | Challenging | Consider pattern improvement |
| 0-29 | Poor | Not suitable for reliable DIC |

### Analysis Metrics

The tool evaluates five key quality metrics:

1. **Gradient Content** (Mean Intensity Gradient - MIG)
   - Measures edge sharpness and feature definition
   - Higher gradients indicate better trackable features

2. **Contrast Distribution**
   - Evaluates local and global contrast variations
   - Good contrast improves correlation accuracy

3. **Speckle Morphology**
   - Analyzes speckle size, shape, and distribution
   - Optimal speckle size: 3-5 pixels diameter

4. **Information Entropy**
   - Calculates pattern uniqueness and randomness
   - Higher entropy reduces correlation ambiguity

5. **Noise Characteristics**
   - Estimates signal-to-noise ratio
   - Lower noise improves sub-pixel accuracy


##  Scientific Background

This tool implements established DIC quality assessment methods from peer-reviewed literature:

### Key References

1. **Pan, B. et al. (2009)**. "Mean intensity gradient: An effective global parameter for quality assessment of the speckle patterns used in digital image correlation." *Optics and Lasers in Engineering*.

2. **Hu, Z. et al. (2021)**. "Enhanced feature for quality assessment of speckle patterns in digital image correlation." *Measurement Science and Technology*.

3. **Reu, P.L. (2015)**. "All about speckles: Speckle density." *Experimental Techniques*.

4. **Sutton, M.A. et al. (2009)**. *Image correlation for shape, motion and deformation measurements*.

### Algorithm Implementation

The quality score combines multiple metrics using weighted averaging:

```
Quality Score = w1×MIG + w2×Contrast + w3×Entropy + w4×Morphology + w5×Noise
```

Where weights are optimized based on empirical DIC performance data.


**Issue: Slow analysis performance**

- Reduce image size/ select a smaller ROI
- If you are in the spinview live feature then choose the easier mode 


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **Isaac Legault** - *Initial development* - [GitHub Profile](https://github.com/ilegault)
- **Leyton (Zhiyan) Lu** - [GitHub Profile](https://github.com/eggman127)

## Acknowledgments

- DIC research community for theoretical foundations
- Open-source contributors for core libraries
- Beta testers for valuable feedback
- Academic partners for validation data

## Support

For support and questions:
- Email: ilegault004@gmail.com
