"""
Performance Monitoring and Metrics System
Tracks system performance, errors, and resource usage
"""
import asyncio
import logging
import time
import psutil
import os
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import traceback
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    unit: str = ""

@dataclass
class ErrorData:
    """Error data structure"""
    error_type: str
    message: str
    timestamp: datetime
    stack_trace: str
    context: Dict[str, Any]

class PerformanceMonitor:
    """Performance monitoring system"""
    
    def __init__(self):
        self.metrics: List[MetricData] = []
        self.errors: List[ErrorData] = []
        self.max_metrics = 10000
        self.max_errors = 1000
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.active_requests = 0
        
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None,
                     unit: str = ""):
        """Record a metric value"""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            unit=unit
        )
        
        self.metrics.append(metric)
        
        # Cleanup old metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None):
        """Record an error"""
        error_data = ErrorData(
            error_type=type(error).__name__,
            message=str(error),
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc(),
            context=context or {}
        )
        
        self.errors.append(error_data)
        self.error_count += 1
        
        # Cleanup old errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # Network metrics (if available)
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "used_mb": memory_used / (1024 * 1024),
                    "total_mb": memory_total / (1024 * 1024),
                    "process_mb": process_memory.rss / (1024 * 1024)
                },
                "disk": {
                    "percent": disk_percent,
                    "used_gb": disk_used / (1024 * 1024 * 1024),
                    "total_gb": disk_total / (1024 * 1024 * 1024)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        uptime = datetime.now() - self.start_time
        
        # Calculate average response time
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # Calculate error rate
        error_rate = 0
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "average_response_time_ms": avg_response_time * 1000,
            "active_requests": self.active_requests,
            "metrics_count": len(self.metrics),
            "errors_count": len(self.errors)
        }
    
    def get_recent_metrics(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get metrics from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_metrics = [
            {
                "name": metric.name,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "tags": metric.tags,
                "unit": metric.unit
            }
            for metric in self.metrics
            if metric.timestamp >= cutoff_time
        ]
        
        return recent_metrics
    
    def get_recent_errors(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get errors from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_errors = [
            {
                "error_type": error.error_type,
                "message": error.message,
                "timestamp": error.timestamp.isoformat(),
                "context": error.context
            }
            for error in self.errors
            if error.timestamp >= cutoff_time
        ]
        
        return recent_errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        system_metrics = self.get_system_metrics()
        app_metrics = self.get_application_metrics()
        
        # Determine health status
        health_status = "healthy"
        warnings = []
        
        # Check CPU usage
        if system_metrics.get("cpu", {}).get("percent", 0) > 80:
            health_status = "warning"
            warnings.append("High CPU usage")
        
        # Check memory usage
        if system_metrics.get("memory", {}).get("percent", 0) > 85:
            health_status = "warning"
            warnings.append("High memory usage")
        
        # Check disk usage
        if system_metrics.get("disk", {}).get("percent", 0) > 90:
            health_status = "critical"
            warnings.append("High disk usage")
        
        # Check error rate
        if app_metrics.get("error_rate_percent", 0) > 5:
            health_status = "warning"
            warnings.append("High error rate")
        
        return {
            "status": health_status,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat(),
            "system_metrics": system_metrics,
            "application_metrics": app_metrics
        }
    
    def start_background_monitoring(self):
        """Start background monitoring task"""
        async def monitoring_task():
            while True:
                try:
                    # Record system metrics
                    system_metrics = self.get_system_metrics()
                    
                    self.record_metric("cpu_percent", system_metrics.get("cpu", {}).get("percent", 0))
                    self.record_metric("memory_percent", system_metrics.get("memory", {}).get("percent", 0))
                    self.record_metric("disk_percent", system_metrics.get("disk", {}).get("percent", 0))
                    self.record_metric("active_requests", self.active_requests)
                    
                    # Sleep for 30 seconds before next measurement
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Monitoring task error: {e}")
                    await asyncio.sleep(30)
        
        asyncio.create_task(monitoring_task())
        logger.info("Background monitoring started")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorators for automatic monitoring
def monitor_performance(func_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func_name or func.__name__
            
            try:
                performance_monitor.active_requests += 1
                result = await func(*args, **kwargs)
                
                # Record successful execution
                execution_time = time.time() - start_time
                performance_monitor.response_times.append(execution_time)
                performance_monitor.record_metric(
                    f"{function_name}_execution_time",
                    execution_time,
                    {"status": "success"},
                    "seconds"
                )
                
                return result
                
            except Exception as e:
                # Record error
                execution_time = time.time() - start_time
                performance_monitor.record_error(e, {
                    "function": function_name,
                    "args": str(args)[:100],
                    "execution_time": execution_time
                })
                
                performance_monitor.record_metric(
                    f"{function_name}_execution_time",
                    execution_time,
                    {"status": "error"},
                    "seconds"
                )
                
                raise
                
            finally:
                performance_monitor.active_requests -= 1
                performance_monitor.request_count += 1
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func_name or func.__name__
            
            try:
                performance_monitor.active_requests += 1
                result = func(*args, **kwargs)
                
                # Record successful execution
                execution_time = time.time() - start_time
                performance_monitor.response_times.append(execution_time)
                performance_monitor.record_metric(
                    f"{function_name}_execution_time",
                    execution_time,
                    {"status": "success"},
                    "seconds"
                )
                
                return result
                
            except Exception as e:
                # Record error
                execution_time = time.time() - start_time
                performance_monitor.record_error(e, {
                    "function": function_name,
                    "args": str(args)[:100],
                    "execution_time": execution_time
                })
                
                performance_monitor.record_metric(
                    f"{function_name}_execution_time",
                    execution_time,
                    {"status": "error"},
                    "seconds"
                )
                
                raise
                
            finally:
                performance_monitor.active_requests -= 1
                performance_monitor.request_count += 1
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def monitor_endpoint(endpoint_name: str = None):
    """Decorator to monitor API endpoint performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            name = endpoint_name or func.__name__
            
            try:
                performance_monitor.active_requests += 1
                result = await func(*args, **kwargs)
                
                # Record successful request
                response_time = time.time() - start_time
                performance_monitor.response_times.append(response_time)
                performance_monitor.record_metric(
                    f"endpoint_{name}_response_time",
                    response_time,
                    {"status": "success"},
                    "seconds"
                )
                
                return result
                
            except Exception as e:
                # Record error
                response_time = time.time() - start_time
                performance_monitor.record_error(e, {
                    "endpoint": name,
                    "response_time": response_time
                })
                
                performance_monitor.record_metric(
                    f"endpoint_{name}_response_time",
                    response_time,
                    {"status": "error"},
                    "seconds"
                )
                
                raise
                
            finally:
                performance_monitor.active_requests -= 1
                performance_monitor.request_count += 1
        
        return wrapper
    return decorator