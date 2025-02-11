from typing import Optional
from base_queue import BaseQueue
from data_contracts import VisualizationContract
import logging

class VisualizationQueue(BaseQueue):
    """Specialized queue for handling VisualizationContract messages"""
    
    def __init__(self):
        super().__init__('visualization_queue')
        self.logger = logging.getLogger('visualization_queue')
        
    def enqueue_visualization_contract(self, contract: VisualizationContract) -> bool:
        """
        Enqueue a VisualizationContract message
        
        Args:
            contract (VisualizationContract): The contract to enqueue
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(contract, VisualizationContract):
            self.logger.error("Invalid contract type - must be VisualizationContract")
            return False
            
        try:
            # Convert contract to dict and enqueue
            return self.enqueue(contract.dict())
        except Exception as e:
            self.logger.error(f"Failed to enqueue VisualizationContract: {e}")
            return False
            
    def dequeue_visualization_contract(self) -> Optional[VisualizationContract]:
        """
        Dequeue a VisualizationContract message
        
        Returns:
            Optional[VisualizationContract]: The dequeued contract or None if empty/failed
        """
        message = self.dequeue()
        if not message:
            return None
            
        try:
            # Convert dict back to VisualizationContract
            return VisualizationContract(**message)
        except Exception as e:
            self.logger.error(f"Failed to parse VisualizationContract: {e}")
            return None
            
    def get_queue_status(self) -> dict:
        """
        Get current status of the visualization queue
        
        Returns:
            dict: Queue status information
        """
        return {
            'queue_name': self.queue_name,
            'size': self.size(),
            'connected': self.redis is not None
        }
