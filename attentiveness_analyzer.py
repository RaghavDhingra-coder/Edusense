"""
Attentiveness Analyzer for Classroom Students
Replaces emotion-based analytics with head pose-based attentiveness detection
"""

import os
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict, deque
import json
import logging
from tqdm import tqdm
from typing import Dict, List, Optional

from head_pose_estimator import HeadPoseEstimator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AttentivenessAnalyzer:
    """
    Analyzes student attentiveness from collected face images using head pose estimation
    """
    
    def __init__(self, 
                 students_dir='students',
                 focus_threshold=0.60,
                 batch_size=1):
        """
        Initialize attentiveness analyzer
        
        Args:
            students_dir: Directory containing student folders
            focus_threshold: Percentage threshold for focused classification (0-1)
            batch_size: Number of images to process at once (1 for head pose)
        """
        self.students_dir = students_dir
        self.focus_threshold = focus_threshold
        self.batch_size = batch_size
        
        # Initialize head pose estimator
        logger.info("=" * 60)
        logger.info("🔧 Initializing Attentiveness Analyzer")
        logger.info("=" * 60)
        logger.info(f"Students dir: {students_dir}")
        logger.info(f"Focus threshold: {focus_threshold * 100}%")
        
        self.pose_estimator = HeadPoseEstimator()
        logger.info("✅ Head pose estimator initialized")
        logger.info("=" * 60)
    
    def analyze_image(self, image_path: str) -> Optional[Dict]:
        """
        Analyze single image for attentiveness
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with pose data or None if failed
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            
            if image is None:
                logger.warning(f"Failed to load image: {image_path}")
                return None
            
            # Get head pose
            pose_data = self.pose_estimator.get_head_pose(image)
            
            return pose_data
        
        except Exception as e:
            logger.warning(f"Failed to analyze {image_path}: {str(e)}")
            return None
    
    def analyze_student_folder(self, student_folder: str) -> Optional[Dict]:
        """
        Analyze all images in a student folder
        
        Args:
            student_folder: Path to student folder
            
        Returns:
            Dictionary with analysis results
        """
        student_id = os.path.basename(student_folder)
        
        logger.info(f"📁 Scanning folder: {student_folder}")
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = [
            os.path.join(student_folder, f)
            for f in os.listdir(student_folder)
            if os.path.splitext(f)[1].lower() in image_extensions
        ]
        
        if len(image_files) == 0:
            logger.warning(f"⚠️  No images found in {student_folder}")
            return None
        
        logger.info(f"✅ Found {len(image_files)} images")
        
        # Analyze each image
        focused_frames = 0
        unfocused_frames = 0
        valid_frames = 0
        
        yaw_values = []
        pitch_values = []
        roll_values = []
        eye_closure_count = 0
        
        logger.info(f"🔄 Analyzing {len(image_files)} images...")
        
        for img_file in image_files:
            pose_data = self.analyze_image(img_file)
            
            if pose_data is not None:
                valid_frames += 1
                
                if pose_data['is_focused']:
                    focused_frames += 1
                else:
                    unfocused_frames += 1
                
                yaw_values.append(pose_data['yaw'])
                pitch_values.append(pose_data['pitch'])
                roll_values.append(pose_data['roll'])
                
                if pose_data['eyes_closed']:
                    eye_closure_count += 1
        
        if valid_frames == 0:
            logger.warning(f"⚠️  No valid frames for {student_id}")
            return None
        
        # Calculate attentiveness percentage
        attentiveness_percentage = (focused_frames / valid_frames) * 100
        
        # Determine final status
        if attentiveness_percentage >= (self.focus_threshold * 100):
            status = "Focused"
            status_color = "success"
        else:
            status = "Not Focused"
            status_color = "danger"
        
        # Calculate statistics
        avg_yaw = np.mean(yaw_values) if yaw_values else 0
        avg_pitch = np.mean(pitch_values) if pitch_values else 0
        avg_roll = np.mean(roll_values) if roll_values else 0
        
        yaw_std = np.std(yaw_values) if yaw_values else 0
        pitch_std = np.std(pitch_values) if pitch_values else 0
        
        # Detect behavioral patterns
        looking_away_frequency = unfocused_frames / valid_frames if valid_frames > 0 else 0
        eye_closure_rate = eye_closure_count / valid_frames if valid_frames > 0 else 0
        head_movement_stability = 1.0 / (1.0 + yaw_std + pitch_std)  # Higher = more stable
        
        # Select representative image (middle of sequence)
        sample_image = image_files[len(image_files) // 2] if image_files else None
        
        # Debug logging
        logger.info(f"   Focused frames: {focused_frames}/{valid_frames}")
        logger.info(f"   Unfocused frames: {unfocused_frames}/{valid_frames}")
        logger.info(f"   Attentiveness: {attentiveness_percentage:.1f}%")
        logger.info(f"   Status: {status}")
        logger.info(f"   Avg head pose: yaw={avg_yaw:.1f}°, pitch={avg_pitch:.1f}°, roll={avg_roll:.1f}°")
        
        # Compile analytics
        analytics = {
            'student_id': student_id,
            'status': status,
            'status_color': status_color,
            'attentiveness_percentage': round(attentiveness_percentage, 1),
            'engagement_percentage': round(attentiveness_percentage, 1),  # Alias for compatibility
            'engagement_score': round(attentiveness_percentage, 1),  # Alias for compatibility
            'images_analyzed': len(image_files),
            'valid_frames': valid_frames,
            'focused_frames': focused_frames,
            'unfocused_frames': unfocused_frames,
            'focused_count': focused_frames,  # Alias for compatibility
            'unfocused_count': unfocused_frames,  # Alias for compatibility
            'head_pose_stats': {
                'avg_yaw': round(avg_yaw, 2),
                'avg_pitch': round(avg_pitch, 2),
                'avg_roll': round(avg_roll, 2),
                'yaw_std': round(yaw_std, 2),
                'pitch_std': round(pitch_std, 2)
            },
            'behavioral_metrics': {
                'looking_away_frequency': round(looking_away_frequency, 3),
                'eye_closure_rate': round(eye_closure_rate, 3),
                'head_movement_stability': round(head_movement_stability, 3)
            },
            'sample_image': sample_image,
            'most_common_state': status,  # For compatibility
            'prediction_breakdown': {  # For compatibility with frontend
                'Focused': {
                    'count': focused_frames,
                    'percentage': round((focused_frames / valid_frames) * 100, 1) if valid_frames > 0 else 0
                },
                'Not Focused': {
                    'count': unfocused_frames,
                    'percentage': round((unfocused_frames / valid_frames) * 100, 1) if valid_frames > 0 else 0
                }
            }
        }
        
        return analytics
    
    def analyze_all_students(self, progress_callback=None) -> List[Dict]:
        """
        Analyze all student folders
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of analytics dictionaries
        """
        logger.info("=" * 60)
        logger.info("📂 Checking students directory...")
        
        if not os.path.exists(self.students_dir):
            logger.error(f"❌ Students directory not found: {self.students_dir}")
            logger.info("Creating students directory...")
            os.makedirs(self.students_dir, exist_ok=True)
            return []
        
        logger.info(f"✅ Students directory exists: {self.students_dir}")
        
        # Get all student folders
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
        
        # Analyze each student
        all_analytics = []
        
        for idx, folder in enumerate(tqdm(student_folders, desc="Analyzing students")):
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 Analyzing {os.path.basename(folder)} ({idx+1}/{len(student_folders)})")
            logger.info(f"{'='*60}")
            
            try:
                analytics = self.analyze_student_folder(folder)
                
                if analytics is not None:
                    all_analytics.append(analytics)
                    logger.info(f"✅ {analytics['student_id']}: {analytics['attentiveness_percentage']}% ({analytics['status']})")
                else:
                    logger.warning(f"⚠️  No valid data for {os.path.basename(folder)}")
            except Exception as e:
                logger.error(f"❌ Error analyzing {os.path.basename(folder)}: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Progress callback
            if progress_callback:
                progress = ((idx + 1) / len(student_folders)) * 100
                progress_callback(progress, analytics if analytics else None)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Successfully analyzed {len(all_analytics)}/{len(student_folders)} students")
        logger.info(f"{'='*60}\n")
        
        return all_analytics
    
    def compute_classroom_summary(self, all_analytics: List[Dict]) -> Dict:
        """
        Compute overall classroom attentiveness summary
        
        Args:
            all_analytics: List of student analytics
            
        Returns:
            Dictionary with classroom summary
        """
        if len(all_analytics) == 0:
            return {
                'total_students': 0,
                'focused_students': 0,
                'moderately_focused_students': 0,
                'unfocused_students': 0,
                'average_attentiveness': 0,
                'average_engagement': 0,  # Alias
                'total_images_analyzed': 0
            }
        
        # Count by status
        status_counts = defaultdict(int)
        for analytics in all_analytics:
            status_counts[analytics['status']] += 1
        
        # Calculate averages
        avg_attentiveness = sum(a['attentiveness_percentage'] for a in all_analytics) / len(all_analytics)
        total_images = sum(a['images_analyzed'] for a in all_analytics)
        
        # Aggregate behavioral metrics
        avg_looking_away = np.mean([a['behavioral_metrics']['looking_away_frequency'] for a in all_analytics])
        avg_eye_closure = np.mean([a['behavioral_metrics']['eye_closure_rate'] for a in all_analytics])
        avg_stability = np.mean([a['behavioral_metrics']['head_movement_stability'] for a in all_analytics])
        
        summary = {
            'total_students': len(all_analytics),
            'focused_students': status_counts['Focused'],
            'moderately_focused_students': 0,  # Not used in binary classification
            'unfocused_students': status_counts['Not Focused'],
            'average_attentiveness': round(avg_attentiveness, 1),
            'average_engagement': round(avg_attentiveness, 1),  # Alias for compatibility
            'total_images_analyzed': total_images,
            'focused_percentage': round((status_counts['Focused'] / len(all_analytics)) * 100, 1) if len(all_analytics) > 0 else 0,
            'unfocused_percentage': round((status_counts['Not Focused'] / len(all_analytics)) * 100, 1) if len(all_analytics) > 0 else 0,
            'classroom_behavioral_metrics': {
                'avg_looking_away_frequency': round(avg_looking_away, 3),
                'avg_eye_closure_rate': round(avg_eye_closure, 3),
                'avg_head_stability': round(avg_stability, 3)
            }
        }
        
        return summary
    
    def generate_report(self, output_file='attentiveness_report.json') -> Dict:
        """
        Generate complete attentiveness report
        
        Args:
            output_file: Path to save JSON report
            
        Returns:
            Dictionary with complete report
        """
        logger.info("Generating attentiveness report...")
        
        # Analyze all students
        all_analytics = self.analyze_all_students()
        
        # Compute classroom summary
        summary = self.compute_classroom_summary(all_analytics)
        
        # Compile report
        report = {
            'summary': summary,
            'students': all_analytics,
            'analysis_type': 'head_pose_attentiveness',
            'timestamp': str(Path(output_file).stat().st_mtime) if os.path.exists(output_file) else None
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_file}")
        
        return report


def main():
    """
    Main function for standalone execution
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Student Attentiveness Analytics")
    parser.add_argument('--students-dir', default='students', help='Students directory')
    parser.add_argument('--output', default='attentiveness_report.json', help='Output file')
    parser.add_argument('--threshold', type=float, default=0.60, help='Focus threshold (0-1)')
    
    args = parser.parse_args()
    
    # Create analytics engine
    analyzer = AttentivenessAnalyzer(
        students_dir=args.students_dir,
        focus_threshold=args.threshold
    )
    
    # Generate report
    report = analyzer.generate_report(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 CLASSROOM ATTENTIVENESS SUMMARY")
    print("="*60)
    print(f"Total Students: {report['summary']['total_students']}")
    print(f"Focused: {report['summary']['focused_students']}")
    print(f"Not Focused: {report['summary']['unfocused_students']}")
    print(f"Average Attentiveness: {report['summary']['average_attentiveness']}%")
    print(f"Total Images Analyzed: {report['summary']['total_images_analyzed']}")
    print("="*60)


if __name__ == "__main__":
    main()
