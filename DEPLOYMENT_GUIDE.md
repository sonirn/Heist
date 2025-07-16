# Production Deployment Guide

## 🚀 Script-to-Video Application - Production Ready

This guide provides comprehensive instructions for deploying the enhanced script-to-video application in production environments.

## 📋 Table of Contents

1. [Production Enhancements](#production-enhancements)
2. [System Requirements](#system-requirements)
3. [Environment Setup](#environment-setup)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security Configuration](#security-configuration)
8. [Performance Optimization](#performance-optimization)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## 🔧 Production Enhancements

### **Scalability & Performance**
- **Database Optimization**: Connection pooling, indexing, and query optimization
- **Cache Management**: In-memory caching with TTL support and automatic cleanup
- **File Management**: Chunked uploads, storage optimization, and automated cleanup
- **Queue System**: Background processing with priority queues and retry logic
- **Performance Monitoring**: Real-time metrics, error tracking, and resource monitoring

### **Infrastructure**
- **Production-Ready Docker Setup**: Multi-stage builds, health checks, resource limits
- **Load Balancing**: Nginx reverse proxy with rate limiting and compression
- **Database Production Config**: MongoDB with proper indexing and replication
- **CDN Integration**: Cloudflare R2 storage for video delivery
- **Auto-scaling**: Horizontal scaling support with queue-based processing

### **Monitoring & Observability**
- **Health Checks**: Comprehensive health monitoring with system metrics
- **Error Tracking**: Centralized error logging and performance monitoring
- **Metrics Collection**: Real-time performance metrics and resource usage
- **Alerting**: System health warnings and critical status monitoring

## 📊 System Requirements

### **Minimum Requirements**
- **CPU**: 4 cores
- **Memory**: 8GB RAM
- **Storage**: 50GB SSD
- **Network**: 1Gbps bandwidth

### **Recommended Requirements**
- **CPU**: 8 cores
- **Memory**: 16GB RAM
- **Storage**: 200GB SSD
- **Network**: 10Gbps bandwidth

### **Software Dependencies**
- Docker 24.0+
- Docker Compose 2.0+
- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Redis 7.0+
- Nginx 1.24+

## 🌍 Environment Setup

### **1. Environment Variables**

Create production environment files:

```bash
# backend/.env.production
ENVIRONMENT=production
MONGO_URL=mongodb://mongodb:27017/script_to_video_production
DB_NAME=script_to_video_production

# API Keys (replace with your own)
GEMINI_API_KEY_1=your_gemini_api_key_1
GEMINI_API_KEY_2=your_gemini_api_key_2
GEMINI_API_KEY_3=your_gemini_api_key_3
MINIMAX_API_KEY=your_minimax_api_key
RUNWAYML_API_KEY1=your_runwayml_api_key_1
RUNWAYML_API_KEY2=your_runwayml_api_key_2

# R2 Storage Configuration
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your_r2_access_key
R2_SECRET_KEY=your_r2_secret_key
R2_BUCKET_NAME=your-bucket-name
```

```bash
# frontend/.env.production
REACT_APP_BACKEND_URL=https://your-domain.com
NODE_ENV=production
```

### **2. SSL Certificate Setup**

For HTTPS support, place your SSL certificates in `/app/ssl/`:

```bash
mkdir -p /app/ssl
cp your_domain.crt /app/ssl/
cp your_domain.key /app/ssl/
```

## 🐳 Docker Deployment

### **1. Build and Deploy**

```bash
# Build production images
docker-compose -f docker-compose.production.yml build

# Start production stack
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps
```

### **2. Service Configuration**

The production setup includes:

- **Backend**: 4 worker processes with health checks
- **Frontend**: Nginx-optimized static serving
- **MongoDB**: Production configuration with replication
- **Redis**: Memory-optimized caching
- **Nginx**: Load balancing and SSL termination

### **3. Resource Limits**

Services are configured with appropriate resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

## ☸️ Kubernetes Deployment

For Kubernetes deployment, apply the provided manifests:

```bash
# Apply production configuration
kubectl apply -f k8s/production/

# Check deployment status
kubectl get pods -n script-to-video
```

## 📈 Monitoring & Observability

### **1. Health Check Endpoints**

- **Main Health**: `GET /api/health`
- **System Metrics**: `GET /api/metrics`
- **Error Logs**: `GET /api/errors`
- **System Info**: `GET /api/system-info`

### **2. Metrics Collection**

The application collects:

- **System Metrics**: CPU, Memory, Disk usage
- **Application Metrics**: Response times, error rates
- **Business Metrics**: Video generation success rates
- **Queue Metrics**: Task processing statistics

### **3. Alerting**

Health check warnings trigger for:

- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Error rate > 5%

## 🔒 Security Configuration

### **1. Network Security**

- Rate limiting on API endpoints
- CORS configuration
- Input validation and sanitization
- Request size limits

### **2. Authentication & Authorization**

- API key validation
- JWT token authentication
- Role-based access control
- Session management

### **3. Data Security**

- Encryption at rest
- SSL/TLS encryption
- Secure file uploads
- Database access controls

## ⚡ Performance Optimization

### **1. Database Optimization**

```javascript
// MongoDB indexes for optimal performance
db.projects.createIndex({ "user_id": 1, "created_at": -1 })
db.generations.createIndex({ "generation_id": 1 }, { unique: true })
db.videos.createIndex({ "status": 1, "created_at": -1 })
```

### **2. Caching Strategy**

- **Memory Cache**: Frequently accessed data
- **Redis Cache**: Session and temporary data
- **CDN Cache**: Static assets and videos
- **Database Cache**: Query result caching

### **3. Queue Processing**

- **Priority Queues**: Critical tasks processed first
- **Retry Logic**: Automatic retry with exponential backoff
- **Worker Scaling**: Multiple workers for parallel processing
- **Resource Management**: Memory and CPU optimization

## 💾 Backup & Recovery

### **1. Database Backup**

```bash
# Create MongoDB backup
mongodump --uri="mongodb://localhost:27017/script_to_video_production" --out=/backups/

# Restore from backup
mongorestore --uri="mongodb://localhost:27017/script_to_video_production" /backups/
```

### **2. File Storage Backup**

```bash
# Backup R2 storage
aws s3 sync s3://your-bucket-name /local/backup/videos/

# Restore files
aws s3 sync /local/backup/videos/ s3://your-bucket-name
```

### **3. Configuration Backup**

- Environment files
- SSL certificates
- Database configuration
- Application logs

## 🔧 Troubleshooting

### **Common Issues**

1. **High Memory Usage**
   - Check for memory leaks in video processing
   - Optimize file cleanup processes
   - Increase worker memory limits

2. **Slow Video Generation**
   - Monitor API response times
   - Check queue processing status
   - Verify network connectivity

3. **Database Connection Issues**
   - Check MongoDB connection pool
   - Verify database indexes
   - Monitor connection limits

### **Debugging Commands**

```bash
# Check application logs
docker-compose logs -f backend

# Monitor system resources
docker stats

# Check database status
docker exec -it mongodb mongo --eval "db.stats()"

# View queue status
curl http://localhost:8001/api/system-info
```

## 📝 Maintenance

### **Regular Tasks**

- **Daily**: Check health metrics and error logs
- **Weekly**: Review performance metrics and optimize
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Capacity planning and scaling review

### **Monitoring Checklist**

- [ ] Health check endpoints responding
- [ ] Database connections stable
- [ ] Queue processing normally
- [ ] Storage usage within limits
- [ ] Error rates below threshold
- [ ] API response times acceptable

## 🚀 Scaling

### **Horizontal Scaling**

- Add more backend worker instances
- Implement database sharding
- Use load balancers for distribution
- Scale queue workers based on load

### **Vertical Scaling**

- Increase CPU and memory allocation
- Optimize database queries
- Improve caching strategies
- Enhance file processing efficiency

## 📞 Support

For production support and troubleshooting:

1. Check the health endpoints for system status
2. Review application logs for errors
3. Monitor system metrics for performance issues
4. Verify database and queue status
5. Contact technical support with specific error details

---

**Production Deployment Status**: ✅ Ready for deployment

**Last Updated**: July 16, 2025

**Version**: 2.0-production