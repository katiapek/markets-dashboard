from typing import Optional, Dict, Any
from base_queue import BaseQueue
from data_contracts import AnalysisContract
import logging
import json
import pandas as pd

class AnalysisQueue(BaseQueue):
    """Specialized queue for handling AnalysisContract messages with enhanced debugging"""
    
    def __init__(self):
        super().__init__('analysis_queue')
        self.logger = logging.getLogger('analysis_queue')
        
    def enqueue_analysis_contract(self, contract: AnalysisContract) -> bool:
        """
        Enqueue an AnalysisContract message
        
        Args:
            contract (AnalysisContract): The contract to enqueue
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(contract, AnalysisContract):
            self.logger.error("Invalid contract type - must be AnalysisContract")
            return False
            
        try:
            # Convert contract to dict with proper DataFrame serialization
            contract_dict = contract.to_dict()
            # Ensure the processed_data is properly serialized
            if 'processed_data' in contract_dict and isinstance(contract_dict['processed_data'], dict):
                # Convert numpy arrays to lists
                if 'data' in contract_dict['processed_data']:
                    contract_dict['processed_data']['data'] = [
                        [float(item) if isinstance(item, (np.floating, float)) else item 
                         for item in row] 
                        for row in contract_dict['processed_data']['data']
                    ]
                contract_dict['processed_data'] = json.dumps(contract_dict['processed_data'])
            return self.enqueue(contract_dict)
        except Exception as e:
            self.logger.error(f"Failed to enqueue AnalysisContract: {e}")
            return False
            
    def dequeue_analysis_contract(self) -> Optional[AnalysisContract]:
        """
        Dequeue an AnalysisContract message
        
        Returns:
            Optional[AnalysisContract]: The dequeued contract or None if empty/failed
        """
        message = self.dequeue()
        if not message:
            return None
            
        try:
            # Convert dict back to AnalysisContract
            if 'processed_data' in message:
                if isinstance(message['processed_data'], str):
                    # Deserialize the processed_data if it was serialized as a string
                    message['processed_data'] = json.loads(message['processed_data'])
                if isinstance(message['processed_data'], dict) and message['processed_data'].get('_is_dataframe'):
                    # Convert back to DataFrame
                    message['processed_data'] = pd.DataFrame(**{
                        'data': message['processed_data']['data'],
                        'index': message['processed_data']['index'],
                        'columns': message['processed_data']['columns']
                    })
                    if 'index' in message['processed_data']:
                        message['processed_data'] = message['processed_data'].set_index('index')
            return AnalysisContract(**message)
        except Exception as e:
            self.logger.error(f"Failed to parse AnalysisContract: {e}")
            return None
            
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current status of the analysis queue
        
        Returns:
            dict: Queue status information including:
                - queue_name: Name of the queue
                - size: Number of items in queue
                - connected: Whether connected to Redis
                - last_error: Last error message (if any)
        """
        status = {
            'queue_name': self.queue_name,
            'size': self.size(),
            'connected': self.redis is not None,
            'last_error': self.last_error if hasattr(self, 'last_error') else None
        }
        
        # Add detailed queue info if connected
        if self.redis is not None:
            try:
                status.update({
                    'memory_usage': self.redis.info('memory')['used_memory_human'],
                    'queue_memory': self.redis.memory_usage(self.queue_name),
                    'pending_messages': self.redis.xlen(self.queue_name)
                })
            except Exception as e:
                self.logger.error(f"Error getting queue details: {e}")
                status['queue_details_error'] = str(e)
                
        return status

    def clear_queue(self) -> bool:
        """
        Clear all messages from the analysis queue
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.redis.delete(self.queue_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear analysis queue: {e}")
            return False

    def peek_next_contract(self) -> Optional[Dict[str, Any]]:
        """
        Peek at the next contract in the queue without removing it
        
        Returns:
            Optional[Dict]: The next contract data or None if empty
        """
        try:
            messages = self.redis.xrange(self.queue_name, count=1)
            if messages:
                return json.loads(messages[0][1]['data'])
            return None
        except Exception as e:
            self.logger.error(f"Failed to peek at next contract: {e}")
            return None
