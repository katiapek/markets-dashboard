from typing import Optional, Dict, Any
from .base import BaseQueue
from data_contracts import VisualizationContract
import logging
import json

class VisualizationQueue(BaseQueue):
    """Specialized queue for handling VisualizationContract messages with enhanced debugging"""
    
    def __init__(self):
        super().__init__('visualization_queue')
        self.logger = logging.getLogger('visualization_queue')
        self.logger.setLevel(logging.DEBUG)
        
    def enqueue_visualization_contract(self, contract: VisualizationContract) -> bool:
        """
        Enqueue a VisualizationContract message with enhanced error handling and debugging
        
        Args:
            contract (VisualizationContract): The contract to enqueue
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(contract, VisualizationContract):
            self.logger.error("Invalid contract type - must be VisualizationContract")
            return False
            
        try:
            # Convert contract to dict with proper serialization
            contract_dict = contract.to_dict()
            
            # Serialize recursively to handle nested objects
            def serialize_recursive(obj):
                if isinstance(obj, dict):
                    return {k: serialize_recursive(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [serialize_recursive(item) for item in obj]
                elif hasattr(obj, 'to_dict'):
                    return obj.to_dict()
                else:
                    return obj
                    
            serialized = serialize_recursive(contract_dict)
            
            # Enqueue the serialized message
            success = self.enqueue(serialized)
            if success:
                self.logger.debug(f"Successfully enqueued VisualizationContract for {contract.analysis_results.get('market', 'unknown')}")
            else:
                self.logger.error("Failed to enqueue VisualizationContract")
            return success
        except Exception as e:
            self.logger.error(f"Failed to enqueue VisualizationContract: {str(e)}", exc_info=True)
            return False
            
    def dequeue_visualization_contract(self) -> Optional[VisualizationContract]:
        """
        Dequeue a VisualizationContract message with enhanced error handling
        
        Returns:
            Optional[VisualizationContract]: The dequeued contract or None if empty/failed
        """
        try:
            message = self.dequeue()
            if not message:
                self.logger.debug("Queue is empty")
                return None
                
            # Deserialize the message
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            if isinstance(message, str):
                message = json.loads(message)
                
            # Create contract from deserialized data
            contract = VisualizationContract.from_dict(message)
            self.logger.debug(f"Successfully dequeued VisualizationContract")
            return contract
        except Exception as e:
            self.logger.error(f"Failed to dequeue VisualizationContract: {str(e)}", exc_info=True)
            return None
            
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get detailed status of the visualization queue
        
        Returns:
            dict: Queue status information including:
                - queue_name
                - size
                - connected
                - last_error (if any)
        """
        status = {
            'queue_name': self.queue_name,
            'size': self.size(),
            'connected': self.redis is not None,
            'last_error': None
        }
        
        try:
            # Add additional diagnostic information
            status['memory_usage'] = self.redis.info().get('used_memory', 0)
            status['pending_messages'] = self.redis.llen(self.queue_name)
        except Exception as e:
            status['last_error'] = str(e)
            self.logger.error(f"Error getting queue status: {str(e)}")
            
        return status
