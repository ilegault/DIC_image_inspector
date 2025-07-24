# core/report_generator.py - Report Generation Logic

import datetime
from typing import Dict, List, Optional, Tuple
import logging
from utils.shared_logging import shared_logger

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive analysis reports for DIC quality assessment.

    This class handles the creation of detailed technical reports, non-technical
    explanations, and recommendations based on analysis results.
    """

    def __init__(self):
        """Initialize the report generator."""
        self.report_sections = {
            'executive': self._generate_executive_summary,
            'technical': self._generate_technical_analysis,
            'recommendations': self._generate_recommendations,
            'mathematical': self._generate_mathematical_content,
            'non_technical': self._generate_non_technical_explanation,
            'dic_parameters': self._generate_dic_parameters,
            'image_info': self._generate_image_information,
            'quality_criteria': self._generate_quality_criteria
        }

    def generate_comprehensive_report(self, analysis_results: Dict,
                                      image_info: Optional[Dict] = None,
                                      roi_info: Optional[Dict] = None) -> str:
        """
        Generate a complete comprehensive report.

        Args:
            analysis_results: Results from quality analysis
            image_info: Information about the analyzed image
            roi_info: Information about ROI if used

        Returns:
            Complete report as formatted string
        """
        sections = []

        # Header
        sections.append(self._generate_report_header())

        # Executive Summary
        sections.append(self._generate_executive_summary(analysis_results))

        # Image Information
        if image_info or roi_info:
            sections.append(self._generate_image_information(image_info, roi_info))

        # Technical Analysis
        sections.append(self._generate_technical_analysis(analysis_results))

        # DIC Parameters
        sections.append(self._generate_dic_parameters(analysis_results))

        # Recommendations
        sections.append(self._generate_recommendations(analysis_results))

        # Non-Technical Explanation
        sections.append(self._generate_non_technical_explanation(analysis_results))

        # Mathematical Background
        sections.append(self._generate_mathematical_content(analysis_results))

        # Quality Assessment Criteria
        sections.append(self._generate_quality_criteria(analysis_results))

        # Footer
        sections.append(self._generate_report_footer())

        return '\n\n'.join(sections)

    def _generate_report_header(self) -> str:
        """Generate report header with title and metadata."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return f"""{"=" * 80}
           DIC IMAGE QUALITY ANALYSIS REPORT
{"=" * 80}
Generated: {timestamp}
Software: DIC Image Quality Inspector
{"=" * 80}"""

    def _generate_executive_summary(self, results: Dict) -> str:
        """Generate executive summary section."""
        overall_score = results.get('overall_score', 0)
        spectrum_used = results.get('spectrum_used', 'optimized')
        analysis_method = results.get('analysis_method', 'Full image')

        # Get quality assessment
        quality_text, _ = self._assess_quality_level(overall_score, spectrum_used)

        return f"""EXECUTIVE SUMMARY
{"-" * 40}
Overall Quality Score: {overall_score:.1f}/100
Assessment: {quality_text}
Analysis Method: {analysis_method}
Method Used: {spectrum_used.replace('_', ' ').title()}

BOTTOM LINE UP FRONT:
{self._generate_bluf(overall_score, spectrum_used)}"""

    def _generate_technical_analysis(self, results: Dict) -> str:
        """Generate technical analysis section."""
        overall_score = results.get('overall_score', 0)
        quality_std = results.get('quality_std', 0)
        stats = results.get('quality_map_stats', {})

        return f"""TECHNICAL ANALYSIS
{"-" * 40}
Quality Statistics:
  • Maximum Quality: {stats.get('max_quality', 0):.1f}%
  • Average Quality: {overall_score:.1f}%
  • Minimum Quality: {stats.get('min_quality', 0):.1f}%
  • Median Quality: {stats.get('median_quality', 0):.1f}%
  • Standard Deviation: {quality_std:.1f}%

Analysis Algorithm:
  The analysis uses advanced subset-based quality assessment including:
  • Gradient content analysis (Mean Intensity Gradient - MIG)
  • Enhanced feature calculation (Ef) combining first and second-order gradients
  • Speckle morphology evaluation
  • Contrast distribution assessment
  • Pattern uniqueness calculation
  • Noise resistance evaluation"""

    def _generate_dic_parameters(self, results: Dict) -> str:
        """Generate DIC parameters section."""
        dic_params = self._calculate_dic_parameters(results)

        return f"""RECOMMENDED DIC PARAMETERS
{"-" * 40}
Correlation Setup:
  • Subset Size (Facet): {dic_params['facet_size']} pixels
  • Step Size: {dic_params['step_size']} pixels
  • Overlap: {dic_params['overlap']}%
  • Expected Accuracy: {dic_params['accuracy']}

Parameter Explanation:
  • Subset Size: Optimal size for correlation windows based on pattern analysis
  • Step Size: Recommended spacing between correlation points
  • Overlap: Percentage overlap between adjacent subsets
  • Expected Accuracy: Predicted displacement measurement precision"""

    def _generate_recommendations(self, results: Dict) -> str:
        """Generate recommendations section."""
        overall_score = results.get('overall_score', 0)
        spectrum_used = results.get('spectrum_used', 'custom_dic')

        recommendations = self._generate_recommendation_list(overall_score, spectrum_used)

        recommendations_text = f"""DETAILED RECOMMENDATIONS
{"-" * 40}"""

        for i, rec in enumerate(recommendations, 1):
            recommendations_text += f"\n{i:2d}. {rec}"

        return recommendations_text

    def _generate_non_technical_explanation(self, results: Dict) -> str:
        """Generate non-technical explanation section."""
        score = results.get('overall_score', 0)
        analysis_method = results.get('analysis_method', 'Full image')

        explanation = f"""WHAT THIS MEANS (NON-TECHNICAL EXPLANATION)
{"-" * 60}
Digital Image Correlation (DIC) Analysis Explanation:

WHAT WE MEASURED:
This analysis examined your image to determine how well it will work for measuring
tiny movements and deformations. Think of it like checking if a photograph has
enough detail and contrast to track specific points accurately.

YOUR RESULT: {score:.1f}/100

WHAT THIS SCORE MEANS:"""

        if score >= 90:
            explanation += """
• EXCELLENT: Your image has outstanding quality for precise measurements
• The pattern has excellent contrast and detail
• You can expect very accurate displacement measurements
• Perfect for critical engineering applications"""
        elif score >= 75:
            explanation += """
• VERY GOOD: Your image has good quality for reliable measurements
• The pattern has good contrast and sufficient detail
• You can expect reliable displacement measurements
• Suitable for most engineering applications"""
        elif score >= 60:
            explanation += """
• GOOD: Your image has acceptable quality for measurements
• The pattern has reasonable contrast and detail
• You can expect moderately accurate measurements
• May need careful analysis parameter selection"""
        elif score >= 45:
            explanation += """
• ACCEPTABLE: Your image has marginal quality for measurements
• The pattern has limited contrast or detail
• Measurements may have increased uncertainty
• Consider improving lighting or pattern if possible"""
        elif score >= 30:
            explanation += """
• CHALLENGING: Your image has poor quality for precise measurements
• The pattern lacks sufficient contrast or detail
• Measurements will have significant uncertainty
• Strong recommendation to improve the image quality"""
        else:
            explanation += """
• POOR: Your image is not suitable for reliable measurements
• The pattern lacks the necessary contrast and detail
• Measurements will be unreliable or may fail completely
• Image quality improvement is essential before proceeding"""

        explanation += f"""

HOW THE ANALYSIS WORKS:
The software examines small regions (subsets) across your image, looking for:
• Sharp edges and clear patterns that can be tracked accurately
• Good contrast between light and dark areas
• Consistent lighting without shadows or glare
• Appropriate speckle or texture patterns for correlation

ANALYSIS METHOD USED:
{analysis_method} - This tells you whether we analyzed your entire image or
just the region you selected.

NEXT STEPS:
Based on your score of {score:.1f}/100, please review the recommendations
section for specific guidance on whether to proceed with your current setup
or make improvements first."""

        return explanation

    def _generate_mathematical_content(self, results: Dict) -> str:
        """Generate mathematical background section."""
        overall_score = results.get('overall_score', 0)
        dic_params = self._calculate_dic_parameters(results)
        spectrum_used = results.get('spectrum_used', 'custom_dic')

        return f"""MATHEMATICAL BACKGROUND & EQUATIONS
{"-" * 60}

1. GRADIENT CONTENT ANALYSIS
{"=" * 30}
The primary quality metric is based on advanced gradient analysis using MIG and Ef calculations:

First-Order Gradient Calculation (Sobel operator):
    Gx(x,y) = I(x+1,y-1) + 2×I(x+1,y) + I(x+1,y+1) - I(x-1,y-1) - 2×I(x-1,y) - I(x-1,y+1)
    Gy(x,y) = I(x-1,y+1) + 2×I(x,y+1) + I(x+1,y+1) - I(x-1,y-1) - 2×I(x,y-1) - I(x+1,y-1)

First-Order Gradient Magnitude:
    |∇I(x,y)| = √(Gx² + Gy²)

Mean Intensity Gradient (MIG) - Pan et al., 2009:
    MIG = (1/N) × Σ Σ |∇I(x,y)|
                  x y
    where N = total number of pixels

Second-Order Gradient Calculation:
    Gxx = ∂²I/∂x²,  Gyy = ∂²I/∂y²,  Gxy = ∂²I/∂x∂y

Second-Order Gradient Magnitude:
    |∇²I(x,y)| = √(Gxx² + Gyy² + 2×Gxy²)

Enhanced Feature (Ef) - Hu et al., 2021:
    Ef = α × MIG + β × (1/N) × Σ Σ |∇²I(x,y)|
                              x y
    where α = 0.7, β = 0.3 (weighting coefficients)

2. CONTRAST ANALYSIS
{"=" * 20}
Multiple contrast measures are computed and combined:

RMS Contrast:
    C_rms = σ / μ
    where σ = standard deviation, μ = mean intensity

Michelson Contrast:
    C_michelson = (I_max - I_min) / (I_max + I_min)

Weber Contrast:
    C_weber = (I_max - μ) / μ

Combined Contrast Score:
    C_total = 0.4×C_rms + 0.3×C_michelson + 0.2×C_weber + 0.1×C_local

3. OVERALL QUALITY COMPUTATION
{"=" * 30}
The final quality score is a weighted combination emphasizing MIG/Ef metrics:

Q_total = w₁×Q_gradient + w₂×Q_contrast + w₃×Q_entropy + w₄×Q_pattern + w₅×Q_noise

where Q_gradient is computed using MIG and Ef:
    Q_gradient = (Ef_score × 0.8 + MIG_score × 0.2) × distribution_bonus

MIG and Ef Scoring:
    MIG_score = min(1.0, normalized_MIG × 6)
    Ef_score = min(1.0, normalized_Ef × 4)
    normalized_MIG = MIG / 255.0
    normalized_Ef = Ef / 255.0

Standard weights:
    w₁ = 0.60  (Gradient content - MIG/Ef emphasis for DIC)
    w₂ = 0.20  (Contrast quality)
    w₃ = 0.10  (Information content)
    w₄ = 0.05  (Pattern complexity)
    w₅ = 0.05  (Noise level)

Constraint: Σwᵢ = 1.0

4. DIC-SPECIFIC CALCULATIONS
{"=" * 30}
Subset Size Optimization:
    s_opt = max(11, min(51, 2.5 × d_feature))
    where d_feature is the average feature diameter

Step Size Calculation:
    step = s_opt × (1 - overlap_fraction)
    typically overlap_fraction = 0.75 (75% overlap)

Expected Displacement Accuracy:
    σ_displacement ≈ 0.01 to 0.1 pixels (depending on quality score)

CURRENT ANALYSIS RESULTS:
Overall Quality Score: {overall_score:.1f}/100 ({overall_score / 100:.3f} normalized)
Optimized DIC Parameters:
  • Subset size (s_opt): {dic_params['facet_size']} pixels
  • Step size: {dic_params['step_size']} pixels
  • Overlap ratio: {dic_params['overlap'] / 100:.2f}
  • Expected accuracy: {dic_params['accuracy']}

Analysis Configuration:
  • Color spectrum: {spectrum_used}

References:
• Pan, B. et al. (2009). Mean intensity gradient: An effective global parameter for quality assessment of the speckle patterns used in digital image correlation. Optics and Lasers in Engineering.
• Hu, Z. et al. (2021). Enhanced feature for quality assessment of speckle patterns in digital image correlation. Measurement Science and Technology.
• Pan, B. (2018). Digital image correlation for surface deformation measurement.
• Sutton, M.A. et al. (2009). Image correlation for shape, motion and deformation measurements.
• Reu, P.L. (2015). All about speckles: Speckle density. Experimental Techniques.
• Blaber, J. et al. (2015). Ncorr: Open-source 2D digital image correlation."""

    def _generate_quality_criteria(self, results: Dict) -> str:
        """Generate quality assessment criteria section."""
        spectrum_used = results.get('spectrum_used', 'custom_dic')

        criteria = f"""QUALITY ASSESSMENT CRITERIA
{"-" * 40}"""

        if spectrum_used == 'custom_dic':
            criteria += """
Using STRICT DIC-ONLY Assessment Criteria:
  • 95-100%: Perfect for DIC (Blue)
  • 90-95%:  Excellent for DIC (Cyan)
  • 85-90%:  Very Good for DIC (Yellow)
  • 80-85%:  Good for DIC (Orange)
  • 75-80%:  Minimum for DIC (Red)
  • 0-75%:   NOT suitable for DIC (Black)

NOTE: This strict assessment only considers patterns with 75%+ scores
      as suitable for DIC applications."""
        else:
            criteria += f"""
Using {spectrum_used.replace('_', ' ').title()} Assessment Criteria:
  • 75-100%: Excellent for DIC
  • 60-75%:  Very Good for DIC
  • 45-60%:  Good for DIC
  • 30-45%:  Acceptable for DIC
  • 15-30%:  Challenging for DIC
  • 0-15%:   Poor for DIC

NOTE: More lenient thresholds suitable for general pattern evaluation."""

        return criteria

    def _generate_image_information(self, image_info: Optional[Dict],
                                    roi_info: Optional[Dict]) -> str:
        """Generate image information section."""
        info_text = f"""IMAGE INFORMATION
{"-" * 40}"""

        if image_info:
            info_text += f"""
Image Dimensions: {image_info.get('width', 'Unknown')} × {image_info.get('height', 'Unknown')} pixels
Total Image Area: {image_info.get('total_area', 'Unknown'):,} pixels"""

        if roi_info:
            info_text += f"""
ROI Area: {roi_info.get('area', 'Unknown'):.0f} pixels² ({roi_info.get('percentage', 0):.1f}% of image)
ROI Points: {roi_info.get('point_count', 'Unknown')} vertices"""
        else:
            info_text += """
Analysis Region: Full image"""

        return info_text

    def _generate_report_footer(self) -> str:
        """Generate report footer."""
        return f"""{"=" * 80}
End of Report
{"=" * 80}"""

    def _calculate_dic_parameters(self, results: Dict) -> Dict:
        """Calculate recommended DIC parameters."""
        # Use optimal subset size from analysis if available
        facet_size = results.get('optimal_subset_size', 21)

        # Calculate step size for standard DIC overlap (75%)
        overlap_percent = 75
        step_size = max(1, int(facet_size * (1 - overlap_percent / 100)))

        # Determine expected accuracy based on pattern quality
        score = results.get('overall_score', 0)
        if score >= 90:
            accuracy = "±0.005-0.01 pixels"
        elif score >= 75:
            accuracy = "±0.01-0.02 pixels"
        elif score >= 60:
            accuracy = "±0.02-0.05 pixels"
        elif score >= 45:
            accuracy = "±0.05-0.1 pixels"
        elif score >= 30:
            accuracy = "±0.1-0.2 pixels"
        else:
            accuracy = "±0.2+ pixels (unreliable)"

        return {
            'facet_size': facet_size,
            'step_size': step_size,
            'overlap': overlap_percent,
            'accuracy': accuracy
        }

    def _generate_recommendation_list(self, score: float, spectrum_type: str) -> List[str]:
        """Generate list of recommendations based on score and spectrum."""
        recommendations = []

        if spectrum_type == 'custom_dic':
            # Strict DIC-only recommendations
            if score >= 95:
                recommendations.extend([
                    " PERFECT pattern! Ideal for high-precision DIC analysis.",
                    "Use finest correlation parameters for maximum accuracy.",
                    "Consider this as a reference pattern for other setups.",
                    "Expected accuracy: ±0.001-0.005 pixels"
                ])
            elif score >= 90:
                recommendations.extend([
                    " EXCELLENT pattern quality for precision DIC work.",
                    "Use standard DIC parameters with confidence.",
                    "Expect sub-pixel accuracy in correlation results.",
                    "Expected accuracy: ±0.005-0.01 pixels"
                ])
            elif score >= 85:
                recommendations.extend([
                    " VERY GOOD pattern for DIC analysis.",
                    "Use recommended DIC parameters - good correlation expected.",
                    "Suitable for most strain measurement applications.",
                    "Expected accuracy: ±0.01-0.02 pixels"
                ])
            elif score >= 80:
                recommendations.extend([
                    " GOOD pattern quality for DIC applications.",
                    "Acceptable correlation reliability with standard parameters.",
                    "Monitor correlation quality during analysis.",
                    "Expected accuracy: ±0.02-0.03 pixels"
                ])
            elif score >= 75:
                recommendations.extend([
                    " MINIMUM pattern - threshold for DIC analysis.",
                    "Use larger subset sizes (increase by 30-50%) for better correlation.",
                    "Monitor correlation quality very closely during analysis.",
                    "Strong recommendation to improve pattern if possible.",
                    "Expected accuracy: ±0.03-0.05 pixels"
                ])
            else:
                recommendations.extend([
                    " CRITICAL: Pattern NOT suitable for DIC analysis.",
                    " MANDATORY recommendation to reapply or enhance speckle pattern.",
                    "Current pattern will result in correlation failure and unreliable results.",
                    "Consider alternative measurement techniques.",
                    " Do not proceed with DIC analysis using this pattern."
                ])
        else:
            # More realistic recommendations for other spectrums
            if score >= 75:
                recommendations.extend([
                    "Excellent pattern! Proceed with DIC analysis using recommended parameters.",
                    "Consider using sub-pixel interpolation for maximum accuracy.",
                    "Pattern has optimal gradient content and speckle morphology."
                ])
            elif score >= 60:
                recommendations.extend([
                    "Very good pattern quality. DIC analysis should work excellently.",
                    "Use standard DIC parameters with confidence.",
                    "Monitor correlation quality during analysis for best results."
                ])
            elif score >= 45:
                recommendations.extend([
                    "Good pattern for DIC analysis with proper setup.",
                    "Use recommended subset sizes and overlap settings.",
                    "Consider slightly larger subset sizes if correlation issues occur."
                ])
            elif score >= 30:
                recommendations.extend([
                    "Acceptable pattern for DIC analysis with careful setup.",
                    "Use larger subset sizes (increase by 20-30%) for better correlation.",
                    "Monitor correlation quality closely during analysis.",
                    "Consider post-processing filtering if needed."
                ])
            elif score >= 15:
                recommendations.extend([
                    "Challenging but workable pattern for DIC analysis.",
                    "Use larger subset sizes and stricter correlation criteria.",
                    "Expect some areas to have poor correlation - filter results carefully.",
                    "Consider pattern enhancement if critical accuracy is needed."
                ])
            else:
                recommendations.extend([
                    "Poor pattern quality - DIC will have significant limitations.",
                    "Strong recommendation to improve or reapply speckle pattern.",
                    "If proceeding: use maximum subset sizes and very strict filtering.",
                    "Consider alternative measurement techniques if high accuracy needed."
                ])

        # Add spectrum-specific note
        if spectrum_type == 'custom_dic':
            recommendations.extend([
                " Note: Using strict DIC-only quality assessment.",
                "Only patterns rated 75%+ are considered suitable for DIC work."
            ])
        else:
            spectrum_name = spectrum_type.replace('_', ' ').title()
            recommendations.extend([
                f" Note: Using {spectrum_name} spectrum assessment.",
                "Professional DIC quality evaluation with appropriate thresholds."
            ])

        return recommendations

    def _assess_quality_level(self, score: float, spectrum_type: str) -> Tuple[str, str]:
        """Assess quality level based on score and spectrum type."""
        if spectrum_type == 'custom_dic':
            # Strict DIC-only assessment
            if score >= 95:
                return "Perfect for DIC", "#008cff"
            elif score >= 90:
                return "Excellent for DIC", "#78ffb4"
            elif score >= 85:
                return "Very Good for DIC", "#ffc800"
            elif score >= 80:
                return "Good for DIC", "#ff5000"
            elif score >= 75:
                return "Minimum for DIC", "#780000"
            else:
                return "CRITICAL - Not suitable for DIC", "#000000"
        else:
            # More realistic thresholds
            if score >= 75:
                return "Excellent for DIC", "#27ae60"
            elif score >= 60:
                return "Very Good for DIC", "#2ecc71"
            elif score >= 45:
                return "Good for DIC", "#f39c12"
            elif score >= 30:
                return "Acceptable for DIC", "#e67e22"
            elif score >= 15:
                return "Challenging for DIC", "#e74c3c"
            else:
                return "Poor for DIC", "#8e44ad"

    def _generate_bluf(self, score: float, spectrum_type: str) -> str:
        """Generate Bottom Line Up Front summary."""
        quality_text, _ = self._assess_quality_level(score, spectrum_type)

        if score >= 90:
            return f" PROCEED - {quality_text}. Your image is excellent for DIC analysis."
        elif score >= 75:
            return f" PROCEED - {quality_text}. Your image is suitable for DIC analysis."
        elif score >= 60:
            return f" PROCEED WITH CAUTION - {quality_text}. Consider larger subset sizes."
        elif score >= 45:
            return f" MARGINAL - {quality_text}. Use with care and larger parameters."
        elif score >= 30:
            return f" NOT RECOMMENDED - {quality_text}. Consider pattern improvement."
        else:
            return f" DO NOT PROCEED - {quality_text}. Pattern enhancement required."

    def generate_section(self, section_type: str, analysis_results: Dict,
                         **kwargs) -> str:
        """
        Generate a specific section of the report.

        Args:
            section_type: Type of section to generate
            analysis_results: Analysis results dictionary
            **kwargs: Additional arguments for specific sections

        Returns:
            Formatted section text
        """
        if section_type in self.report_sections:
            try:
                return self.report_sections[section_type](analysis_results, **kwargs)
            except Exception as e:
                logger.error(f"Error generating {section_type} section: {e}")
                return f"Error generating {section_type} section: {str(e)}"
        else:
            logger.warning(f"Unknown report section type: {section_type}")
            return f"Unknown section type: {section_type}"

    def get_available_sections(self) -> List[str]:
        """Get list of available report sections."""
        return list(self.report_sections.keys())

    def save_report_to_file(self, report_content: str, filename: str) -> bool:
        """
        Save report content to a file using shared logging system.

        Args:
            report_content: The complete report text
            filename: Target filename

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use shared logging system for DIC quality reports
            filepath = shared_logger.write_text_log('dic_quality', filename, report_content)
            logger.info(f"✅ Report saved to shared logging directory: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save report to {filename}: {e}")
            return False

    def save_report_to_export_directory(self, report_content: str, filename: str) -> bool:
        """
        Save report content to shared export directory for cross-app access.

        Args:
            report_content: The complete report text
            filename: Target filename

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use shared export directory for reports that should be accessible by all apps
            filepath = shared_logger.write_text_log('export', filename, report_content)
            logger.info(f"📤 Report exported to shared directory: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export report to {filename}: {e}")
            return False