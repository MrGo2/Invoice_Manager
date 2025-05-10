"""
OCR Confidence Merger

This module merges results from multiple OCR engines based on confidence scores.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OCRMerger:
    """
    Merges and selects the best results from multiple OCR engines.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the OCR merger.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.threshold = config["ocr"]["confidence"]["threshold"]
        self.strategy = config["ocr"]["confidence"]["merge_strategy"]
        self.last_confidence = 0.0
        
        logger.info(f"Initialized OCR merger with strategy: {self.strategy}")
    
    def merge(self, 
              primary_results: List[Dict], 
              fallback_results: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Merge results from primary and fallback OCR engines.
        
        Args:
            primary_results: Results from the primary OCR engine
            fallback_results: Results from the fallback OCR engine (optional)
            
        Returns:
            Merged OCR results
        """
        # If no fallback results, return primary
        if fallback_results is None or len(fallback_results) == 0:
            self.last_confidence = self._calculate_avg_confidence(primary_results)
            logger.debug(f"No fallback results provided. Using primary results with avg confidence: {self.last_confidence:.2f}")
            return primary_results
        
        if len(primary_results) == 0:
            self.last_confidence = self._calculate_avg_confidence(fallback_results)
            logger.debug(f"No primary results provided. Using fallback results with avg confidence: {self.last_confidence:.2f}")
            return fallback_results
        
        # Calculate confidence metrics
        primary_conf = self._calculate_avg_confidence(primary_results)
        fallback_conf = self._calculate_avg_confidence(fallback_results)
        logger.debug(f"Primary OCR confidence: {primary_conf:.2f}, Fallback OCR confidence: {fallback_conf:.2f}")
        
        # Choose strategy for merging
        if self.strategy == "highest_confidence":
            return self._merge_highest_confidence(primary_results, fallback_results)
        elif self.strategy == "line_by_line":
            return self._merge_line_by_line(primary_results, fallback_results)
        elif self.strategy == "word_by_word":
            return self._merge_word_by_word(primary_results, fallback_results)
        else:
            # Default to highest overall confidence
            if primary_conf >= fallback_conf:
                self.last_confidence = primary_conf
                return primary_results
            else:
                self.last_confidence = fallback_conf
                return fallback_results
    
    def _calculate_avg_confidence(self, results: List[Dict]) -> float:
        """
        Calculate average confidence score for OCR results.
        
        Args:
            results: OCR results
            
        Returns:
            Average confidence score (0.0-1.0)
        """
        if not results:
            return 0.0
        return sum(word.get("conf", 0.0) for word in results) / len(results)
    
    def _merge_highest_confidence(self, 
                                 primary_results: List[Dict], 
                                 fallback_results: List[Dict]) -> List[Dict]:
        """
        Merge by choosing the set with highest overall confidence.
        
        Args:
            primary_results: Results from primary OCR
            fallback_results: Results from fallback OCR
            
        Returns:
            The set of results with highest overall confidence
        """
        primary_conf = self._calculate_avg_confidence(primary_results)
        fallback_conf = self._calculate_avg_confidence(fallback_results)
        
        if primary_conf >= fallback_conf:
            logger.info(f"Using primary OCR results (conf: {primary_conf:.2f} >= {fallback_conf:.2f})")
            self.last_confidence = primary_conf
            return primary_results
        else:
            logger.info(f"Using fallback OCR results (conf: {fallback_conf:.2f} > {primary_conf:.2f})")
            self.last_confidence = fallback_conf
            return fallback_results
    
    def _merge_line_by_line(self, 
                           primary_results: List[Dict], 
                           fallback_results: List[Dict]) -> List[Dict]:
        """
        Merge by comparing results line by line and choosing highest confidence.
        
        Args:
            primary_results: Results from primary OCR
            fallback_results: Results from fallback OCR
            
        Returns:
            Merged results with best lines from each source
        """
        # Group words by lines based on vertical position
        primary_lines = self._group_by_lines(primary_results)
        fallback_lines = self._group_by_lines(fallback_results)
        
        # For each line position, choose the one with higher confidence
        merged_results = []
        total_confidence = 0.0
        line_count = 0
        
        # Process all line positions from both sources
        all_y_positions = sorted(set(list(primary_lines.keys()) + list(fallback_lines.keys())))
        
        for y_pos in all_y_positions:
            # Find closest line in each source
            primary_key = self._find_closest_key(primary_lines.keys(), y_pos)
            fallback_key = self._find_closest_key(fallback_lines.keys(), y_pos)
            
            primary_line = primary_lines.get(primary_key, [])
            fallback_line = fallback_lines.get(fallback_key, [])
            
            # Calculate confidence for each line
            if primary_line:
                primary_conf = sum(w["conf"] for w in primary_line) / len(primary_line)
            else:
                primary_conf = 0.0
                
            if fallback_line:
                fallback_conf = sum(w["conf"] for w in fallback_line) / len(fallback_line)
            else:
                fallback_conf = 0.0
            
            # Choose the line with higher confidence
            if primary_conf >= fallback_conf and primary_line:
                merged_results.extend(primary_line)
                total_confidence += primary_conf
                line_count += 1
            elif fallback_line:
                merged_results.extend(fallback_line)
                total_confidence += fallback_conf
                line_count += 1
        
        # Calculate overall confidence
        self.last_confidence = total_confidence / max(1, line_count)
        logger.info(f"Line-by-line merge completed with {line_count} lines, avg confidence: {self.last_confidence:.2f}")
        
        return merged_results
    
    def _merge_word_by_word(self, 
                           primary_results: List[Dict], 
                           fallback_results: List[Dict]) -> List[Dict]:
        """
        Merge by comparing words with similar positions and choosing highest confidence.
        
        Args:
            primary_results: Results from primary OCR
            fallback_results: Results from fallback OCR
            
        Returns:
            Merged results with best words from each source
        """
        merged_results = []
        used_fallback_indices = set()
        total_confidence = 0.0
        
        # For each word in primary results, find potential matches in fallback
        for primary_word in primary_results:
            primary_box = primary_word.get("box", (0, 0, 0, 0))
            
            # Find potential matching words in fallback (by position overlap)
            matches = []
            for i, fallback_word in enumerate(fallback_results):
                if i in used_fallback_indices:
                    continue
                    
                fallback_box = fallback_word.get("box", (0, 0, 0, 0))
                if self._boxes_overlap(primary_box, fallback_box):
                    matches.append((i, fallback_word))
            
            # If matches found, compare confidence and choose best
            if matches:
                best_match_idx, best_match = max(matches, key=lambda x: x[1].get("conf", 0))
                if best_match.get("conf", 0) > primary_word.get("conf", 0):
                    merged_results.append(best_match)
                    used_fallback_indices.add(best_match_idx)
                    total_confidence += best_match.get("conf", 0)
                else:
                    merged_results.append(primary_word)
                    total_confidence += primary_word.get("conf", 0)
            else:
                merged_results.append(primary_word)
                total_confidence += primary_word.get("conf", 0)
        
        # Add remaining fallback words that weren't matched
        for i, fallback_word in enumerate(fallback_results):
            if i not in used_fallback_indices:
                merged_results.append(fallback_word)
                total_confidence += fallback_word.get("conf", 0)
        
        # Calculate overall confidence
        self.last_confidence = total_confidence / max(1, len(merged_results))
        logger.info(f"Word-by-word merge completed with {len(merged_results)} words, avg confidence: {self.last_confidence:.2f}")
        
        return merged_results
    
    def _group_by_lines(self, results: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Group OCR words by their vertical position (line).
        
        Args:
            results: OCR results
            
        Returns:
            Dictionary mapping y-positions to lists of words
        """
        lines = {}
        
        for word in results:
            # Get the vertical middle of the word
            box = word.get("box", (0, 0, 0, 0))
            if len(box) >= 4:
                y_middle = (box[1] + box[3]) // 2
                
                # Group with a tolerance to account for slight misalignments
                line_key = (y_middle // 10) * 10  # Round to nearest 10px
                
                if line_key not in lines:
                    lines[line_key] = []
                lines[line_key].append(word)
        
        return lines
    
    def _find_closest_key(self, keys, target_key):
        """Find the closest key in a collection of keys to the target key."""
        if not keys:
            return None
        return min(keys, key=lambda k: abs(k - target_key)) if keys else None
    
    def _boxes_overlap(self, box1, box2, threshold=0.3):
        """
        Check if two bounding boxes overlap with a given threshold.
        
        Args:
            box1, box2: Boxes in format (x1, y1, x2, y2)
            threshold: Minimum overlap ratio to consider boxes as overlapping
            
        Returns:
            True if boxes overlap with at least the threshold ratio
        """
        # Ensure boxes have 4 coordinates
        if len(box1) < 4 or len(box2) < 4:
            return False
            
        # Calculate intersection
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])
        
        if x_right < x_left or y_bottom < y_top:
            return False  # No overlap
            
        intersection = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate areas
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        if area1 <= 0 or area2 <= 0:
            return False
            
        # Calculate overlap ratio
        overlap_ratio = intersection / min(area1, area2)
        
        return overlap_ratio >= threshold 