"""
Robust Main Application for Classroom Face Detection and Tracking
Uses improved ReID system with:
- Temporal consistency
- Hybrid matching
- Quality filtering
- Embedding smoothing
"""

import cv2
import sys
import argparse
from pathlib import Path
import time

from face_detector import FaceDetector
from image_manager import ImageManager
from video_processor import VideoProcessor
from face_reid_robust import RobustFaceReID
import config_robust as config


class RobustClassroomTrackingSystem:
    """
    Robust classroom tracking system with improved ReID
    """
    
    def __init__(self, video_source=0, output_dir=None, preset='balanced'):
        """
        Initialize the robust tracking system
        
        Args:
            video_source: Video source (0 for webcam, or path to video file)
            output_dir: Directory for saving student images
            preset: Configuration preset ('fast', 'balanced', 'accurate', 'hackathon')
        """
        self.video_source = video_source
        self.output_dir = output_dir or config.OUTPUT_DIR
        
        # Apply preset
        config.apply_preset(preset)
        
        # Initialize components
        print("=" * 60)
        print("🎓 ROBUST CLASSROOM TRACKING SYSTEM")
        print("=" * 60)
        print(f"📋 Preset: {preset}")
        
        self.detector = None
        self.image_manager = None
        self.video_processor = None
        self.reid_system = None
        
        # Frame counter
        self.frame_number = 0
        self.processed_frames = 0
        
        # Track management
        self.active_tracks = set()
        
        # Performance tracking
        self.processing_times = []
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all system components"""
        try:
            print("\n📦 Initializing components...")
            
            # Face detector
            self.detector = FaceDetector()
            
            # Image manager
            self.image_manager = ImageManager(self.output_dir)
            
            # Video processor
            self.video_processor = VideoProcessor(self.video_source)
            
            # Robust ReID system
            if config.ENABLE_REID:
                print("\n🔄 Initializing Robust ReID system...")
                self.reid_system = RobustFaceReID(
                    similarity_threshold=config.REID_SIMILARITY_THRESHOLD,
                    spatial_weight=config.REID_SPATIAL_WEIGHT,
                    temporal_weight=config.REID_TEMPORAL_WEIGHT,
                    embedding_weight=config.REID_EMBEDDING_WEIGHT,
                    max_embeddings_per_student=config.REID_MAX_EMBEDDINGS_PER_STUDENT,
                    cooldown_period=config.REID_COOLDOWN_PERIOD,
                    quality_threshold=config.REID_QUALITY_THRESHOLD
                )
            else:
                print("\n⚠️  ReID disabled")
                self.reid_system = None
            
            print("✅ All components initialized\n")
            
        except Exception as e:
            print(f"❌ Initialization failed: {str(e)}")
            sys.exit(1)
    
    def process_frame(self, frame):
        """
        Process a single frame with robust ReID
        
        Args:
            frame: Input frame
            
        Returns:
            Annotated frame
        """
        self.frame_number += 1
        current_time = time.time()
        
        # Skip frames for performance
        if config.SKIP_FRAMES > 1 and self.frame_number % config.SKIP_FRAMES != 0:
            # Just draw existing info
            annotated_frame = frame.copy()
            annotated_frame = self.video_processor.draw_fps(annotated_frame)
            stats = self.image_manager.get_statistics()
            annotated_frame = self.video_processor.draw_info(
                annotated_frame,
                stats['total_students'],
                stats['total_images']
            )
            return annotated_frame
        
        self.processed_frames += 1
        process_start = time.time()
        
        # Debug mode
        debug = config.SHOW_DEBUG_OVERLAY and self.frame_number <= config.DEBUG_OVERLAY_DURATION
        
        if debug and self.frame_number % 30 == 1:
            print(f"\n{'='*60}")
            print(f"🔍 FRAME {self.frame_number} (Processed: {self.processed_frames})")
            print(f"{'='*60}")
        
        # Detect and track faces
        detections = self.detector.track_faces(frame, self.frame_number, debug=False)
        
        # Track current frame's track IDs
        current_tracks = set()
        
        # Process each detection with Robust ReID
        reid_detections = []
        stats_counters = {
            'validation_failed': 0,
            'crop_failed': 0,
            'quality_rejected': 0,
            'new_students': 0,
            'matched_students': 0,
            'recovered_tracks': 0
        }
        
        for detection in detections:
            x1, y1, x2, y2, track_id, confidence, track_age = detection
            current_tracks.add(track_id)
            
            # Validate detection
            bbox = (x1, y1, x2, y2)
            if not self.detector.is_valid_face_detection(bbox, confidence):
                stats_counters['validation_failed'] += 1
                continue
            
            # Crop face
            face_crop = self.image_manager.crop_face(frame, bbox)
            
            if face_crop is None:
                stats_counters['crop_failed'] += 1
                continue
            
            # Apply Robust ReID
            if self.reid_system and config.ENABLE_REID:
                student_id, is_new, details = self.reid_system.register_or_match_face(
                    track_id, face_crop, bbox, confidence, current_time
                )
                
                # Track statistics
                if is_new:
                    stats_counters['new_students'] += 1
                elif 'recovered' in details:
                    stats_counters['recovered_tracks'] += 1
                elif 'rejected' in details:
                    stats_counters['quality_rejected'] += 1
                else:
                    stats_counters['matched_students'] += 1
                
                # Log significant events
                if debug and 'new' in details:
                    quality = details.get('quality', 0)
                    print(f"✨ New: Student {student_id} (Track {track_id}, Q:{quality:.1f})")
                elif debug and 'combined_score' in details:
                    score = details['combined_score']
                    emb = details['embedding_similarity']
                    print(f"🔄 Match: Track {track_id} → Student {student_id} "
                          f"(score:{score:.2f}, emb:{emb:.2f})")
            else:
                # No ReID
                student_id = track_id
                is_new = True
            
            # Save face crop (with quality filtering)
            if confidence >= config.SAVE_MIN_CONFIDENCE:
                saved = self.image_manager.save_face_image(
                    frame, bbox, student_id, confidence
                )
            
            # Add to display list
            reid_detections.append((x1, y1, x2, y2, student_id, confidence))
        
        # Handle lost tracks
        if self.reid_system and config.ENABLE_REID:
            lost_tracks = self.active_tracks - current_tracks
            for lost_track in lost_tracks:
                self.reid_system.handle_track_lost(lost_track)
            
            # Periodic cleanup
            if self.frame_number % config.CLEANUP_INTERVAL == 0:
                self.reid_system.cleanup_old_tracks(current_time)
        
        self.active_tracks = current_tracks
        
        # Draw detections
        annotated_frame = self.video_processor.draw_detections(frame, reid_detections)
        
        # Draw debug overlay
        if debug:
            annotated_frame = self._draw_debug_overlay(
                annotated_frame,
                len(detections),
                len(reid_detections),
                stats_counters
            )
        
        # Draw FPS
        annotated_frame = self.video_processor.draw_fps(annotated_frame)
        
        # Draw info
        stats = self.image_manager.get_statistics()
        annotated_frame = self.video_processor.draw_info(
            annotated_frame,
            stats['total_students'],
            stats['total_images']
        )
        
        # Track processing time
        process_time = time.time() - process_start
        self.processing_times.append(process_time)
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)
        
        return annotated_frame
    
    def _draw_debug_overlay(self, frame, yolo_count, reid_count, stats):
        """Draw debug information overlay"""
        import cv2
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 90), (400, 250), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        
        # Debug text
        y_pos = 110
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        cv2.putText(frame, f"Detections: {yolo_count}", (15, y_pos), font, 0.6, (0, 255, 0), 2)
        y_pos += 25
        
        cv2.putText(frame, f"Valid: {reid_count}", (15, y_pos), font, 0.6, (0, 255, 255), 2)
        y_pos += 25
        
        cv2.putText(frame, f"New: {stats['new_students']}", (15, y_pos), font, 0.6, (255, 255, 0), 2)
        y_pos += 25
        
        cv2.putText(frame, f"Matched: {stats['matched_students']}", (15, y_pos), font, 0.6, (255, 0, 255), 2)
        y_pos += 25
        
        cv2.putText(frame, f"Quality Rejected: {stats['quality_rejected']}", (15, y_pos), font, 0.5, (0, 165, 255), 2)
        y_pos += 25
        
        # Average processing time
        if len(self.processing_times) > 0:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            cv2.putText(frame, f"Proc Time: {avg_time*1000:.1f}ms", (15, y_pos), font, 0.5, (255, 255, 255), 2)
        
        return frame
    
    def run(self):
        """Main processing loop"""
        print("🚀 Starting robust face tracking...")
        print("📹 Controls:")
        print("   'q' - Quit")
        print("   's' - Show statistics")
        print("   'r' - Reset statistics")
        print()
        
        try:
            while True:
                # Read frame
                ret, frame = self.video_processor.read_frame()
                
                if not ret:
                    print("⚠️  End of video or failed to read frame")
                    break
                
                # Process frame
                annotated_frame = self.process_frame(frame)
                
                # Display
                self.video_processor.display_frame(annotated_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n🛑 Stopping system...")
                    break
                elif key == ord('s'):
                    self._print_statistics()
                elif key == ord('r'):
                    self._reset_statistics()
        
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._cleanup()
    
    def _print_statistics(self):
        """Print comprehensive statistics"""
        print("\n" + "=" * 60)
        print("📊 ROBUST TRACKING STATISTICS")
        print("=" * 60)
        
        # Image manager stats
        stats = self.image_manager.get_statistics()
        print(f"Total Students: {stats['total_students']}")
        print(f"Total Images Saved: {stats['total_images']}")
        print(f"Frames Processed: {self.processed_frames} / {self.frame_number}")
        print(f"Current FPS: {self.video_processor.get_fps():.1f}")
        
        # Processing time
        if len(self.processing_times) > 0:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            print(f"Avg Processing Time: {avg_time*1000:.1f}ms")
        
        # Per-student counts
        if stats['students']:
            print("\n📁 Per-Student Image Count:")
            for student_id, count in sorted(stats['students'].items(), 
                                           key=lambda x: int(x[0]) if x[0].isdigit() else 0):
                print(f"   Student {student_id}: {count} images")
        
        # ReID stats
        if self.reid_system and config.ENABLE_REID:
            print("\n" + "-" * 60)
            print("🔍 ROBUST REID STATISTICS")
            print("-" * 60)
            reid_stats = self.reid_system.get_statistics()
            print(f"Total Unique Students: {reid_stats['total_students']}")
            print(f"Active Tracks: {reid_stats['active_tracks']}")
            print(f"Lost Tracks (grace period): {reid_stats['lost_tracks']}")
            print(f"Embeddings Extracted: {reid_stats['embeddings_extracted']}")
            print(f"Successful Matches: {reid_stats['successful_matches']}")
            print(f"New Students Created: {reid_stats['new_students_detected']}")
            print(f"Quality Rejections: {reid_stats['quality_rejected']}")
            print(f"Cooldown Preventions: {reid_stats['cooldown_prevented']}")
        
        print("=" * 60 + "\n")
    
    def _reset_statistics(self):
        """Reset statistics"""
        print("\n🔄 Resetting statistics...")
        self.processing_times = []
        print("✅ Statistics reset\n")
    
    def _cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        
        if self.video_processor:
            self.video_processor.release()
        
        # Final statistics
        self._print_statistics()
        
        print("✅ System stopped successfully")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Robust Classroom Face Detection and Tracking System"
    )
    
    parser.add_argument(
        '--source',
        type=str,
        default='0',
        help='Video source: 0 for webcam, or path to video file'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=config.OUTPUT_DIR,
        help=f'Output directory for student images (default: {config.OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '--preset',
        type=str,
        choices=['fast', 'balanced', 'accurate', 'hackathon'],
        default='balanced',
        help='Configuration preset (default: balanced)'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        default=config.DEVICE,
        help=f'Device for inference: cuda:0 or cpu (default: {config.DEVICE})'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Update config
    config.DEVICE = args.device
    
    # Convert source to int if digit
    video_source = int(args.source) if args.source.isdigit() else args.source
    
    # Validate video file
    if not isinstance(video_source, int):
        if not Path(video_source).exists():
            print(f"❌ Error: Video file not found: {video_source}")
            sys.exit(1)
    
    # Create and run system
    system = RobustClassroomTrackingSystem(
        video_source=video_source,
        output_dir=args.output,
        preset=args.preset
    )
    
    system.run()


if __name__ == "__main__":
    main()
