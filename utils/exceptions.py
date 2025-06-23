# Custom Exceptions
class BulkServiceError(Exception):
    pass


class WalletError(BulkServiceError):
    pass


class GSheetUpdateError(BulkServiceError):
    pass
