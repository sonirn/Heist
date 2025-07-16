"""
Queue Management System
Handles background processing with priority queues and retry logic
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import uuid
from enum import Enum
from dataclasses import dataclass
import traceback

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Task:
    """Task data structure"""
    id: str
    name: str
    handler: str
    payload: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Any] = None

class QueueManager:
    """Async queue manager with priority support and retry logic"""
    
    def __init__(self):
        self.queues: Dict[TaskPriority, asyncio.Queue] = {
            TaskPriority.CRITICAL: asyncio.Queue(),
            TaskPriority.HIGH: asyncio.Queue(),
            TaskPriority.MEDIUM: asyncio.Queue(),
            TaskPriority.LOW: asyncio.Queue()
        }
        self.tasks: Dict[str, Task] = {}
        self.handlers: Dict[str, Callable] = {}
        self.workers: List[asyncio.Task] = []
        self.worker_count = 3
        self.is_running = False
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "retry_tasks": 0
        }
    
    def register_handler(self, name: str, handler: Callable):
        """Register task handler function"""
        self.handlers[name] = handler
        logger.info(f"Registered task handler: {name}")
    
    async def add_task(self, name: str, handler: str, payload: Dict[str, Any],
                      priority: TaskPriority = TaskPriority.MEDIUM,
                      max_retries: int = 3) -> str:
        """Add task to queue"""
        try:
            task_id = str(uuid.uuid4())
            
            task = Task(
                id=task_id,
                name=name,
                handler=handler,
                payload=payload,
                priority=priority,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                max_retries=max_retries
            )
            
            self.tasks[task_id] = task
            await self.queues[priority].put(task)
            
            self.stats["total_tasks"] += 1
            logger.info(f"Added task {task_id} with priority {priority.name}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to add task: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and result"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "error_message": task.error_message,
            "result": task.result
        }
    
    async def start_workers(self):
        """Start background worker tasks"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.worker_count):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker_task)
        
        logger.info(f"Started {self.worker_count} queue workers")
    
    async def stop_workers(self):
        """Stop all workers"""
        self.is_running = False
        
        # Cancel all worker tasks
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Stopped all queue workers")
    
    async def _worker(self, worker_name: str):
        """Worker task that processes queue items"""
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get next task from highest priority queue
                task = await self._get_next_task()
                
                if task:
                    await self._process_task(task, worker_name)
                else:
                    # No tasks available, wait briefly
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _get_next_task(self) -> Optional[Task]:
        """Get next task from highest priority queue"""
        # Check queues in priority order
        for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                        TaskPriority.MEDIUM, TaskPriority.LOW]:
            try:
                task = self.queues[priority].get_nowait()
                return task
            except asyncio.QueueEmpty:
                continue
        
        return None
    
    async def _process_task(self, task: Task, worker_name: str):
        """Process a single task"""
        try:
            # Update task status
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            
            logger.info(f"Worker {worker_name} processing task {task.id}: {task.name}")
            
            # Get handler function
            handler = self.handlers.get(task.handler)
            if not handler:
                raise ValueError(f"No handler registered for: {task.handler}")
            
            # Execute task
            result = await handler(task.payload)
            
            # Mark task as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            self.stats["completed_tasks"] += 1
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.error_message = str(e)
            
            # Handle retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRY
                
                # Add back to queue with exponential backoff
                delay = min(60, 2 ** task.retry_count)
                await asyncio.sleep(delay)
                
                await self.queues[task.priority].put(task)
                self.stats["retry_tasks"] += 1
                
                logger.info(f"Task {task.id} scheduled for retry {task.retry_count}")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                self.stats["failed_tasks"] += 1
                
                logger.error(f"Task {task.id} failed permanently after {task.max_retries} retries")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queue_sizes = {}
        for priority, queue in self.queues.items():
            queue_sizes[priority.name] = queue.qsize()
        
        active_tasks = len([t for t in self.tasks.values() 
                          if t.status == TaskStatus.PROCESSING])
        
        return {
            "queue_sizes": queue_sizes,
            "active_tasks": active_tasks,
            "total_workers": len(self.workers),
            "is_running": self.is_running,
            "stats": self.stats
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Cleanup old completed/failed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        cleanup_count = 0
        task_ids_to_remove = []
        
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and
                task.completed_at and task.completed_at < cutoff_time):
                task_ids_to_remove.append(task_id)
        
        for task_id in task_ids_to_remove:
            del self.tasks[task_id]
            cleanup_count += 1
        
        logger.info(f"Cleaned up {cleanup_count} old tasks")
        return cleanup_count

# Global queue manager instance
queue_manager = QueueManager()

# Task handler decorators
def task_handler(name: str):
    """Decorator to register task handlers"""
    def decorator(func):
        queue_manager.register_handler(name, func)
        return func
    return decorator

# Example task handlers
@task_handler("video_generation")
async def handle_video_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle video generation task"""
    try:
        # This will be implemented with actual video generation logic
        generation_id = payload.get("generation_id")
        script = payload.get("script")
        
        logger.info(f"Starting video generation for {generation_id}")
        
        # Simulate video generation process
        await asyncio.sleep(2)  # Simulate processing time
        
        return {
            "generation_id": generation_id,
            "status": "completed",
            "video_path": f"/tmp/generated_{generation_id}.mp4",
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise

@task_handler("file_cleanup")
async def handle_file_cleanup(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file cleanup task"""
    try:
        directory = payload.get("directory")
        max_age_hours = payload.get("max_age_hours", 24)
        
        # Import file manager
        from file_manager import file_manager
        
        cleanup_count = await file_manager.cleanup_old_files(directory, max_age_hours)
        
        return {
            "directory": directory,
            "cleanup_count": cleanup_count,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File cleanup failed: {e}")
        raise

@task_handler("analytics_processing")
async def handle_analytics_processing(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle analytics processing task"""
    try:
        event_type = payload.get("event_type")
        data = payload.get("data")
        
        # Process analytics data
        logger.info(f"Processing analytics event: {event_type}")
        
        return {
            "event_type": event_type,
            "processed_data": data,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics processing failed: {e}")
        raise