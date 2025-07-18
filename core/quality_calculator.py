# core/quality_calculator.py - Quality Metrics Calculator

import cv2
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging
from analysis.gradient_analysis import GradientAnalyzer

logger = logging.getLogger(__name__)


class QualityCalculator:
    """
    Calculates comprehensive quality metrics for DIC analysis.

    This class orchestrates various quality analysis algorithms and combines
    them into a unified quality score suitable for DIC applications.
    """

    def __init__(self):
        """Initialize the quality calculator with default weights."""
        # Initialize gradient analyzer
        self.gradient_analyzer = GradientAnalyzer()
        
        # Quality metric weights (must sum to 1.0)
        self.weights = {
            'gradient': 0.40,  # Gradient content (most important for DIC)
            'contrast': 0.25,  # Contrast quality
            'entropy': 0.20,  # Information content
            'pattern': 0.10,  # Pattern complexity
            'noise': 0.05  # Noise level
        }

        # Scoring calibration parameters
        self.mig_normalization_factor = 50  # MIG typically ranges 0-50 for good speckle patterns
        self.ef_normalization_factor = 40  # Initial estimate, needs empirical calibration
        self.mig_score_multiplier = 2.0  # Adjusted from original 6 to account for new normalization
        self.ef_score_multiplier = 1.2   # Initial value for empirical calibration

        # Validate weights
        if abs(sum(self.weights.values()) - 1.0) > 1e-6:
            logger.warning(f"Quality weights don't sum to 1.0: {sum(self.weights.values())}")

    def update_scoring_parameters(self, mig_norm_factor: Optional[float] = None,
                                  ef_norm_factor: Optional[float] = None,
                                  mig_score_multiplier: Optional[float] = None,
                                  ef_score_multiplier: Optional[float] = None):
        """
        Update scoring calibration parameters.
        
        Args:
            mig_norm_factor: New MIG normalization factor
            ef_norm_factor: New Ef normalization factor  
            mig_score_multiplier: New MIG score multiplier
            ef_score_multiplier: New Ef score multiplier
        """
        if mig_norm_factor is not None:
            self.mig_normalization_factor = mig_norm_factor
            logger.info(f"Updated MIG normalization factor to: {mig_norm_factor}")
            
        if ef_norm_factor is not None:
            self.ef_normalization_factor = ef_norm_factor
            logger.info(f"Updated Ef normalization factor to: {ef_norm_factor}")
            
        if mig_score_multiplier is not None:
            self.mig_score_multiplier = mig_score_multiplier
            logger.info(f"Updated MIG score multiplier to: {mig_score_multiplier}")
            
        if ef_score_multiplier is not None:
            self.ef_score_multiplier = ef_score_multiplier
            logger.info(f"Updated Ef score multiplier to: {ef_score_multiplier}")

    def calculate_quality_score(self, image: np.ndarray, roi_coords: Optional[list] = None) -> Dict:
        """
        Calculate comprehensive quality score for an image or ROI.

        Args:
            image: Input image as numpy array
            roi_coords: Optional ROI coordinates for focused analysis

        Returns:
            Dict containing quality score and detailed metrics
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Apply ROI mask if provided
        analysis_region = self._apply_roi_mask(gray, roi_coords)

        # Calculate individual quality metrics
        gradient_metrics = self._calculate_gradient_quality(analysis_region)
        contrast_metrics = self._calculate_contrast_quality(analysis_region)
        entropy_metrics = self._calculate_entropy_quality(analysis_region)
        pattern_metrics = self._calculate_pattern_quality(analysis_region)
        noise_metrics = self._calculate_noise_quality(analysis_region)

        # Combine metrics using weighted average
        overall_score = (
                gradient_metrics['score'] * self.weights['gradient'] +
                contrast_metrics['score'] * self.weights['contrast'] +
                entropy_metrics['score'] * self.weights['entropy'] +
                pattern_metrics['score'] * self.weights['pattern'] +
                noise_metrics['score'] * self.weights['noise']
        )

        # Convert to 0-100 scale
        overall_score = max(0.0, min(100.0, overall_score * 100))

        return {
            'overall_score': round(overall_score, 1),
            'quality_normalized': overall_score / 100.0,
            'gradient_metrics': gradient_metrics,
            'contrast_metrics': contrast_metrics,
            'entropy_metrics': entropy_metrics,
            'pattern_metrics': pattern_metrics,
            'noise_metrics': noise_metrics,
            'weights_used': self.weights.copy(),
            'analysis_method': 'ROI-based' if roi_coords else 'Full image'
        }

    def _apply_roi_mask(self, gray: np.ndarray, roi_coords: Optional[list]) -> np.ndarray:
        """Apply ROI mask to image if coordinates provided."""
        if not roi_coords or len(roi_coords) < 3:
            return gray

        try:
            # Create mask for polygon ROI
            mask = np.zeros(gray.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)

            # Validate and clamp coordinates
            h, w = gray.shape[:2]
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

            cv2.fillPoly(mask, [pts], 255)

            # Apply mask
            masked_image = cv2.bitwise_and(gray, gray, mask=mask)
            return masked_image

        except Exception as e:
            logger.warning(f"Failed to apply ROI mask: {e}")
            return gray

    def _calculate_gradient_quality(self, gray: np.ndarray) -> Dict:
        """
        Calculate gradient-based quality metrics for DIC assessment using GradientAnalyzer.
        """
        # Use the gradient analyzer directly
        quality_scores = self.gradient_analyzer.calculate_gradient_quality_score(
            gray, 
            mig_norm_factor=self.mig_normalization_factor,
            ef_norm_factor=self.ef_normalization_factor,
            mig_score_multiplier=self.mig_score_multiplier,
            ef_score_multiplier=self.ef_score_multiplier
        )
        
        # Log values for debugging
        logger.info(f"Using multipliers - MIG: {self.mig_score_multiplier}, Ef: {self.ef_score_multiplier}")
        logger.info(f"Raw MIG: {quality_scores['raw_mig']:.2f} (normalized: {quality_scores['normalized_mig']:.3f})")
        logger.info(f"Raw Ef: {quality_scores['raw_ef']:.2f} (normalized: {quality_scores['normalized_ef']:.3f})")
        logger.info(f"MIG Score: {quality_scores['mig_score']:.3f}, Ef Score: {quality_scores['ef_score']:.3f}")
        logger.info(f"Final Gradient Score: {quality_scores['gradient_score']:.3f}")
        
        return {
            'score': quality_scores['gradient_score'],
            'mig_score': quality_scores['mig_score'],
            'ef_score': quality_scores['ef_score'],
            'raw_mig': quality_scores['raw_mig'],
            'raw_ef': quality_scores['raw_ef'],
            'distribution_bonus': quality_scores['distribution_bonus']
        }

    def _calculate_contrast_quality(self, gray: np.ndarray) -> Dict:
        """Calculate contrast-based quality metrics."""
        mean_val = np.mean(gray)
        std_val = np.std(gray)
        min_val = np.min(gray)
        max_val = np.max(gray)

        # Multiple contrast measures with safe arithmetic
        rms_contrast = std_val / (mean_val + 1e-6)
        
        # Safe Michelson contrast calculation
        # Avoid overflow by checking individual values first
        if max_val > 0 and min_val >= 0:
            # Use float conversion to avoid integer overflow
            max_f = float(max_val)
            min_f = float(min_val)
            denominator = max_f + min_f
            if denominator > 0:
                michelson_contrast = (max_f - min_f) / denominator
            else:
                michelson_contrast = 0.0
        else:
            michelson_contrast = 0.0
            
        weber_contrast = (max_val - mean_val) / (mean_val + 1e-6)

        # Local contrast analysis with safe arithmetic
        if gray.shape[0] > 7 and gray.shape[1] > 7:
            kernel = np.ones((5, 5)) / 25
            local_mean = cv2.filter2D(gray.astype(float), -1, kernel)
            mean_local_mean = np.mean(local_mean)
            if mean_local_mean > 0:
                local_contrast = np.std(gray - local_mean) / mean_local_mean
            else:
                local_contrast = 0.0
        else:
            local_contrast = rms_contrast

        # Combined contrast score
        contrast_score = (
                min(1.0, rms_contrast / 0.4) * 0.4 +
                min(1.0, michelson_contrast * 2) * 0.3 +
                min(1.0, weber_contrast / 0.5) * 0.2 +
                min(1.0, local_contrast / 0.3) * 0.1
        )

        return {
            'score': contrast_score,
            'rms_contrast': rms_contrast,
            'michelson_contrast': michelson_contrast,
            'weber_contrast': weber_contrast,
            'local_contrast': local_contrast,
            'mean_intensity': mean_val,
            'std_intensity': std_val
        }

    def _calculate_entropy_quality(self, gray: np.ndarray) -> Dict:
        """Calculate information content (entropy) quality metrics."""
        from scipy.stats import entropy

        # Shannon entropy
        hist, _ = np.histogram(gray, bins=64, range=(0, 256), density=True)
        shannon_entropy = entropy(hist[hist > 0]) if np.any(hist > 0) else 0
        entropy_score = min(1.0, shannon_entropy / 5.0)

        # Local entropy analysis
        if gray.shape[0] > 5 and gray.shape[1] > 5:
            local_entropies = []
            window_size = min(7, gray.shape[0] // 2, gray.shape[1] // 2)
            if window_size >= 3:
                step = max(1, window_size // 2)
                for i in range(0, gray.shape[0] - window_size + 1, step):
                    for j in range(0, gray.shape[1] - window_size + 1, step):
                        window = gray[i:i + window_size, j:j + window_size]
                        w_hist, _ = np.histogram(window, bins=16, range=(0, 256), density=True)
                        w_entropy = entropy(w_hist[w_hist > 0]) if np.any(w_hist > 0) else 0
                        local_entropies.append(w_entropy)

            local_entropy_score = np.mean(local_entropies) / 4.0 if local_entropies else entropy_score
        else:
            local_entropy_score = entropy_score

        information_score = entropy_score * 0.6 + min(1.0, local_entropy_score) * 0.4

        return {
            'score': information_score,
            'shannon_entropy': shannon_entropy,
            'local_entropy_avg': np.mean(local_entropies) if 'local_entropies' in locals() and local_entropies else 0,
            'entropy_normalized': entropy_score,
            'local_entropy_normalized': local_entropy_score
        }

    def _calculate_pattern_quality(self, gray: np.ndarray) -> Dict:
        """Calculate pattern complexity and morphology quality metrics."""
        # Speckle analysis using adaptive thresholding
        if gray.shape[0] > 10 and gray.shape[1] > 10:
            block_size = max(3, min(gray.shape[0] // 3, gray.shape[1] // 3, 15))
            if block_size % 2 == 0:
                block_size += 1

            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 2
            )

            # Find connected main_components (speckles)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

            if num_labels > 1:
                areas = stats[1:, cv2.CC_STAT_AREA]  # Skip background

                # Size-relative speckle filtering
                min_speckle_area = max(2, int(gray.size * 0.0001))  # 0.01% of image
                max_speckle_area = int(gray.size * 0.01)  # 1% of image

                valid_areas = areas[(areas >= min_speckle_area) & (areas <= max_speckle_area)]

                if len(valid_areas) > 0:
                    avg_speckle_diameter = np.sqrt(np.mean(valid_areas) / np.pi) * 2
                    speckle_density = len(valid_areas) / gray.size * 1e6
                    coverage = np.sum(valid_areas) / gray.size

                    # Pattern uniformity
                    pattern_uniformity = max(0.0,
                                             float(100 * (1 - np.std(valid_areas) / (np.mean(valid_areas) + 1e-6))))

                    # Combined pattern score
                    if 0.001 <= coverage <= 0.1:  # Good coverage range
                        coverage_score = 1.0
                    else:
                        coverage_score = 0.6

                    if 50 <= speckle_density <= 5000:  # Good density range
                        density_score = 1.0
                    else:
                        density_score = 0.7

                    pattern_score = coverage_score * 0.5 + density_score * 0.3 + (pattern_uniformity / 100) * 0.2
                else:
                    avg_speckle_diameter = 0
                    speckle_density = 0
                    coverage = 0
                    pattern_uniformity = 0
                    pattern_score = 0.3
            else:
                avg_speckle_diameter = 0
                speckle_density = 0
                coverage = 0
                pattern_uniformity = 0
                pattern_score = 0.2
        else:
            # Image too small for meaningful speckle analysis
            avg_speckle_diameter = 0
            speckle_density = 0
            coverage = 0
            pattern_uniformity = 0
            pattern_score = 0.5

        return {
            'score': pattern_score,
            'avg_speckle_diameter': avg_speckle_diameter,
            'speckle_density': speckle_density,
            'coverage': coverage,
            'pattern_uniformity': pattern_uniformity
        }

    def _calculate_noise_quality(self, gray: np.ndarray) -> Dict:
        """Calculate noise-related quality metrics."""
        # Estimate noise using bilateral filtering for better signal/noise separation
        if gray.shape[0] > 5 and gray.shape[1] > 5:
            try:
                # Use bilateral filter for signal estimation
                denoised = cv2.bilateralFilter(gray, 5, 50, 50)
            except:
                # Fallback to Gaussian blur
                denoised = cv2.GaussianBlur(gray, (5, 5), 1.0)
        else:
            # Too small for filtering
            denoised = gray.copy()

        # Calculate noise
        noise = gray.astype(float) - denoised.astype(float)
        noise_std = np.std(noise)
        signal_std = np.std(denoised)
        signal_mean = np.mean(denoised)

        # Signal-to-Noise Ratio with safe arithmetic
        if noise_std > 0:
            snr = signal_std / noise_std
            snr_db = 20 * np.log10(snr) if snr > 0 else 0
        else:
            snr = float('inf')  # Perfect signal (no noise)
            snr_db = 100.0  # Very high SNR

        # Normalize SNR for quality score (good SNR is typically >20dB)
        noise_score = min(1.0, snr_db / 30.0) if snr_db > 0 else 0

        return {
            'score': noise_score,
            'snr': snr,
            'snr_db': snr_db,
            'noise_std': noise_std,
            'signal_std': signal_std,
            'signal_mean': signal_mean
        }

    def set_weights(self, **kwargs) -> None:
        """
        Update quality metric weights.

        Args:
            **kwargs: Weight values for gradient, contrast, entropy, pattern, noise
        """
        for key, value in kwargs.items():
            if key in self.weights:
                self.weights[key] = value
            else:
                logger.warning(f"Unknown weight key: {key}")

        # Normalize weights to sum to 1.0
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for key in self.weights:
                self.weights[key] /= total_weight

        logger.info(f"Updated quality weights: {self.weights}")

    def get_weights(self) -> Dict[str, float]:
        """Get current quality metric weights."""
        return self.weights.copy()

    def calculate_quality_statistics(self, quality_scores: np.ndarray) -> Dict:
        """
        Calculate statistical metrics for a set of quality scores.

        Args:
            quality_scores: Array of quality scores (0-1 range)

        Returns:
            Dictionary of statistical metrics
        """
        if quality_scores.size == 0:
            return {
                'min_quality': 0.0,
                'max_quality': 0.0,
                'mean_quality': 0.0,
                'median_quality': 0.0,
                'std_quality': 0.0,
                'percentile_25': 0.0,
                'percentile_75': 0.0,
                'quality_range': 0.0
            }

        # Convert to percentage for reporting
        scores_percent = quality_scores * 100

        return {
            'min_quality': float(np.min(scores_percent)),
            'max_quality': float(np.max(scores_percent)),
            'mean_quality': float(np.mean(scores_percent)),
            'median_quality': float(np.median(scores_percent)),
            'std_quality': float(np.std(scores_percent)),
            'percentile_25': float(np.percentile(scores_percent, 25)),
            'percentile_75': float(np.percentile(scores_percent, 75)),
            'quality_range': float(np.max(scores_percent) - np.min(scores_percent))
        }

    def calculate_subset_quality(self, subset: np.ndarray) -> float:
        """
        Calculate quality score for a subset/patch of an image.
        
        This method is optimized for quality map generation where many small
        subsets need to be analyzed efficiently. Uses MIG/Ef-based gradient scoring.
        
        Args:
            subset: Image subset as numpy array (grayscale)
            
        Returns:
            Quality score in range 0-1
        """
        try:
            # Ensure we have a valid subset
            if subset.size == 0 or subset.shape[0] < 3 or subset.shape[1] < 3:
                return 0.0
            
            # Convert to grayscale if needed
            if len(subset.shape) == 3:
                gray = cv2.cvtColor(subset, cv2.COLOR_RGB2GRAY)
            else:
                gray = subset.copy()
            
            # Calculate simplified quality metrics for efficiency using MIG/Ef approach
            gradient_score = self._calculate_fast_gradient_quality(gray)
            contrast_score = self._calculate_fast_contrast_quality(gray)
            entropy_score = self._calculate_fast_entropy_quality(gray)
            
            # Updated weighted combination emphasizing gradient quality (aligned with main weights)
            quality_score = (
                gradient_score * 0.60 +  # Increased gradient weight for MIG/Ef emphasis
                contrast_score * 0.25 +  # Contrast quality
                entropy_score * 0.15     # Information content
            )
            
            # Apply critical quality checks - more lenient for artificial speckle patterns
            critical_factors = 0
            if gradient_score < 0.05:  # Only extremely poor gradients
                critical_factors += 1
            if contrast_score < 0.05:  # Only extremely poor contrast
                critical_factors += 1
            if entropy_score < 0.05:  # Only extremely poor entropy
                critical_factors += 1
            
            # Apply lighter penalties for critical issues
            if critical_factors >= 3:
                quality_score *= 0.3  # Moderate penalty for all critical issues
            elif critical_factors >= 2:
                quality_score *= 0.6  # Light penalty for multiple critical issues
            elif critical_factors == 1:
                quality_score *= 0.8  # Very light penalty for single critical issue
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.warning(f"Error calculating subset quality: {e}")
            return 0.0
    
    def _calculate_fast_gradient_quality(self, gray: np.ndarray) -> float:
        """
        Fast gradient quality calculation for subset analysis using GradientAnalyzer.
        """
        # Use the gradient analyzer directly for fast calculation
        quality_scores = self.gradient_analyzer.calculate_gradient_quality_score(
            gray,
            mig_norm_factor=self.mig_normalization_factor,
            ef_norm_factor=self.ef_normalization_factor,
            mig_score_multiplier=self.mig_score_multiplier,
            ef_score_multiplier=self.ef_score_multiplier
        )
        
        return quality_scores['gradient_score']
    
    def _calculate_fast_contrast_quality(self, gray: np.ndarray) -> float:
        """Fast contrast quality calculation for subset analysis."""
        mean_val = np.mean(gray)
        std_val = np.std(gray)
        
        # RMS contrast
        rms_contrast = std_val / (mean_val + 1e-6)
        
        # More discriminating contrast assessment using sigmoid-like curve
        if rms_contrast > 0.8:  # Very high contrast (excellent)
            contrast_score = 1.0
        elif rms_contrast > 0.5:  # High contrast (very good)
            contrast_score = 0.7 + 0.3 * (rms_contrast - 0.5) / 0.3
        elif rms_contrast > 0.3:  # Medium contrast (good)
            contrast_score = 0.4 + 0.3 * (rms_contrast - 0.3) / 0.2
        elif rms_contrast > 0.15:  # Low contrast (fair)
            contrast_score = 0.2 + 0.2 * (rms_contrast - 0.15) / 0.15
        elif rms_contrast > 0.05:  # Very low contrast (poor)
            contrast_score = 0.1 + 0.1 * (rms_contrast - 0.05) / 0.1
        else:  # Extremely low contrast (critical)
            contrast_score = rms_contrast * 2  # Linear scaling for very low values
        
        # Check for over-saturation
        if rms_contrast > 1.5:  # Very high contrast might indicate noise
            contrast_score *= 0.8
        
        return min(1.0, contrast_score)
    
    def _calculate_fast_entropy_quality(self, gray: np.ndarray) -> float:
        """Fast entropy quality calculation for subset analysis."""
        # Calculate histogram with fewer bins for speed
        hist, _ = np.histogram(gray, bins=32, range=(0, 256), density=True)
        
        # Shannon entropy
        hist = hist[hist > 0]  # Remove zero bins
        if len(hist) == 0:
            return 0.0
            
        entropy_val = -np.sum(hist * np.log2(hist))
        
        # More discriminating entropy assessment using sigmoid-like curve
        # Max entropy for 32 bins is log2(32) = 5
        if entropy_val > 4.0:  # Very high entropy (excellent)
            entropy_score = 1.0
        elif entropy_val > 3.0:  # High entropy (very good)
            entropy_score = 0.7 + 0.3 * (entropy_val - 3.0) / 1.0
        elif entropy_val > 2.0:  # Medium entropy (good)
            entropy_score = 0.4 + 0.3 * (entropy_val - 2.0) / 1.0
        elif entropy_val > 1.0:  # Low entropy (fair)
            entropy_score = 0.2 + 0.2 * (entropy_val - 1.0) / 1.0
        elif entropy_val > 0.5:  # Very low entropy (poor)
            entropy_score = 0.1 + 0.1 * (entropy_val - 0.5) / 0.5
        else:  # Extremely low entropy (critical)
            entropy_score = entropy_val * 0.2  # Linear scaling for very low values
        
        return min(1.0, entropy_score)

    def calculate_live_analysis_quality(self, image: np.ndarray, roi_coords: Optional[List[Tuple[int, int]]] = None,
                                        grid_size: Optional[Tuple[int, int]] = None) -> Tuple[np.ndarray, float]:
        """
        Calculate quality map for live analysis with optional ROI masking.

        Args:
            image: Input image array
            roi_coords: Optional polygon ROI coordinates (image-relative)
            grid_size: Optional grid size for quality map

        Returns:
            Tuple of (quality_map, overall_score)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()

        # Create ROI mask if coordinates provided
        roi_mask = None
        if roi_coords and len(roi_coords) >= 3:
            roi_mask = np.zeros(gray.shape[:2], dtype=np.uint8)
            pts = np.array(roi_coords, dtype=np.int32)

            # Clamp coordinates to image bounds
            h, w = gray.shape
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

            cv2.fillPoly(roi_mask, [pts], 255)

            # Apply mask to image for analysis
            masked_gray = cv2.bitwise_and(gray, gray, mask=roi_mask)
        else:
            masked_gray = gray

        # Calculate quality map using gradient analysis (fast for live mode)
        grad_x = cv2.Sobel(masked_gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(masked_gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Normalize
        max_grad = gradient_magnitude.max()
        if max_grad > 0:
            quality_map = gradient_magnitude / max_grad
        else:
            quality_map = np.zeros_like(gradient_magnitude)

        # Apply smoothing
        quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)

        # Calculate overall score
        if roi_mask is not None:
            # Score only from ROI pixels
            roi_pixels = quality_map[roi_mask > 0]
            overall_score = float(np.mean(roi_pixels)) if len(roi_pixels) > 0 else 0.0
        else:
            # Score from entire image
            overall_score = float(np.mean(quality_map))

        # Log the analysis details
        logger.info(f"Full quality score: {overall_score:.3f} (using MIG={self.mig_normalization_factor}, Ef={self.ef_normalization_factor})")
        logger.info(f"Generating simplified quality map for visualization...")
        logger.info(
            f"Live analysis complete: score={overall_score:.3f}, grid={grid_size if grid_size else 'auto'}, image={gray.shape}")

        return quality_map, overall_score

    def _calculate_quality_map_with_mask(self, gray: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Calculate quality map only for masked regions."""
        # Use gradient-based quality for speed
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # Normalize and apply mask
        quality_map = gradient_magnitude / (gradient_magnitude.max() + 1e-6)
        quality_map = quality_map * (mask / 255.0)  # Apply mask

        return quality_map

    def calculate_live_analysis_quality_parallel(self, image: np.ndarray, grid_size: tuple = None) -> tuple:
        """
        Parallel version of calculate_live_analysis_quality for better performance.

        Uses ThreadPoolExecutor to process grid cells in parallel while maintaining
        accuracy of DIC calculations.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        try:
            # Ensure grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()

            h, w = gray.shape

            # Step 1: Calculate accurate overall score (same as before)
            full_metrics = self.analyze_comprehensive(gray)
            overall_score = self.calculate_overall_quality_score(full_metrics)

            # Step 2: Generate quality map using parallel processing
            if grid_size is None:
                if min(h, w) < 100:
                    grid_size = (5, 5)
                elif min(h, w) < 300:
                    grid_size = (10, 10)
                elif min(h, w) < 600:
                    grid_size = (15, 15)
                else:
                    grid_size = (20, 20)

            grid_rows, grid_cols = grid_size
            cell_h = h // grid_rows
            cell_w = w // grid_cols

            # Initialize quality grid
            quality_grid = np.zeros((grid_rows, grid_cols), dtype=np.float32)

            # Prepare cell data for parallel processing
            cell_tasks = []
            for i in range(grid_rows):
                for j in range(grid_cols):
                    y_start = i * cell_h
                    y_end = min((i + 1) * cell_h, h)
                    x_start = j * cell_w
                    x_end = min((j + 1) * cell_w, w)

                    cell = gray[y_start:y_end, x_start:x_end]
                    cell_tasks.append(((i, j), cell))

            # Process cells in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_cell = {}

                for (i, j), cell in cell_tasks:
                    future = executor.submit(self.calculate_subset_quality, cell)
                    future_to_cell[future] = (i, j)

                # Collect results
                for future in as_completed(future_to_cell):
                    i, j = future_to_cell[future]
                    try:
                        quality_grid[i, j] = future.result()
                    except Exception as e:
                        logger.error(f"Error processing cell ({i},{j}): {e}")
                        quality_grid[i, j] = 0.0

            # Upscale and smooth
            quality_map = cv2.resize(quality_grid, (w, h), interpolation=cv2.INTER_CUBIC)
            quality_map = cv2.GaussianBlur(quality_map, (3, 3), 0.5)
            quality_map = np.clip(quality_map, 0, 1)

            return quality_map, overall_score

        except Exception as e:
            logger.error(f"Error in calculate_live_analysis_quality_parallel: {e}")
            return np.zeros_like(gray, dtype=np.float32), 0.0

    def assess_quality_level(self, score: float, spectrum_type: str = 'optimized') -> Tuple[str, str]:
        """
        Assess quality level based on score and spectrum type.

        Args:
            score: Quality score (0-100)
            spectrum_type: Type of quality spectrum being used

        Returns:
            Tuple of (quality_level, color_hex)
        """
        if spectrum_type == 'optimized':
            # Realistic DIC assessment with practical thresholds
            if score >= 80:
                return "Excellent for DIC", "#0000ff"
            elif score >= 60:
                return "Very Good for DIC", "#00ff00"
            elif score >= 40:
                return "Good for DIC", "#ffff00"
            elif score >= 25:
                return "Fair for DIC", "#ff7f00"
            elif score >= 10:
                return "Poor for DIC", "#ff0000"
            else:
                return "Critical - Not suitable for DIC", "#000000"

        elif spectrum_type == 'controlled':
            # Controlled method realistic thresholds
            if score >= 75:
                return "Excellent for DIC", "#0064ff"
            elif score >= 60:
                return "Good for DIC", "#00ffff"
            elif score >= 45:
                return "Acceptable for DIC", "#ffff00"
            elif score >= 30:
                return "Challenging for DIC", "#ff8c00"
            elif score >= 15:
                return "Poor for DIC", "#ff0000"
            else:
                return "Unusable for DIC", "#320000"

        elif spectrum_type == 'custom_dic':
            # Custom DIC assessment optimized for artificial speckle patterns
            if score >= 85:
                return "Excellent for DIC", "#0000ff"
            elif score >= 70:
                return "Very Good for DIC", "#00ff00"
            elif score >= 50:
                return "Good for DIC", "#ffff00"
            elif score >= 30:
                return "Fair for DIC", "#ff7f00"
            elif score >= 15:
                return "Poor for DIC", "#ff0000"
            elif score >= 5:
                return "Very Poor for DIC", "#800000"
            else:
                return "Critical - Not suitable for DIC", "#000000"

        else:
            # Default to optimized thresholds
            return self.assess_quality_level(score, 'optimized')