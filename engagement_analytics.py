"""
Student-wise Engagement Analytics Engine
Analyzes all images in student folders and computes engagement metrics
"""

import os
import cv2
import torch
import numpy as np
from pathlib import Path
from PIL import Image
import torchvision.transforms as transforms
from collections import defaultdict
import json
import logging
from tqdm import tqdm

from engagement_model import (
    load_engagement_model, 
    CLASS_NAMES, 
    CLASS_DISPLAY_NAMES,
    CLASS_WEIGHTS
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EngagementAnalytics:
    """
    Analyzes student engagement from collected face images
    """
    
    def __init__(self, 
                 model_path='best_model_state.bin',
                 students_dir='students',
                 device='cpu',
                 batch_size=32):
        """
        Initialize engagement analytics engine
        
        Args:
            model_path: Path to trained model
            students_dir: Directory containing student folders
            device: Device for inference ('cpu' or 'cuda')
            batch_size: Batch size for inference
        """
        self.model_path = model_path
        self.students_dir = students_dir
        self.device = device
        self.batch_size = batch_size
        
        # Load model
        logger.info("=" * 60)
        logger.info(f"🔧 Initializing Engagement Analytics Engine")
        logger.info("=" * 60)
        logger.info(f"Model path: {model_path}")
        logger.info(f"Students dir: {students_dir}")
        logger.info(f"Device: {device}")
        logger.info(f"Batch size: {batch_size}")
        
        if not os.path.exists(model_path):
            logger.error(f"❌ Model file not found: {model_path}")
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        logger.info(f"✅ Model file exists: {model_path}")
        logger.info(f"Loading engagement model...")
        
        try:
            self.model = load_engagement_model(model_path, device)
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            raise
        
        # Image preprocessing (matches training pipeline - grayscale)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.Grayscale(num_output_channels=1),  # Convert to grayscale
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.5],  # Single channel
                std=[0.5]
            )
        ])
        
        logger.info("=" * 60)
        logger.info("✅ Engine initialized successfully")
        logger.info("=" * 60)
    
    def preprocess_image(self, image_path):
        """
        Preprocess image for model inference
        
        Args:
            image_path: Path to image file
            
        Returns:
            Preprocessed tensor or None if error
        """
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Apply transforms
            tensor = self.transform(image)
            
            return tensor
        
        except Exception as e:
            logger.warning(f"Failed to preprocess {image_path}: {str(e)}")
            return None
    
    def predict_batch(self, image_tensors):
        """
        Run batch inference
        
        Args:
            image_tensors: List of preprocessed tensors
            
        Returns:
            List of predicted class indices
        """
        if len(image_tensors) == 0:
            return []
        
        # Stack tensors into batch
        batch = torch.stack(image_tensors).to(self.device)
        
        # Run inference
        with torch.no_grad():
            outputs = self.model(batch)
            _, predictions = torch.max(outputs, 1)
        
        pred_list = predictions.cpu().numpy().tolist()
        
        # Debug: log prediction distribution for first batch
        if len(pred_list) > 0:
            from collections import Counter
            pred_counts = Counter(pred_list)
            logger.debug(f"    Batch predictions: {dict(pred_counts)}")
        
        return pred_list
    
    def analyze_student_folder(self, student_folder):
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
        
        # Preprocess images in batches
        all_predictions = []
        valid_images = []
        
        logger.info(f"🔄 Processing {len(image_files)} images in batches of {self.batch_size}...")
        
        for i in range(0, len(image_files), self.batch_size):
            batch_files = image_files[i:i + self.batch_size]
            batch_tensors = []
            batch_valid_files = []
            
            for img_file in batch_files:
                tensor = self.preprocess_image(img_file)
                if tensor is not None:
                    batch_tensors.append(tensor)
                    batch_valid_files.append(img_file)
            
            # Run batch inference
            if len(batch_tensors) > 0:
                predictions = self.predict_batch(batch_tensors)
                all_predictions.extend(predictions)
                valid_images.extend(batch_valid_files)
                logger.info(f"  Batch {i//self.batch_size + 1}: {len(predictions)} predictions")
        
        if len(all_predictions) == 0:
            logger.warning(f"⚠️  No valid predictions for {student_id}")
            return None
        
        logger.info(f"✅ Total predictions: {len(all_predictions)}")
        
        # Log prediction distribution
        from collections import Counter
        pred_counts = Counter(all_predictions)
        logger.info(f"   Prediction distribution:")
        for class_idx, count in sorted(pred_counts.items()):
            logger.info(f"     [{class_idx}] {CLASS_DISPLAY_NAMES[class_idx]}: {count}")
        
        # Compute analytics
        analytics = self._compute_analytics(
            student_id, 
            all_predictions, 
            valid_images
        )
        
        return analytics
    
    def _compute_analytics(self, student_id, predictions, image_files):
        """
        Compute engagement analytics from predictions
        
        Args:
            student_id: Student identifier
            predictions: List of predicted class indices
            image_files: List of image file paths
            
        Returns:
            Dictionary with analytics
        """
        # Count predictions
        prediction_counts = defaultdict(int)
        for pred in predictions:
            prediction_counts[pred] += 1
        
        # Define focused vs unfocused classes
        # Focused: Engaged (0), Confused (1), Frustrated (2)
        # Unfocused: Looking Away (3), Bored (4), Drowsy (5)
        FOCUSED_CLASSES = {0, 1, 2}
        UNFOCUSED_CLASSES = {3, 4, 5}
        
        # Count focused vs unfocused
        focused_count = sum(prediction_counts[cls] for cls in FOCUSED_CLASSES)
        unfocused_count = sum(prediction_counts[cls] for cls in UNFOCUSED_CLASSES)
        total_images = len(predictions)
        
        # Calculate engagement percentage
        engagement_percentage = (focused_count / total_images * 100) if total_images > 0 else 0
        
        # Determine status based on engagement percentage
        if engagement_percentage >= 75:
            status = "Focused"
            status_color = "success"
        elif engagement_percentage >= 40:
            status = "Moderately Focused"
            status_color = "warning"
        else:
            status = "Unfocused"
            status_color = "danger"
        
        # Debug logging
        logger.info(f"   Focused images: {focused_count}/{total_images}")
        logger.info(f"   Unfocused images: {unfocused_count}/{total_images}")
        logger.info(f"   Engagement: {engagement_percentage:.1f}%")
        logger.info(f"   Status: {status}")
        
        # Calculate percentages for each class
        prediction_breakdown = {
            CLASS_DISPLAY_NAMES[class_idx]: {
                'count': prediction_counts[class_idx],
                'percentage': round((prediction_counts[class_idx] / total_images) * 100, 1)
            }
            for class_idx in range(6)
        }
        
        # Find most common state
        most_common_class = max(prediction_counts.items(), key=lambda x: x[1])[0]
        most_common_state = CLASS_DISPLAY_NAMES[most_common_class]
        
        # Select representative image (middle of sequence)
        sample_image = image_files[len(image_files) // 2] if image_files else None
        
        # Compile analytics
        analytics = {
            'student_id': student_id,
            'status': status,
            'status_color': status_color,
            'engagement_percentage': round(engagement_percentage, 1),
            'engagement_score': round(engagement_percentage, 1),  # Keep for backward compatibility
            'images_analyzed': total_images,
            'focused_count': focused_count,
            'unfocused_count': unfocused_count,
            'prediction_breakdown': prediction_breakdown,
            'most_common_state': most_common_state,
            'sample_image': sample_image,
            'detailed_counts': {
                CLASS_DISPLAY_NAMES[k]: v 
                for k, v in prediction_counts.items()
            }
        }
        
        return analytics
    
    def analyze_all_students(self, progress_callback=None):
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
                    logger.info(f"✅ {analytics['student_id']}: {analytics['engagement_score']}% ({analytics['status']})")
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
    
    def compute_classroom_summary(self, all_analytics):
        """
        Compute overall classroom engagement summary
        
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
                'average_engagement': 0,
                'total_images_analyzed': 0
            }
        
        # Count by status
        status_counts = defaultdict(int)
        for analytics in all_analytics:
            status_counts[analytics['status']] += 1
        
        # Calculate averages
        avg_engagement = sum(a['engagement_percentage'] for a in all_analytics) / len(all_analytics)
        total_images = sum(a['images_analyzed'] for a in all_analytics)
        
        # Aggregate prediction breakdown
        aggregated_breakdown = defaultdict(lambda: {'count': 0, 'percentage': 0})
        for analytics in all_analytics:
            for state, data in analytics['prediction_breakdown'].items():
                aggregated_breakdown[state]['count'] += data['count']
        
        # Calculate percentages
        for state in aggregated_breakdown:
            aggregated_breakdown[state]['percentage'] = round(
                (aggregated_breakdown[state]['count'] / total_images) * 100, 1
            ) if total_images > 0 else 0
        
        summary = {
            'total_students': len(all_analytics),
            'focused_students': status_counts['Focused'],
            'moderately_focused_students': status_counts['Moderately Focused'],
            'unfocused_students': status_counts['Unfocused'],
            'average_engagement': round(avg_engagement, 1),
            'total_images_analyzed': total_images,
            'classroom_breakdown': dict(aggregated_breakdown),
            'focused_percentage': round((status_counts['Focused'] / len(all_analytics)) * 100, 1) if len(all_analytics) > 0 else 0,
            'unfocused_percentage': round((status_counts['Unfocused'] / len(all_analytics)) * 100, 1) if len(all_analytics) > 0 else 0
        }
        
        return summary
    
    def generate_report(self, output_file='engagement_report.json'):
        """
        Generate complete engagement report
        
        Args:
            output_file: Path to save JSON report
            
        Returns:
            Dictionary with complete report
        """
        logger.info("Generating engagement report...")
        
        # Analyze all students
        all_analytics = self.analyze_all_students()
        
        # Compute classroom summary
        summary = self.compute_classroom_summary(all_analytics)
        
        # Compile report
        report = {
            'summary': summary,
            'students': all_analytics,
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
    
    parser = argparse.ArgumentParser(description="Student Engagement Analytics")
    parser.add_argument('--students-dir', default='students', help='Students directory')
    parser.add_argument('--model-path', default='best_model_state.bin', help='Model path')
    parser.add_argument('--output', default='engagement_report.json', help='Output file')
    parser.add_argument('--device', default='cpu', choices=['cpu', 'cuda'], help='Device')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    
    args = parser.parse_args()
    
    # Create analytics engine
    analytics = EngagementAnalytics(
        model_path=args.model_path,
        students_dir=args.students_dir,
        device=args.device,
        batch_size=args.batch_size
    )
    
    # Generate report
    report = analytics.generate_report(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 CLASSROOM ENGAGEMENT SUMMARY")
    print("="*60)
    print(f"Total Students: {report['summary']['total_students']}")
    print(f"Focused: {report['summary']['focused_students']}")
    print(f"Neutral: {report['summary']['neutral_students']}")
    print(f"Distracted: {report['summary']['distracted_students']}")
    print(f"Average Engagement: {report['summary']['average_engagement']}%")
    print(f"Total Images Analyzed: {report['summary']['total_images_analyzed']}")
    print("="*60)


if __name__ == "__main__":
    main()
