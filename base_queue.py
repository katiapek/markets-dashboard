import redis
import json
from typing import Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

class BaseQueue(ABC):
    """Base class for message queues with common functionality"""
    
    def __init__(self, queue_name: str, redis_host: str = 'localhost', redis_port: int = 6379):
        """
        Args:
            queue_name (str): Name of the queue
            redis_host (str): Redis server host
            redis_port (int): Redis server port
        """
        self.queue_name = queue_name
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis = None
        self.logger = self._setup_logger()
        self._connect_redis()
        
    def _setup_logger(self):
        """Configure logger for the queue"""
        logger = logging.getLogger(f"{self.queue_name}_queue")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
        
    def _connect_redis(self):
        """Establish connection to Redis server"""
        try:
            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                socket_connect_timeout=1,  # 1 second timeout
                socket_timeout=1,
                decode_responses=True
            )
            # Test the connection
            self.redis.ping()
            self.logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
        except redis.ConnectionError as e:
            self.logger.error(f"Could not connect to Redis: {e}")
            self.redis = None
            
    def enqueue(self, message: Dict[str, Any]) -> bool:
        """
        Add a message to the queue
        
        Args:
            message (dict): Message to enqueue
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            self.logger.error("Cannot enqueue - Redis connection not available")
            return False
            
        try:
            serialized = json.dumps(message)
            self.redis.rpush(self.queue_name, serialized)
            self.logger.debug(f"Enqueued message to {self.queue_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to enqueue message: {e}")
            return False
            
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get and remove a message from the queue
        
        Returns:
            Optional[dict]: Dequeued message or None if empty/failed
        """
        if not self.redis:
            self.logger.error("Cannot dequeue - Redis connection not available")
            return None
            
        try:
            serialized = self.redis.lpop(self.queue_name)
            if serialized:
                self.logger.debug(f"Dequeued message from {self.queue_name}")
                return json.loads(serialized)
            return None
        except Exception as e:
            self.logger.error(f"Failed to dequeue message: {e}")
            return None
            
    def size(self) -> int:
        """
        Get current queue size
        
        Returns:
            int: Number of messages in queue
        """
        if not self.redis:
            self.logger.error("Cannot get queue size - Redis connection not available")
            return 0
            
        try:
            return self.redis.llen(self.queue_name)
        except Exception as e:
            self.logger.error(f"Failed to get queue size: {e}")
            return 0
            
    def clear(self) -> bool:
        """
        Clear all messages from the queue
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            self.logger.error("Cannot clear queue - Redis connection not available")
            return False
            
        try:
            self.redis.delete(self.queue_name)
            self.logger.info(f"Cleared queue {self.queue_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear queue: {e}")
            return False
