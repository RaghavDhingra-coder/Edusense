# 📊 Student-wise Engagement Analytics

**Analyze classroom engagement from collected face images using deep learning**

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Make sure you have student images collected
ls students/

# 2. Run the dashboard
./run_analytics_dashboard.sh

# 3. Open browser
# Navigate to: http://localhost:5000

# 4. Click "Analyze Classroom"
```

---

## 🎯 What It Does

Analyzes ALL images in each student folder and determines:
- **Focused** (70%+) - Highly engaged
- **Neutral** (40-69%) - Moderately engaged  
- **Distracted** (<40%) - Low engagement

### Engagement Classes Detected:
- ✅ Engaged
- 🤔 Confused
- 😤 Frustrated
- 👀 Looking Away
- 😴 Bored
- 💤 Drowsy

---

## 📊 Dashboard Features

### Summary Cards
- Total Students
- Focused Count
- Distracted Count
- Average Engagement %

### Distribution Chart
Visual breakdown of classroom engagement levels

### Student Cards
For each student:
- Face image
- Engagement score (0-100%)
- Status badge
- Images analyzed
- Detailed breakdown

---

## 🚀 Usage Options

### Option 1: Web Dashboard (Recommended)

```bash
./run_analytics_dashboard.sh
```

Then open: `http://localhost:5000`

### Option 2: Command Line

```bash
python engagement_analytics.py --students-dir students --output report.json
```

Generates `engagement_report.json` with complete analytics.

### Option 3: Python API

```python
from engagement_analytics import EngagementAnalytics

# Create analytics engine
analytics = EngagementAnalytics(
    model_path='best_model_state.bin',
    students_dir='students'
)

# Generate report
report = analytics.generate_report('report.json')

# Print summary
print(f"Average engagement: {report['summary']['average_engagement']}%")
print(f"Focused students: {report['summary']['focused_students']}")
```

---

## 📁 Required Files

```
✅ best_model_state.bin    # Trained engagement model
✅ engagement_model.py     # Model architecture
✅ engagement_analytics.py # Analytics engine
✅ api_server.py           # Flask API
✅ frontend/               # Dashboard files
✅ students/               # Student face images
   ├── student_1/
   ├── student_2/
   └── ...
```

---

## 🔧 API Endpoints

### POST /api/analyze
Analyze all students
```bash
curl -X POST http://localhost:5000/api/analyze
```

### GET /api/student/<id>
Get specific student details
```bash
curl http://localhost:5000/api/student/student_1
```

### GET /api/summary
Get cached summary
```bash
curl http://localhost:5000/api/summary
```

### GET /api/stats
Get quick statistics
```bash
curl http://localhost:5000/api/stats
```

---

## 📊 Scoring System

### Weights
```
Engaged         = +2
Confused        = +1
Frustrated      =  0
Looking Away    = -1
Bored           = -1
Drowsy          = -2
```

### Calculation
```
Total Score = Σ(class_weight × count)
Normalized = (score - min) / (max - min) × 100
```

### Status Determination
```
Score ≥ 70%  → Focused
Score 40-69% → Neutral
Score < 40%  → Distracted
```

---

## 🎨 Example Output

### Console
```
📊 CLASSROOM ENGAGEMENT SUMMARY
============================================================
Total Students: 15
Focused: 10
Neutral: 3
Distracted: 2
Average Engagement: 72.5%
Total Images Analyzed: 1850
============================================================
```

### JSON Report
```json
{
  "summary": {
    "total_students": 15,
    "focused_students": 10,
    "neutral_students": 3,
    "distracted_students": 2,
    "average_engagement": 72.5
  },
  "students": [
    {
      "student_id": "student_1",
      "status": "Focused",
      "engagement_score": 82.3,
      "images_analyzed": 124,
      "prediction_breakdown": {...}
    }
  ]
}
```

---

## 🐛 Troubleshooting

### No students found
**Problem**: `Warning: No student folders found`
**Solution**: Run tracking system first to collect images

### Model not found
**Problem**: `Failed to load model`
**Solution**: Ensure `best_model_state.bin` is in project root

### Port already in use
**Problem**: `Address already in use`
**Solution**: 
```bash
# Kill existing process
lsof -ti:5000 | xargs kill -9

# Or use different port
python api_server.py --port 5001
```

### CORS errors
**Problem**: Browser blocks API requests
**Solution**: Flask-CORS is enabled. Check browser console for details.

---

## 📈 Performance

- **Speed**: 50-100 images/second (CPU)
- **Memory**: ~1-2GB peak usage
- **Typical**: 15 students × 100 images = 30-60 seconds

### Optimization
```python
# Use GPU
analytics = EngagementAnalytics(device='cuda')

# Increase batch size
analytics = EngagementAnalytics(batch_size=64)
```

---

## 🔄 Workflow

```
1. Run Tracking System
   ↓
   Collect face images → students/student_X/

2. Run Analytics
   ↓
   Analyze all images → Generate report

3. View Dashboard
   ↓
   Visualize results → Make decisions
```

---

## 🎓 Use Cases

### Post-Session Analysis
After recording a class:
```bash
python engagement_analytics.py
```

### Live Dashboard
During or after class:
```bash
./run_analytics_dashboard.sh
```

### Batch Processing
Multiple sessions:
```bash
for dir in session_*/students; do
    python engagement_analytics.py --students-dir $dir --output ${dir}_report.json
done
```

---

## 📚 Documentation

- **Complete Guide**: `ENGAGEMENT_ANALYTICS_GUIDE.md`
- **API Reference**: See `api_server.py` docstrings
- **Model Details**: See `engagement_model.py`

---

## ✅ Checklist

Before running analytics:
- [ ] Tracking system has run and collected images
- [ ] `students/` directory exists with student folders
- [ ] Each folder has at least 10-20 images
- [ ] `best_model_state.bin` is present
- [ ] Dependencies installed (`pip install -r requirements.txt`)

---

## 🎯 Tips

1. **Collect enough images** - At least 50 per student for reliable results
2. **Good quality** - Ensure clear, well-lit faces
3. **Regular analysis** - Run after each session
4. **Combine metrics** - Use with attendance, participation data
5. **Validate results** - Spot-check predictions

---

## 🚀 Integration

### With Tracking System

Add to `main_robust.py` after tracking:
```python
# After tracking completes
from engagement_analytics import EngagementAnalytics

print("\n🔄 Running engagement analysis...")
analytics = EngagementAnalytics()
report = analytics.generate_report()
print(f"✅ Average engagement: {report['summary']['average_engagement']}%")
```

### With External Systems

```python
import requests

# Trigger analysis
response = requests.post('http://localhost:5000/api/analyze')
data = response.json()

# Get results
summary = data['summary']
students = data['students']

# Use in your system
for student in students:
    print(f"{student['student_id']}: {student['engagement_score']}%")
```

---

## 📞 Support

**Issues?**
1. Check logs in console
2. Verify model file exists
3. Ensure student folders have images
4. Review `ENGAGEMENT_ANALYTICS_GUIDE.md`

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Compatible with**: EduSense AI Tracking System v1.0+

---

Made with ❤️ for education
