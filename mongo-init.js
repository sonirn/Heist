// MongoDB initialization script for production
db = db.getSiblingDB('script_to_video_production');

// Create collections with proper indexes
db.createCollection('projects');
db.createCollection('generations');
db.createCollection('videos');
db.createCollection('users');
db.createCollection('analytics');
db.createCollection('sessions');

// Create indexes for performance
db.projects.createIndex({ "project_id": 1 }, { unique: true });
db.projects.createIndex({ "user_id": 1, "created_at": -1 });
db.projects.createIndex({ "status": 1 });
db.projects.createIndex({ "title": "text" });

db.generations.createIndex({ "generation_id": 1 }, { unique: true });
db.generations.createIndex({ "project_id": 1 });
db.generations.createIndex({ "status": 1 });
db.generations.createIndex({ "created_at": -1 });

db.videos.createIndex({ "generation_id": 1 });
db.videos.createIndex({ "project_id": 1 });
db.videos.createIndex({ "status": 1 });
db.videos.createIndex({ "created_at": -1 });

db.users.createIndex({ "user_id": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

db.analytics.createIndex({ "timestamp": -1, "event_type": 1 });
db.analytics.createIndex({ "user_id": 1, "timestamp": -1 });

db.sessions.createIndex({ "session_id": 1 }, { unique: true });
db.sessions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 3600 });

// Insert default data
db.projects.insertOne({
  project_id: "system_health_check",
  title: "System Health Check",
  script: "This is a system health check project",
  status: "created",
  created_at: new Date(),
  updated_at: new Date()
});

print("Database initialized successfully");