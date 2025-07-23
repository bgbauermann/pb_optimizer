import pandas as pd
from datetime import datetime
from src.data.data_access_layer import DataAccessLayer

class PBOptimizer:

    def __init__(self, data_access_layer: DataAccessLayer):
        self.dao = data_access_layer

    async def allocate_trade_list(self, as_of_date: datetime, trade_list: pd.DataFrame) -> pd.DataFrame:
        positions = self.dao.get_positions(as_of_date)
        sec_coefficients = self.dao.get_security_pb_coefficients(as_of_date)

        allocations = pd.DataFrame()
        return allocations
