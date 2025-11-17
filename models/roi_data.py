"""
Region of Interest (ROI) data model and operations.

Provides data structure and methods for managing ROI selections including polygon
and rectangular regions. Handles coordinate transformations, mask generation, and
area calculations for focused analysis.

Usage:
    roi = ROIData(coordinates=[(x1,y1), (x2,y2), ...], roi_type='polygon')
    mask = roi.create_mask(image_shape)
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np
import cv2


@dataclass
class ROIData:
    """
    Region of Interest data container.

    Handles both polygon and rectangular ROI types with coordinate management
    and mask generation capabilities.
    """
    coordinates: List[Tuple[float, float]]
    roi_type: str = 'polygon'  # 'polygon' or 'rectangle'

    def __post_init__(self):
        """Validate ROI data after initialization."""
        if not self.coordinates:
            raise ValueError("ROI coordinates cannot be empty")

        if self.roi_type == 'polygon' and len(self.coordinates) < 3:
            raise ValueError("Polygon ROI requires at least 3 points")

        if self.roi_type == 'rectangle' and len(self.coordinates) != 4:
            raise ValueError("Rectangle ROI requires exactly 4 points")

    def create_mask(self, image_shape: Tuple[int, int]) -> np.ndarray:
        """
        Create a binary mask for the ROI.

        Args:
            image_shape: (height, width) of the target image

        Returns:
            Binary mask array (0s and 255s)
        """
        mask = np.zeros(image_shape, dtype=np.uint8)

        if self.roi_type == 'polygon':
            # Convert coordinates to integer array
            pts = np.array(self.coordinates, dtype=np.int32)

            # Clamp coordinates to image bounds
            h, w = image_shape
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

            # Fill polygon
            cv2.fillPoly(mask, [pts], 255)

        elif self.roi_type == 'rectangle':
            # Extract rectangle bounds
            x_coords = [pt[0] for pt in self.coordinates]
            y_coords = [pt[1] for pt in self.coordinates]
            x1, x2 = int(min(x_coords)), int(max(x_coords))
            y1, y2 = int(min(y_coords)), int(max(y_coords))

            # Clamp to image bounds
            h, w = image_shape
            x1, x2 = max(0, x1), min(w - 1, x2)
            y1, y2 = max(0, y1), min(h - 1, y2)

            # Fill rectangle
            mask[y1:y2, x1:x2] = 255

        return mask

    def calculate_area(self) -> float:
        """Calculate the area of the ROI."""
        if self.roi_type == 'polygon':
            # Use shoelace formula for polygon area
            coords = self.coordinates
            area = 0.5 * abs(sum(
                x0 * y1 - x1 * y0
                for ((x0, y0), (x1, y1)) in zip(coords, coords[1:] + [coords[0]])
            ))
            return area

        elif self.roi_type == 'rectangle':
            x_coords = [pt[0] for pt in self.coordinates]
            y_coords = [pt[1] for pt in self.coordinates]
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            return width * height

        return 0.0

    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        """Get bounding box coordinates (x1, y1, x2, y2)."""
        x_coords = [pt[0] for pt in self.coordinates]
        y_coords = [pt[1] for pt in self.coordinates]

        x1, x2 = int(min(x_coords)), int(max(x_coords))
        y1, y2 = int(min(y_coords)), int(max(y_coords))

        return x1, y1, x2, y2

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside the ROI."""
        if self.roi_type == 'polygon':
            # Use OpenCV point in polygon test
            pts = np.array(self.coordinates, dtype=np.float32)
            return cv2.pointPolygonTest(pts, (x, y), False) >= 0

        elif self.roi_type == 'rectangle':
            x1, y1, x2, y2 = self.get_bounding_box()
            return x1 <= x <= x2 and y1 <= y <= y2

        return False

    def get_percentage_of_image(self, image_shape: Tuple[int, int]) -> float:
        """Get ROI area as percentage of total image area."""
        h, w = image_shape
        total_area = h * w
        roi_area = self.calculate_area()

        if total_area == 0:
            return 0.0

        return (roi_area / total_area) * 100

    def has_valid_coordinates(self) -> bool:
        """Check if ROI has valid coordinates."""
        if not self.coordinates:
            return False
        
        if self.roi_type == 'polygon' and len(self.coordinates) < 3:
            return False
            
        if self.roi_type == 'rectangle' and len(self.coordinates) != 4:
            return False
            
        # Check that all coordinates are valid numbers
        try:
            for x, y in self.coordinates:
                if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                    return False
                if not (np.isfinite(x) and np.isfinite(y)):
                    return False
        except (TypeError, ValueError):
            return False
            
        return True

    def transform_coordinates(self, scale_factor: float, offset: Tuple[float, float] = (0, 0)) -> 'ROIData':
        """
        Transform ROI coordinates by scale and offset.

        Args:
            scale_factor: Scaling factor to apply
            offset: (x_offset, y_offset) to apply after scaling

        Returns:
            New ROIData with transformed coordinates
        """
        offset_x, offset_y = offset

        transformed_coords = [
            (x * scale_factor + offset_x, y * scale_factor + offset_y)
            for x, y in self.coordinates
        ]

        return ROIData(
            coordinates=transformed_coords,
            roi_type=self.roi_type
        )

    def to_canvas_coordinates(self, display_scale: float, image_offset: Tuple[float, float]) -> List[
        Tuple[float, float]]:
        """
        Convert image coordinates to canvas coordinates for display.

        Args:
            display_scale: Scale factor from image to display
            image_offset: (x_offset, y_offset) of image on canvas

        Returns:
            List of canvas coordinates
        """
        offset_x, offset_y = image_offset

        return [
            (x * display_scale + offset_x, y * display_scale + offset_y)
            for x, y in self.coordinates
        ]

    @classmethod
    def from_canvas_coordinates(
            cls,
            canvas_coords: List[Tuple[float, float]],
            display_scale: float,
            image_offset: Tuple[float, float]
    ) -> 'ROIData':
        """
        Create ROIData from canvas coordinates.

        Args:
            canvas_coords: List of (x, y) coordinates in canvas space
            display_scale: Scale factor from image to display
            image_offset: (x_offset, y_offset) of image on canvas

        Returns:
            ROIData with image coordinates
        """
        offset_x, offset_y = image_offset

        image_coords = [
            ((x - offset_x) / display_scale, (y - offset_y) / display_scale)
            for x, y in canvas_coords
        ]

        return cls(coordinates=image_coords)

    def __str__(self) -> str:
        """String representation of ROI."""
        area = self.calculate_area()
        point_count = len(self.coordinates)

        return f"ROI({self.roi_type}): {point_count} points, {area:.0f} pixels²"