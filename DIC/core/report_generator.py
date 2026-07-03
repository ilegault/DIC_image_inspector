"""
Report generation module for DIC quality assessment results.

This module handles the creation of comprehensive analysis reports including
technical details, non-technical explanations, DIC parameter recommendations,
and quality criteria assessments. It provides formatted text reports suitable
for documentation and export.

Usage:
    from core.report_generator import ReportGenerator

    generator = ReportGenerator()
    report = generator.generate_comprehensive_report(analysis_results, image_info, roi_info)
"""

import datetime
from typing import Dict, List, Optional, Tuple
import logging
from DIC.utils.shared_logging import shared_logger

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

        # Score Breakdown (new: per-component table)
        sections.append(self._generate_score_breakdown(analysis_results))

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

    def _generate_score_breakdown(self, results: Dict) -> str:
        """Generate per-component score breakdown table."""
        cs = results.get('component_scores', {})

        header = f"""SCORE BREAKDOWN
{"-" * 40}"""

        if not cs or not any(k in cs for k in ('gradient', 'contrast', 'entropy', 'pattern', 'noise')):
            return header + "\nScore breakdown unavailable for this analysis."

        order = ['gradient', 'contrast', 'entropy', 'pattern', 'noise']
        labels = {'gradient': 'Gradient', 'contrast': 'Contrast',
                  'entropy': 'Entropy', 'pattern': 'Pattern', 'noise': 'Noise'}

        rows = [f"{'Component':<12}  {'Weight':>6}  {'Score/100':>9}  {'Contributes':>12}"]
        rows.append("-" * 44)

        total = 0.0
        for name in order:
            if name not in cs:
                continue
            comp = cs[name]
            weight = comp.get('weight', 0)
            score = comp.get('score', 0)
            contrib = comp.get('weighted_contribution', 0)
            total += contrib
            rows.append(f"{labels[name]:<12}  {weight*100:>5.0f}%  {score:>9.1f}  {contrib:>10.1f} pts")

        rows.append("-" * 44)
        rows.append(f"Overall score (sum of contributions): {total:.1f} / 100")

        # Key sub-metrics
        sub_lines = []
        if 'gradient' in cs:
            gm = cs['gradient'].get('sub_metrics', {})
            if gm.get('MIG', 0) or gm.get('Ef', 0):
                sub_lines.append(f"  Gradient sub-metrics: MIG={gm.get('MIG', 0):.2f}, Ef={gm.get('Ef', 0):.2f}, "
                                  f"distribution_bonus={gm.get('distribution_bonus', 0):.3f}")
        if 'noise' in cs:
            nm = cs['noise'].get('sub_metrics', {})
            if nm.get('snr_db', 0):
                sub_lines.append(f"  Noise sub-metrics: SNR={nm.get('snr_db', 0):.1f} dB")

        body = "\n".join(rows)
        if sub_lines:
            body += "\n\n" + "\n".join(sub_lines)

        return header + "\n" + body

    def _generate_technical_analysis(self, results: Dict) -> str:
        """Generate technical analysis section."""
        overall_score = results.get('overall_score', 0)
        stats = results.get('quality_map_stats', {})

        mean_map = stats.get('mean_quality', overall_score)
        max_q = stats.get('max_quality', 0)
        min_q = stats.get('min_quality', 0)
        median_q = stats.get('median_quality', 0)
        std_q = stats.get('std_quality', 0)

        lines = [
            f"TECHNICAL ANALYSIS",
            f"{'-' * 40}",
            f"Quality Statistics:",
            f"  • Maximum map quality: {max_q:.1f}%",
            f"  • Average map quality (spatial): {mean_map:.1f}%",
            f"  • Minimum map quality: {min_q:.1f}%",
        ]
        if median_q != 0.0:
            lines.append(f"  • Median: {median_q:.1f}%")
        if std_q != 0.0:
            lines.append(f"  • Std Deviation: {std_q:.1f}%")

        lines += [
            "",
            "Analysis Algorithm:",
            "  The analysis uses advanced subset-based quality assessment including:",
            "  • Gradient content analysis (Mean Intensity Gradient - MIG)",
            "  • Enhanced feature calculation (Ef) combining first and second-order gradients",
            "  • Speckle morphology evaluation",
            "  • Contrast distribution assessment",
            "  • Pattern uniqueness calculation",
            "  • Noise resistance evaluation",
        ]

        return "\n".join(lines)

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
        spectrum_used = results.get('spectrum_used', 'optimized')
        quality_text, _ = self._assess_quality_level(score, spectrum_used)

        if score >= 75:
            action = "Proceed with DIC analysis using recommended parameters."
        elif score >= 60:
            action = "Proceed with caution — consider larger subset sizes."
        elif score >= 45:
            action = "Use with care; larger subsets and strict filtering recommended."
        elif score >= 30:
            action = "Pattern improvement strongly recommended before proceeding."
        else:
            action = "Pattern is not suitable — reapply or enhance speckle pattern first."

        return f"""WHAT THIS MEANS (NON-TECHNICAL EXPLANATION)
{"-" * 60}
DIC (Digital Image Correlation) tracks a speckle pattern between images to
measure displacement and strain. Pattern quality directly determines how
accurately those measurements can be made.

Overall score: {score:.1f}/100 — {quality_text}

Next step: {action}

Consult the Score Breakdown above and the Recommendations section for
specific guidance on which aspects of the pattern to improve."""

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
The final quality score is a weighted combination of all five components:

Q_total = w_gradient×Q_gradient + w_contrast×Q_contrast + w_entropy×Q_entropy
        + w_pattern×Q_pattern + w_noise×Q_noise
(each Q on 0–1 scale, then ×100 for the 0–100 score)

where Q_gradient is computed using MIG and Ef:
    Q_gradient = (Ef_score × 0.8 + MIG_score × 0.2) × distribution_bonus

MIG and Ef Scoring:
    # keep in sync with QualityCalculator.__init__
    normalized_MIG = MIG / 50      (mig_normalization_factor = 50)
    normalized_Ef  = Ef  / 40      (ef_normalization_factor = 40)
    MIG_score = min(1.0, normalized_MIG × 2.0)   (mig_score_multiplier = 2.0)
    Ef_score  = min(1.0, normalized_Ef  × 1.2)   (ef_score_multiplier = 1.2)

Component Weights (must sum to 1.0):
    w_gradient = 0.40   (Gradient content — MIG/Ef, most important for DIC)
    w_contrast = 0.25   (Contrast quality)
    w_entropy  = 0.20   (Information content)
    w_pattern  = 0.10   (Speckle pattern quality)
    w_noise    = 0.05   (Noise resistance)

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

NOTE: Only patterns rated 75%+ are considered suitable for DIC work."""
        else:
            criteria += f"""
Using {spectrum_used.replace('_', ' ').title()} Assessment Criteria:
  • 75-100%: Excellent  (green on map)
  • 60-75%:  Very Good  (cyan on map)
  • 45-60%:  Good       (yellow on map)
  • 30-45%:  Acceptable (orange on map)
  • 15-30%:  Challenging (dark red on map)
  • 0-15%:   Poor       (black on map)

NOTE: Map colors, legend labels, and these thresholds all use the same bands."""

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