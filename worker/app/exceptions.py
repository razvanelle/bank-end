class TransactionError(Exception):
    """
    Custom exceptions base class for handling various processor errors.
    """
    def __init__(self, message, transaction_id=None):
        super().__init__(message)
        self.transaction_id = transaction_id
        self.message = message

    def __str__(self):
        base_message = super().__str__()
        if self.transaction_id:
            return f"Transaction ID: {self.transaction_id} - {base_message}"
        return base_message
    
class RetryTransactionError(TransactionError):
    """
    Base Error for processing transaction, results in a requeue (NAck)
    """
    pass

class ProcessingError(TransactionError):
    """
    Base Error processing transaction, results in moving to Eerror queue (Ack)
    """
    pass

class RejectTransactionError(TransactionError):
    """
    Base Error for handling reasons for rejecting transactions (Ack)
    """
    pass

class WalletAuthorizationError(RejectTransactionError):
    """
    Specific Error for Low balance - Reject (Ack)
    """
    pass


