"""
Flask API Server for Engagement Analytics
Provides REST endpoints for frontend dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime

from hybrid_attentiveness import HybridAttentivenessAnalyzer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global analytics engine
analytics_engine = None


def get_analytics_engine():
    """Get or create analytics engine"""
    global analytics_engine
    
    if analytics_engine is None:
        analytics_engine = HybridAttentivenessAnalyzer(
            students_dir='students',
            focus_threshold=0.65,
            yaw_threshold=30.0,
            pitch_threshold=30.0,
            roll_threshold=35.0,
            consecutive_distraction_threshold=2
        )
    
    return analytics_engine


@app.route('/api/debug/predict', methods=['POST'])
def debug_predict():
    """
    Debug endpoint: analyze single image for attentiveness
    
    Expects: multipart/form-data with 'image' file
    Returns: Head pose data and attentiveness prediction
    """
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['image']
        
        # Save temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # Get analytics engine
        engine = get_analytics_engine()
        
        # Analyze image using hybrid analyzer
        result = engine.analyze_single_frame(tmp_path)
        
        # Clean up
        import os
        os.unlink(tmp_path)
        
        if result is None or result.get('method') == 'failed':
            return jsonify({
                'success': False,
                'error': result.get('reason', 'Failed to analyze image')
            }), 400
        
        response = {
            'success': True,
            'is_focused': result['is_focused'],
            'confidence': result['confidence'],
            'method': result['method']
        }
        
        # Add method-specific data
        if result['method'] == 'head_pose':
            response.update({
                'yaw': result['yaw'],
                'pitch': result['pitch'],
                'roll': result['roll'],
                'yaw_ok': result['yaw_ok'],
                'pitch_ok': result['pitch_ok'],
                'roll_ok': result['roll_ok']
            })
        elif result['method'] == 'image_quality_fallback':
            response.update({
                'quality': result['quality'],
                'sharpness': result.get('sharpness', 0),
                'brightness': result.get('brightness', 0)
            })
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Debug predict failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_classroom():
    """
    Analyze all students and return engagement analytics
    Includes automatic identity merge step
    
    Returns:
        JSON with student analytics and classroom summary
    """
    try:
        logger.info("=" * 60)
        logger.info("🔍 Starting classroom analysis...")
        logger.info("=" * 60)
        
        # Get analytics engine
        logger.info("Loading analytics engine...")
        engine = get_analytics_engine()
        logger.info("✅ Analytics engine loaded")
        
        # Analyze all students
        logger.info("Analyzing all students...")
        all_analytics = engine.analyze_all_students()
        logger.info(f"✅ Analyzed {len(all_analytics)} students")
        
        # Compute summary
        logger.info("Computing classroom summary...")
        summary = engine.compute_classroom_summary(all_analytics)
        logger.info(f"✅ Summary computed: {summary['average_engagement']}% avg engagement")
        
        # Prepare response
        response = {
            'success': True,
            'summary': summary,
            'students': all_analytics,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("=" * 60)
        logger.info(f"✅ Analysis complete: {len(all_analytics)} students")
        logger.info("=" * 60)
        
        return jsonify(response)
    
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Analysis failed: {str(e)}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/student/<student_id>', methods=['GET'])
def get_student_details(student_id):
    """
    Get detailed analytics for a specific student
    
    Args:
        student_id: Student identifier
        
    Returns:
        JSON with student details
    """
    try:
        engine = get_analytics_engine()
        
        # Analyze specific student
        student_folder = os.path.join(engine.students_dir, student_id)
        
        if not os.path.exists(student_folder):
            return jsonify({
                'success': False,
                'error': f'Student {student_id} not found'
            }), 404
        
        analytics = engine.analyze_student_folder(student_folder)
        
        if analytics is None:
            return jsonify({
                'success': False,
                'error': f'No valid data for {student_id}'
            }), 404
        
        return jsonify({
            'success': True,
            'student': analytics
        })
    
    except Exception as e:
        logger.error(f"Failed to get student details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """
    Get classroom summary without full analysis
    Reads from cached report if available
    
    Returns:
        JSON with classroom summary
    """
    try:
        report_file = 'engagement_report.json'
        
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            return jsonify({
                'success': True,
                'summary': report['summary'],
                'cached': True,
                'timestamp': report.get('timestamp')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No cached report available. Run analysis first.'
            }), 404
    
    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """
    Serve student images
    
    Args:
        filename: Image filename (e.g., student_1/frame_001.jpg)
        
    Returns:
        Image file
    """
    try:
        # Security: ensure path is within students directory
        safe_path = os.path.normpath(filename)
        if '..' in safe_path:
            return jsonify({'error': 'Invalid path'}), 400
        
        directory = os.path.dirname(os.path.join('students', safe_path))
        filename = os.path.basename(safe_path)
        
        return send_from_directory(directory, filename)
    
    except Exception as e:
        logger.error(f"Failed to serve image: {str(e)}")
        return jsonify({'error': str(e)}), 404


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get quick statistics about available data
    
    Returns:
        JSON with data statistics
    """
    try:
        students_dir = 'students'
        
        if not os.path.exists(students_dir):
            return jsonify({
                'success': True,
                'total_students': 0,
                'total_images': 0
            })
        
        # Count students and images
        student_folders = [
            d for d in os.listdir(students_dir)
            if os.path.isdir(os.path.join(students_dir, d))
            and d.startswith('student_')
        ]
        
        total_images = 0
        for folder in student_folders:
            folder_path = os.path.join(students_dir, folder)
            images = [
                f for f in os.listdir(folder_path)
                if f.endswith(('.jpg', '.jpeg', '.png'))
            ]
            total_images += len(images)
        
        return jsonify({
            'success': True,
            'total_students': len(student_folders),
            'total_images': total_images
        })
    
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Serve frontend dashboard"""
    return send_from_directory('frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static frontend files"""
    return send_from_directory('frontend', path)


def main():
    """Run Flask server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Engagement Analytics API Server")
    parser.add_argument('--host', default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting API server on {args.host}:{args.port}")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
