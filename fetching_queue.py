from typing import Optional
from base_queue import BaseQueue
from data_contracts import FetchingContract
import logging

class FetchingQueue(BaseQueue):
    """Specialized queue for handling FetchingContract messages"""
    
    def __init__(self):
        super().__init__('fetching_queue')
        self.logger = logging.getLogger('fetching_queue')
        
    def enqueue_fetching_contract(self, contract: FetchingContract) -> bool:
        """
        Enqueue a FetchingContract message
        
        Args:
            contract (FetchingContract): The contract to enqueue
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(contract, FetchingContract):
            self.logger.error("Invalid contract type - must be FetchingContract")
            return False
            
        try:
            # Convert contract to dict and enqueue
            return self.enqueue(contract.dict())
        except Exception as e:
            self.logger.error(f"Failed to enqueue FetchingContract: {e}")
            return False
            
    def dequeue_fetching_contract(self) -> Optional[FetchingContract]:
        """
        Dequeue a FetchingContract message
        
        Returns:
            Optional[FetchingContract]: The dequeued contract or None if empty/failed
        """
        message = self.dequeue()
        if not message:
            return None
            
        try:
            # Convert dict back to FetchingContract
            return FetchingContract(**message)
        except Exception as e:
            self.logger.error(f"Failed to parse FetchingContract: {e}")
            return None
            
    def get_queue_status(self) -> dict:
        """
        Get current status of the fetching queue
        
        Returns:
            dict: Queue status information
        """
        return {
            'queue_name': self.queue_name,
            'size': self.size(),
            'connected': self.redis is not None
        }
