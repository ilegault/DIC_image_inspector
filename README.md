# DIC Image Quality Inspector

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

## 🔬 Overview

**DIC Image Quality Inspector** is a sophisticated Python application designed to evaluate and optimize speckle pattern quality for Digital Image Correlation (DIC) applications. It provides comprehensive analysis of speckle patterns, helping researchers and engineers determine if their specimens are properly prepared for mechanical testing with DIC systems.

The tool analyzes critical quality metrics including gradient content, contrast distribution, speckle morphology, information entropy, and noise characteristics to provide scientifically-based recommendations for optimal DIC correlation parameters.

## ✨ Key Features

### Core Analysis Capabilities
- 🎯 **Advanced Quality Metrics**: Mean Intensity Gradient (MIG), Enhanced Feature (Ef) calculation, entropy analysis
- 📊 **Real-time Quality Visualization**: Color-mapped quality overlays with multiple spectrum options
- 🔍 **Region of Interest (ROI) Selection**: Polygon-based ROI for focused analysis
- 📈 **DIC Parameter Optimization**: Automatic subset size and step size recommendations
- 📸 **Multiple Input Methods**: File loading, screenshot capture, live camera feed (Windows)

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

## 🖼️ Screenshots

<img width="1006" height="804" alt="image" src="https://github.com/user-attachments/assets/33e2e2fb-7b92-4c9f-bb44-a55b68ca078b" />


## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Operating System: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/DIC_image_inspector.git
   cd DIC_image_inspector
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

## 📦 Dependencies

### Core Requirements
```
numpy>=1.20.0
opencv-python>=4.5.0
Pillow>=8.0.0
matplotlib>=3.3.0
scipy>=1.6.0
```

### Platform-Specific Dependencies

**Windows (for SpinView camera support):**
```
pywin32>=300
```

**All platforms:**
- tkinter (usually included with Python)

## 💻 Usage

### Basic Workflow

1. **Load an Image**
   ```python
   # Via GUI: Click "Load Image" button
   # Supported formats: PNG, JPEG, TIFF, BMP
   ```

2. **Select Region of Interest** (Optional)
   - Click "Select ROI" button
   - Click to add polygon vertices
   - Press Enter to complete selection
   - Hold Ctrl for enhanced selection mode

3. **Analyze Pattern**
   - Adjust analysis parameters:
     - Subset Size: 11-51 pixels (default: 19)
     - Step Size: 1-8 pixels (default: 4)
   - Click "Analyze" button

4. **View Results**
   - Overall quality score (0-100)
   - Quality map visualization
   - DIC parameter recommendations
   - Statistical analysis

5. **Export Results**
   - Text report with detailed analysis
   - Quality map overlays
   - Original image with annotations

### Advanced Usage

#### Command Line Arguments
```bash
# Run with debug mode
python main.py --debug

# Specify initial image
python main.py --image path/to/image.png

# Set analysis parameters
python main.py --subset 21 --step 5
```

#### Programmatic Usage
```python
from core.image_analyzer import ImageAnalyzer
from models.image_data import ImageData

# Initialize analyzer
analyzer = ImageAnalyzer()

# Load and analyze image
image_data = ImageData.from_file("speckle_pattern.png")
results = analyzer.analyze_image(
    image_data,
    subset_size=19,
    step_size=4
)

# Access results
print(f"Overall Quality: {results.overall_score:.1f}%")
print(f"Recommended Subset: {results.dic_parameters['subset_size']} pixels")
```

## 📊 Understanding Quality Scores

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

## 🛠️ Configuration

### Application Settings

Configuration file: `config.json`

```json
{
  "theme": "dark",
  "analysis": {
    "default_subset_size": 19,
    "default_step_size": 4,
    "quality_threshold": 0.75,
    "enable_gpu": true
  },
  "export": {
    "default_format": "png",
    "compression_quality": 95,
    "include_metadata": true
  }
}
```

### Performance Tuning

```python
# In utils/constants.py
PERFORMANCE = {
    'enable_gpu_acceleration': True,
    'enable_multiprocessing': True,
    'thread_pool_size': 4,
    'max_image_display_size': 4096
}
```

## 📁 Project Structure

```
DIC_image_inspector/
├── 📂 analysis/              # Core analysis algorithms
│   ├── entropy_analysis.py   # Information content analysis
│   ├── gradient_analysis.py  # MIG and gradient calculations
│   ├── morphology_analysis.py # Speckle shape analysis
│   └── quality_map/          # Quality visualization
├── 📂 core/                  # Business logic
│   ├── image_analyzer.py    # Main analysis orchestrator
│   └── report_generator.py  # Report generation
├── 📂 models/               # Data models
│   ├── analysis_result.py   # Analysis result container
│   ├── image_data.py       # Image data wrapper
│   └── roi_data.py         # ROI data structure
├── 📂 ui/                   # User interface
│   ├── main_window.py       # Main application window
│   ├── main_components/     # UI components
│   ├── dialogs/            # Dialog windows
│   └── live_analyze/       # Live analysis features
├── 📂 utils/               # Utilities
│   ├── constants.py        # Application constants
│   ├── validation.py       # Input validation
│   └── file_operations.py  # File I/O operations
├── 📄 main.py              # Entry point
├── 📄 app.py               # Application initialization
├── 📄 requirements.txt     # Dependencies
└── 📄 README.md           # This file
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=. tests/

# Run specific test module
python -m pytest tests/test_analyzer.py
```

### Performance Testing
```python
# Benchmark analysis performance
python tests/benchmark.py --iterations 100
```

## 🔬 Scientific Background

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

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Add docstrings to all public methods
- Maximum line length: 100 characters

## 🐛 Troubleshooting

### Common Issues

**Issue: Application won't start**
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue: SpinView camera not detected (Windows)**
```bash
# Install Windows-specific dependencies
pip install pywin32

# Run as administrator if needed
```

**Issue: Slow analysis performance**
```python
# Reduce image size or select ROI
# Adjust parameters in utils/constants.py
PERFORMANCE['enable_multiprocessing'] = True
PERFORMANCE['thread_pool_size'] = 8
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Isaac Legault** - *Initial development* - [GitHub Profile](https://github.com/ilegault)

## 🙏 Acknowledgments

- DIC research community for theoretical foundations
- Open-source contributors for core libraries
- Beta testers for valuable feedback
- Academic partners for validation data

## 📮 Support

For support and questions:
- 📧 Email: ilegault004@gmail.com
