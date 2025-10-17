# 🚀 Deployment Guide

## Pre-Deployment Checklist

✅ **Files Ready for Deployment:**
- [ ] `api/model_rf_pipeline.joblib` - Main Random Forest model (✅ Exported)
- [ ] `api/metrics_precomputed.json` - Model performance data (✅ Created)
- [ ] `api/test_set_small.json` - Test dataset sample (✅ Created)
- [ ] `requirements.txt` - Python dependencies (✅ Ready)
- [ ] `vercel.json` - Deployment configuration (✅ Configured)
- [ ] `README.md` - Project documentation (✅ Updated)
- [ ] `LICENSE` - MIT License (✅ Added)
- [ ] `.gitignore` - Git ignore file (✅ Added)

## 🌐 Deploy to Vercel

### Step 1: Push to GitHub

```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit: Fraud Detection System"

# Create new repository on GitHub, then:
git remote add origin https://github.com/yourusername/fraud-detection.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Vercel

1. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub
2. **Click "New Project"**
3. **Import your GitHub repository**
4. **Configure project**:
   - Framework Preset: **Other**
   - Root Directory: **/** (default)
   - No environment variables needed
5. **Click "Deploy"**
6. **Wait for deployment** (usually 1-2 minutes)

### Step 3: Test Your Deployment

Once deployed, test these URLs:
- `https://your-project.vercel.app/` - Main dashboard
- `https://your-project.vercel.app/transaction.html` - Transaction form
- `https://your-project.vercel.app/api/predict` - API endpoint (POST)
- `https://your-project.vercel.app/api/metrics` - Metrics endpoint (GET)

## 🧪 Pre-Deployment Testing

### Test Local API
```bash
python test_local_api.py
```
Expected output: ✅ Success with fraud prediction

### Test Transaction Form
1. Start local server: `python local_server.py`
2. Open: `http://localhost:8002/transaction.html`
3. Fill form with test data:
   - Amount: 9000.60
   - Old Balance Origin: 9000.60
   - Transaction Type: Cash Out
4. Submit and verify fraud detection works

## 🔧 Post-Deployment

### Update Your README
Replace `yourusername` with your actual GitHub username:
```markdown
git clone https://github.com/YOURUSERNAME/fraud-detection.git
```

### Custom Domain (Optional)
1. In Vercel dashboard → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

### Analytics (Optional)
Vercel provides built-in analytics:
- Go to your project dashboard
- Click "Analytics" tab
- Monitor API usage and performance

## 🚨 Troubleshooting

### Common Deployment Issues

**❌ Build Failed: Python dependencies**
- Check `requirements.txt` has correct package versions
- Ensure scikit-learn, starlette, joblib are included

**❌ Function Timeout**
- Model file too large (>250MB limit for Vercel)
- Optimize model or use model compression

**❌ 500 Error: Model file not found**
- Verify `api/model_rf_pipeline.joblib` is in repository
- Check file was properly committed and pushed

**❌ API Returns 404**
- Verify Vercel routes in `vercel.json`
- Check function endpoints are correctly named

### Performance Optimization

1. **Model Size**: Keep under 100MB for optimal performance
2. **Cold Starts**: First request may be slower (~2-3 seconds)
3. **Concurrent Requests**: Vercel auto-scales serverless functions

## 📊 Monitoring

### Vercel Analytics
- Function invocations
- Response times
- Error rates
- Geographic distribution

### Custom Monitoring
Add logging to track:
- Prediction accuracy over time
- Most common transaction types
- API usage patterns

## 🔄 Updates and Maintenance

### Model Updates
1. Retrain model in notebook
2. Export new `model_rf_pipeline.joblib`
3. Commit and push to GitHub
4. Vercel auto-deploys

### Code Updates
1. Make changes locally
2. Test with `python local_server.py`
3. Commit and push to GitHub
4. Vercel automatically redeploys

---

**🎉 Your fraud detection system is now ready for production!**

Share your deployed URL and help prevent financial fraud worldwide! 🛡️