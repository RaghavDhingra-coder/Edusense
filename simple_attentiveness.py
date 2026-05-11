"""
Simplified Attentiveness Analyzer using basic heuristics
Works with cropped face images from tracking system
"""

import os
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict
import json
import logging
from tqdm import tqdm
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleAttentivenessAnalyzer:
    """
    Simplified attentiveness analyzer using image-based heuristics
    Designed for cropped face images from classroom tracking
    """
    
    def __init__(self, students_dir='students', focus_threshold=0.70):
        """
        Initialize analyzer
        
        Args:
            students_dir: Directory containing student folders
            focus_threshold: Threshold for focused classification (0-1)
        """
        self.students_dir = students_dir
        self.focus_threshold = focus_threshold
        
        logger.info("=" * 60)
        logger.info("🔧 Initializing Simple Attentiveness Analyzer")
        logger.info("=" * 60)
        logger.info(f"Students dir: {students_dir}")
        logger.info(f"Focus threshold: {focus_threshold * 100}%")
        logger.info("=" * 60)
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze single image - assume focused by default for cropped faces
        
        For cropped face images from tracking:
        - If face is visible and clear → Focused
        - If image is blurry or dark → Not Focused
        
        Args:
            image_path: Path to image
            
        Returns:
            Dict with is_focused and quality score
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {'is_focused': False, 'quality': 0.0}
            
            # Calculate image quality metrics
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness = min(1.0, laplacian_var / 500.0)
            
            # Brightness
            brightness = np.mean(gray) / 255.0
            brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Prefer mid-range
            
            # Overall quality
            quality = (sharpness * 0.7 + brightness_score * 0.3)
            
            # Assume focused if quality is reasonable
            # (Face was detected and tracked, so student is present)
            # Lower threshold for cropped faces
            is_focused = quality > 0.15
            
            return {
                'is_focused': is_focused,
                'quality': quality,
                'sharpness': sharpness,
                'brightness': brightness
            }
        except Exception as e:
            logger.debug(f"Failed to analyze {image_path}: {e}")
            return {'is_focused': False, 'quality': 0.0}
    
    def analyze_student_folder(self, student_folder: str) -> Optional[Dict]:
        """
        Analyze all images in student folder
        
        Args:
            student_folder: Path to student folder
            
        Returns:
            Analytics dictionary
        """
        student_id = os.path.basename(student_folder)
        
        logger.info(f"📁 Scanning folder: {student_folder}")
        
        # Get image files
        image_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = [
            os.path.join(student_folder, f)
            for f in os.listdir(student_folder)
            if os.path.splitext(f)[1].lower() in image_extensions
        ]
        
        if len(image_files) == 0:
            logger.warning(f"⚠️  No images in {student_folder}")
            return None
        
        logger.info(f"✅ Found {len(image_files)} images")
        
        # Analyze each image
        focused_frames = 0
        unfocused_frames = 0
        quality_scores = []
        
        for img_file in image_files:
            result = self.analyze_image(img_file)
            
            if result['is_focused']:
                focused_frames += 1
            else:
                unfocused_frames += 1
            
            quality_scores.append(result['quality'])
        
        total_frames = len(image_files)
        attentiveness_percentage = (focused_frames / total_frames) * 100
        
        # Determine status
        if attentiveness_percentage >= (self.focus_threshold * 100):
            status = "Focused"
            status_color = "success"
        else:
            status = "Not Focused"
            status_color = "danger"
        
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        
        logger.info(f"   Focused: {focused_frames}/{total_frames}")
        logger.info(f"   Attentiveness: {attentiveness_percentage:.1f}%")
        logger.info(f"   Status: {status}")
        logger.info(f"   Avg quality: {avg_quality:.2f}")
        
        sample_image = image_files[len(image_files) // 2] if image_files else None
        
        return {
            'student_id': student_id,
            'status': status,
            'status_color': status_color,
            'attentiveness_percentage': round(attentiveness_percentage, 1),
            'engagement_percentage': round(attentiveness_percentage, 1),
            'engagement_score': round(attentiveness_percentage, 1),
            'images_analyzed': total_frames,
            'valid_frames': total_frames,
            'focused_frames': focused_frames,
            'unfocused_frames': unfocused_frames,
            'focused_count': focused_frames,
            'unfocused_count': unfocused_frames,
            'avg_quality': round(avg_quality, 3),
            'sample_image': sample_image,
            'most_common_state': status,
            'prediction_breakdown': {
                'Focused': {
                    'count': focused_frames,
                    'percentage': round((focused_frames / total_frames) * 100, 1)
                },
                'Not Focused': {
                    'count': unfocused_frames,
                    'percentage': round((unfocused_frames / total_frames) * 100, 1)
                }
            }
        }
    
    def analyze_all_students(self, progress_callback=None) -> List[Dict]:
        """Analyze all student folders"""
        logger.info("=" * 60)
        logger.info("📂 Checking students directory...")
        
        if not os.path.exists(self.students_dir):
            logger.error(f"❌ Students directory not found: {self.students_dir}")
            return []
        
        student_folders = [
            os.path.join(self.students_dir, d)
            for d in os.listdir(self.students_dir)
            if os.path.isdir(os.path.join(self.students_dir, d))
            and d.startswith('student_')
        ]
        
        if len(student_folders) == 0:
            logger.warning("⚠️  No student folders found")
            return []
        
        logger.info(f"✅ Found {len(student_folders)} student folders")
        
        all_analytics = []
        
        for idx, folder in enumerate(tqdm(student_folders, desc="Analyzing students")):
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 Analyzing {os.path.basename(folder)} ({idx+1}/{len(student_folders)})")
            logger.info(f"{'='*60}")
            
            try:
                analytics = self.analyze_student_folder(folder)
                if analytics:
                    all_analytics.append(analytics)
            except Exception as e:
                logger.error(f"❌ Error: {e}")
        
        logger.info(f"\n✅ Analyzed {len(all_analytics)}/{len(student_folders)} students\n")
        return all_analytics
    
    def compute_classroom_summary(self, all_analytics: List[Dict]) -> Dict:
        """Compute classroom summary"""
        if not all_analytics:
            return {
                'total_students': 0,
                'focused_students': 0,
                'moderately_focused_students': 0,
                'unfocused_students': 0,
                'average_attentiveness': 0,
                'average_engagement': 0,
                'total_images_analyzed': 0
            }
        
        status_counts = defaultdict(int)
        for a in all_analytics:
            status_counts[a['status']] += 1
        
        avg_attentiveness = sum(a['attentiveness_percentage'] for a in all_analytics) / len(all_analytics)
        total_images = sum(a['images_analyzed'] for a in all_analytics)
        
        return {
            'total_students': len(all_analytics),
            'focused_students': status_counts['Focused'],
            'moderately_focused_students': 0,
            'unfocused_students': status_counts['Not Focused'],
            'average_attentiveness': round(avg_attentiveness, 1),
            'average_engagement': round(avg_attentiveness, 1),
            'total_images_analyzed': total_images,
            'focused_percentage': round((status_counts['Focused'] / len(all_analytics)) * 100, 1),
            'unfocused_percentage': round((status_counts['Not Focused'] / len(all_analytics)) * 100, 1)
        }
    
    def generate_report(self, output_file='attentiveness_report.json') -> Dict:
        """Generate report"""
        logger.info("Generating report...")
        
        all_analytics = self.analyze_all_students()
        summary = self.compute_classroom_summary(all_analytics)
        
        report = {
            'summary': summary,
            'students': all_analytics,
            'analysis_type': 'simple_attentiveness'
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_file}")
        return report
