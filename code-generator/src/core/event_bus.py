"""
CORE COMPONENT: Handler Event Bus
=================================
Event-driven communication between handlers
"""
shikharprakash shikharprakash
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class HandlerEvent:
    """Structured event for handler communication"""
    event_id: str
    event_type: str
    data: Dict[str, Any]
    source_handler: str
    timestamp: str
    correlation_id: str = None

class HandlerEventBus:
    """Event bus for handler coordination and communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[HandlerEvent] = []
        self.active_correlations: Dict[str, List[str]] = {}  # correlation_id -> event_ids
        self.max_history_size = 1000
    
    def subscribe(self, event_type: str, callback: Callable, handler_name: str = "unknown"):
        """Subscribe to specific event types"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
        logger.info(f"📡 Handler '{handler_name}' subscribed to event: {event_type}")
    
    async def publish(self, event_type: str, data: Dict[str, Any], 
                     source_handler: str = "system", correlation_id: str = None):
        """Publish event to all subscribers"""
        
        # Create structured event
        event = HandlerEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
            source_handler=source_handler,
            timestamp=datetime.utcnow().isoformat(),
            correlation_id=correlation_id or str(uuid.uuid4())
        )
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Track correlations
        if event.correlation_id not in self.active_correlations:
            self.active_correlations[event.correlation_id] = []
        self.active_correlations[event.correlation_id].append(event.event_id)
        
        logger.info(f"📢 Publishing event: {event_type} from {source_handler}")
        
        # Notify subscribers asynchronously
        subscribers = self.subscribers.get(event_type, [])
        if subscribers:
            tasks = []
            for callback in subscribers:
                task = asyncio.create_task(self._safe_callback(callback, event))
                tasks.append(task)
            
            # Wait for all callbacks to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            logger.warning(f"⚠️ No subscribers for event: {event_type}")
    
    async def _safe_callback(self, callback: Callable, event: HandlerEvent):
        """Execute callback with error handling"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(f"❌ Event callback failed for {event.event_type}: {e}")
    
    def get_event_history(self, event_types: List[str] = None, 
                         correlation_id: str = None, 
                         source_handler: str = None) -> List[HandlerEvent]:
        """Get filtered event history"""
        filtered_events = self.event_history
        
        if event_types:
            filtered_events = [e for e in filtered_events if e.event_type in event_types]
        
        if correlation_id:
            filtered_events = [e for e in filtered_events if e.correlation_id == correlation_id]
        
        if source_handler:
            filtered_events = [e for e in filtered_events if e.source_handler == source_handler]
        
        return filtered_events
    
    def get_correlation_events(self, correlation_id: str) -> List[HandlerEvent]:
        """Get all events for a specific correlation ID"""
        return [e for e in self.event_history if e.correlation_id == correlation_id]
    
    def wait_for_event(self, event_type: str, timeout: int = 30) -> asyncio.Future:
        """Wait for specific event with timeout"""
        future = asyncio.Future()
        
        def callback(event: HandlerEvent):
            if not future.done():
                future.set_result(event)
        
        self.subscribe(event_type, callback, "wait_for_event")
        
        # Set timeout
        asyncio.create_task(self._timeout_future(future, timeout))
        
        return future
    
    async def _timeout_future(self, future: asyncio.Future, timeout: int):
        """Timeout handler for wait_for_event"""
        await asyncio.sleep(timeout)
        if not future.done():
            future.set_exception(asyncio.TimeoutError(f"Event wait timeout after {timeout}s"))
    
    def create_correlation_id(self) -> str:
        """Create new correlation ID for tracking related events"""
        return str(uuid.uuid4())
    
    def get_handler_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        handler_counts = {}
        event_type_counts = {}
        
        for event in self.event_history:
            # Count by handler
            if event.source_handler not in handler_counts:
                handler_counts[event.source_handler] = 0
            handler_counts[event.source_handler] += 1
            
            # Count by event type
            if event.event_type not in event_type_counts:
                event_type_counts[event.event_type] = 0
            event_type_counts[event.event_type] += 1
        
        return {
            "total_events": len(self.event_history),
            "active_correlations": len(self.active_correlations),
            "subscriber_count": sum(len(subs) for subs in self.subscribers.values()),
            "handler_event_counts": handler_counts,
            "event_type_counts": event_type_counts,
            "recent_events": [
                {"type": e.event_type, "source": e.source_handler, "time": e.timestamp}
                for e in self.event_history[-5:]
            ]
        }