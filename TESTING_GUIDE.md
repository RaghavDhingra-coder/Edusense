# EduSense AI - Testing Guide
**Quick Reference for Testing All Features**

---

## 🚀 Quick Start

### Server is Already Running ✅
- **Process ID**: 82196
- **Port**: 8080
- **Status**: Operational

### Access Points
- **Local**: http://localhost:8080
- **Ngrok**: https://wharf-undertake-dawdler.ngrok-free.dev

---

## 🧪 Test Scenarios

### Test 1: Ngrok Camera Startup (PRIORITY)
**Goal**: Verify the "string did not match" error is fixed

**Steps**:
1. Open browser (Chrome or Safari)
2. Navigate to: https://wharf-undertake-dawdler.ngrok-free.dev
3. Open browser console (F12 or Cmd+Option+I)
4. Click "Start Camera" button
5. Watch console for debug logs

**Expected Result**:
```
═══════════════════════════════════════════════════════
🎥 STARTING CAMERA - DEBUG INFO
═══════════════════════════════════════════════════════
Current URL: https://wharf-undertake-dawdler.ngrok-free.dev/
Origin: https://wharf-undertake-dawdler.ngrok-free.dev
Fetching: /api/camera/start
Response status: 200
Response ok: true
✅ Camera started
📺 SETTING VIDEO STREAM
Stream URL: /api/video_feed?t=1234567890
Validated full URL: https://wharf-undertake-dawdler.ngrok-free.dev/api/video_feed?t=1234567890
✅ Video src set successfully
```

**Success Criteria**:
- ✅ No "string did not match" error
- ✅ Video stream loads and displays
- ✅ FPS counter starts updating
- ✅ Detection boxes appear on faces

**If It Fails**:
- Check console for error messages
- Look for the exact line where it fails
- Copy the full error stack trace
- Share the console logs

---

### Test 2: Recognition Accuracy (CRITICAL)
**Goal**: Verify instant recognition with no "Unknown → Name" delay

**Steps**:
1. Start camera (localhost or ngrok)
2. Position a registered student in front of camera:
   - Mayur
   - Raghav
   - Tanmay
   - Abhishek
3. Watch the bounding box and name label
4. Check browser console for recognition logs

**Expected Result**:
- **Frame 1**: Shows correct name immediately (no "Unknown" first)
- **Bounding Box**: Green color for registered students
- **Name Label**: Stable, no flickering
- **Console Logs**: Recognition time <10ms

**Success Criteria**:
- ✅ Correct name from first frame
- ✅ No "Unknown" → "Correct Name" transition
- ✅ Stable identity (no flickering between names)
- ✅ Green bounding box for registered students
- ✅ Orange bounding box for unknown persons

**If It Fails**:
- Check server logs for recognition debug messages
- Look for similarity scores in logs
- Verify embeddings loaded correctly
- Check if recognition engine initialized

---

### Test 3: FPS Performance
**Goal**: Verify smooth frame rate with recognition enabled

**Steps**:
1. Start camera
2. Watch the FPS counter in the UI
3. Check browser console for timing logs

**Expected Result**:
- **FPS**: 15-20 FPS (target)
- **Recognition Time**: <10ms per frame
- **Frame Processing**: Smooth, no stuttering

**Success Criteria**:
- ✅ FPS counter updates every second
- ✅ FPS stays above 10 (minimum acceptable)
- ✅ Video stream is smooth
- ✅ No lag or freezing

**If It Fails**:
- Check if recognition is blocking frame processing
- Verify cache is being used (should see cache hit logs)
- Check CPU usage
- Look for performance warnings in logs

---

### Test 4: Video Upload via Ngrok
**Goal**: Verify video upload and analysis works via ngrok

**Steps**:
1. Open: https://wharf-undertake-dawdler.ngrok-free.dev
2. Click "Upload Video" tab
3. Select a video file with faces
4. Click "Upload and Analyze"
5. Wait for processing
6. Check results

**Expected Result**:
- ✅ Video uploads successfully
- ✅ Processing starts automatically
- ✅ Progress bar shows upload status
- ✅ Analysis results display after processing
- ✅ Detected students shown with statistics

**Success Criteria**:
- ✅ Upload completes without errors
- ✅ Analysis runs successfully
- ✅ Results match expected students
- ✅ Statistics are accurate

---

### Test 5: Student Registration via Ngrok
**Goal**: Verify student registration works via ngrok

**Steps**:
1. Open: https://wharf-undertake-dawdler.ngrok-free.dev/register.html
2. Enter student name
3. Upload a photo or capture from camera
4. Click "Register Student"
5. Verify student appears in list

**Expected Result**:
- ✅ Registration form works
- ✅ Photo upload/capture works
- ✅ Student added to database
- ✅ Student appears in list immediately
- ✅ Recognition cache updated (hot-reload)

**Success Criteria**:
- ✅ No errors during registration
- ✅ Student visible in list
- ✅ Can test recognition immediately (no server restart needed)

---

### Test 6: Analytics Timing
**Goal**: Verify analytics work after camera stops

**Steps**:
1. Start camera
2. Let it run for 30-60 seconds
3. Click "Stop Camera"
4. **Wait 30-60 seconds** (important!)
5. Click "Analyze" button
6. Check results

**Expected Result**:
- ✅ Analysis runs successfully
- ✅ Results show detected students
- ✅ Statistics are accurate
- ✅ Images are available

**Success Criteria**:
- ✅ No "No images found" error
- ✅ Analysis completes successfully
- ✅ Results match camera session

**If "No Images Found" Error**:
- This is expected if you click "Analyze" too quickly
- Wait 30-60 seconds after stopping camera
- Images are still uploading to cloud
- Check upload status: http://localhost:8080/api/upload/status

---

## 🔍 Debugging Tips

### Browser Console
Open with: `F12` or `Cmd+Option+I` (Mac) or `Ctrl+Shift+I` (Windows)

**Look for**:
- Debug logs starting with 🎥, 📺, ✅, ❌
- Error messages in red
- Network requests in Network tab
- Response data in console

### Server Logs
**View logs**:
```bash
# If server is running in terminal, logs appear there
# Or check the process output
```

**Look for**:
- Recognition timing logs
- Similarity scores
- Cache hit/miss logs
- Error tracebacks

### Common Issues

#### Issue: "String did not match" error
**Solution**: Already fixed with relative URLs
**Verify**: Check console shows relative URLs like `/api/camera/start`

#### Issue: "Unknown" then correct name
**Solution**: Recognition engine with temporal smoothing
**Verify**: Check server logs for recognition timing

#### Issue: "No images found" in analytics
**Solution**: Wait 30-60 seconds after stopping camera
**Verify**: Check `/api/upload/status` endpoint

#### Issue: Low FPS
**Solution**: Recognition cache should speed things up
**Verify**: Check recognition time in logs (<10ms target)

---

## 📊 Performance Benchmarks

### Target Metrics
- **Recognition Time**: <10ms per frame
- **FPS**: 15-20 FPS with recognition enabled
- **Cache Lookup**: 1-2ms
- **Frame Processing**: <50ms total
- **Upload Time**: 30-60 seconds for full session

### Acceptable Ranges
- **Recognition Time**: <20ms (acceptable)
- **FPS**: >10 FPS (minimum)
- **Cache Lookup**: <5ms (acceptable)

---

## ✅ Test Checklist

### Ngrok Deployment
- [ ] Camera starts without "string did not match" error
- [ ] Video stream loads via ngrok
- [ ] FPS counter updates
- [ ] Detection works
- [ ] Recognition works
- [ ] Video upload works
- [ ] Student registration works
- [ ] Analytics work

### Recognition System
- [ ] Registered students recognized instantly
- [ ] No "Unknown → Name" delay
- [ ] Stable identity (no flickering)
- [ ] Green box for known students
- [ ] Orange box for unknown persons
- [ ] Recognition time <10ms
- [ ] Cache working (fast lookups)

### Performance
- [ ] FPS stays above 10
- [ ] Video stream is smooth
- [ ] No lag or freezing
- [ ] Recognition doesn't block frames
- [ ] Upload completes in reasonable time

### End-to-End Workflow
- [ ] Start camera → Detect → Recognize → Stop
- [ ] Upload video → Process → Analyze → Results
- [ ] Register student → Test recognition → Success
- [ ] Analytics → View statistics → Export data

---

## 🎯 Priority Testing Order

1. **First**: Test ngrok camera startup (Test 1)
2. **Second**: Test recognition accuracy (Test 2)
3. **Third**: Test FPS performance (Test 3)
4. **Fourth**: Test video upload (Test 4)
5. **Fifth**: Test student registration (Test 5)
6. **Sixth**: Test analytics (Test 6)

---

## 📝 Reporting Issues

If you encounter issues, please provide:

1. **Which test failed**: Test number and name
2. **Browser console logs**: Copy the full console output
3. **Server logs**: Copy relevant server log lines
4. **Screenshots**: If visual issues
5. **Steps to reproduce**: Exact steps you followed
6. **Expected vs Actual**: What you expected vs what happened

---

## 🎉 Success Indicators

**System is working correctly when**:
- ✅ Camera starts on both localhost and ngrok
- ✅ Recognition shows correct names immediately
- ✅ FPS stays smooth (>10 FPS)
- ✅ All features work via ngrok
- ✅ No errors in console or logs

---

*Last Updated: May 13, 2026*
