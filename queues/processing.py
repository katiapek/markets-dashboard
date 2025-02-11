from typing import Optional
from .base import BaseQueue
from data_contracts import ProcessingContract
import logging

class ProcessingQueue(BaseQueue):
    """Specialized queue for handling ProcessingContract messages"""
    
    def __init__(self):
        super().__init__('processing_queue')
        self.logger = logging.getLogger('processing_queue')
        
    def enqueue_processing_contract(self, contract: ProcessingContract) -> bool:
        """
        Enqueue a ProcessingContract message
        
        Args:
            contract (ProcessingContract): The contract to enqueue
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(contract, ProcessingContract):
            self.logger.error("Invalid contract type - must be ProcessingContract")
            return False
            
        try:
            # Convert contract to dict with proper DataFrame serialization
            contract_dict = contract.to_dict()
            return self.enqueue(contract_dict)
        except Exception as e:
            self.logger.error(f"Failed to enqueue ProcessingContract: {e}")
            return False
            
    def dequeue_processing_contract(self) -> Optional[ProcessingContract]:
        """
        Dequeue a ProcessingContract message
        
        Returns:
            Optional[ProcessingContract]: The dequeued contract or None if empty/failed
        """
        message = self.dequeue()
        if not message:
            return None
            
        try:
            # Convert dict back to ProcessingContract
            return ProcessingContract(**message)
        except Exception as e:
            self.logger.error(f"Failed to parse ProcessingContract: {e}")
            return None
            
    def get_queue_status(self) -> dict:
        """
        Get current status of the processing queue
        
        Returns:
            dict: Queue status information
        """
        return {
            'queue_name': self.queue_name,
            'size': self.size(),
            'connected': self.redis is not None
        }
