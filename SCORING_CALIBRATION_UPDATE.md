# Scoring Calibration Update - MIG and Ef Metrics

## Overview

The scoring calibration for MIG (Mean Intensity Gradient) and Ef (Enhanced feature) metrics has been updated to better align with the expected ranges for good speckle patterns in DIC analysis.

## Changes Made

### 1. MIG Normalization Update

**Before:**
- MIG values were normalized by dividing by 255
- Score multiplier: 6.0

**After:**
- MIG values are normalized by dividing by 50 (typical range for good speckle patterns)
- Score multiplier: 1.2 (adjusted to maintain similar scoring behavior)

**Rationale:** According to Pan et al. (2009), MIG typically ranges 0-50 for good speckle patterns, making 255 an inappropriate normalization factor.

### 2. Ef Normalization Update

**Before:**
- Ef values were normalized by dividing by 255
- Score multiplier: 4.0

**After:**
- Ef values are normalized by dividing by 100 (initial estimate, configurable)
- Score multiplier: 1.0 (initial value, configurable)
- **Empirical calibration support added**

**Rationale:** Ef metric needs empirical calibration based on actual test images since its range depends on the specific implementation and image characteristics.

### 3. Configurable Parameters

The following parameters are now configurable:

```python
# Normalization factors
mig_normalization_factor = 50.0   # Based on literature
ef_normalization_factor = 100.0   # Initial estimate, needs calibration

# Score multipliers
mig_score_multiplier = 1.2         # Adjusted for new normalization
ef_score_multiplier = 1.0          # Initial value, needs calibration
```

## New Methods Added

### `set_scoring_calibration()`

Allows manual adjustment of calibration parameters:

```python
calc = QualityCalculator()
calc.set_scoring_calibration(
    mig_normalization_factor=50.0,
    ef_normalization_factor=120.0,
    mig_score_multiplier=1.2,
    ef_score_multiplier=1.1
)
```

### `get_scoring_calibration()`

Returns current calibration parameters:

```python
params = calc.get_scoring_calibration()
print(params)
# Output: {'mig_normalization_factor': 50.0, 'ef_normalization_factor': 100.0, ...}
```

### `calibrate_ef_from_samples()`

Automatically calibrates Ef normalization based on sample images:

```python
# Load your good quality speckle images
sample_images = [img1, img2, img3, ...]

# Calibrate Ef normalization
calc.calibrate_ef_from_samples(sample_images, target_ef_range=(0.3, 0.8))
```

## Empirical Calibration Process

### Step 1: Collect Sample Images

Gather a set of speckle pattern images that represent good quality for DIC analysis.

### Step 2: Use the Calibration Utility

```bash
python calibrate_ef_metric.py /path/to/speckle/images/
```

This will:
- Analyze the Ef value distribution in your images
- Provide calibration recommendations
- Generate code snippets for implementation

### Step 3: Apply Calibration

Use the recommended parameters in your quality calculator:

```python
calc = QualityCalculator()
calc.set_scoring_calibration(ef_normalization_factor=recommended_value)
```

## Testing

Run the test script to see the calibration in action:

```bash
python test_scoring_calibration.py
```

This demonstrates:
- Updated MIG normalization
- Configurable Ef normalization
- Empirical calibration process
- Comparison between old and new normalization

## Impact on Quality Scores

### MIG Scoring
- Raw MIG values in the range 0-50 will now be properly normalized
- Scores should be more accurate for typical speckle patterns
- Very high MIG values (>50) will be capped at maximum score

### Ef Scoring
- Initial normalization provides a starting point
- Empirical calibration allows fine-tuning based on actual data
- More accurate assessment of gradient quality

### Overall Quality Scores
- More accurate gradient quality assessment
- Better discrimination between good and poor speckle patterns
- Maintained backward compatibility with existing thresholds

## Recommendations

1. **For immediate use:** The updated MIG normalization (÷50) provides better scoring out of the box.

2. **For optimal results:** Perform empirical calibration of the Ef metric using your specific speckle pattern images.

3. **For validation:** Test the calibration with known good and poor quality images to verify the scoring behavior.

## Files Modified

- `core/quality_calculator.py` - Updated scoring calibration
- `test_scoring_calibration.py` - Test script (new)
- `calibrate_ef_metric.py` - Calibration utility (new)

## References

- Pan, B., Qian, K., Xie, H., & Asundi, A. (2009). Two-dimensional digital image correlation for in-plane displacement and strain measurement: a review. *Measurement Science and Technology*, 20(6), 062001.
- Hu, Z., Xu, T., Wang, X., Chen, Z., & Luo, H. (2021). A novel speckle pattern quality assessment method based on enhanced feature matching. *Optics and Lasers in Engineering*, 140, 106526.