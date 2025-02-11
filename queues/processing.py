import pandas as pd
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
            
            # Ensure raw_data is properly serialized
            if hasattr(contract, 'raw_data') and contract.raw_data is not None:
                if isinstance(contract.raw_data, pd.DataFrame):
                    contract_dict['raw_data'] = contract.raw_data.to_dict(orient='records')
            
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
            if 'raw_data' in message and isinstance(message['raw_data'], list):
                # Convert raw_data back to DataFrame
                message['raw_data'] = pd.DataFrame(message['raw_data'])
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
