import asyncio
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from src.data.data_access_layer import DataAccessLayer
from src.data.initialize_data import initialize_mock_data


class PBOptimizer:

    def __init__(self, data_access_layer: DataAccessLayer):
        self.dao = data_access_layer

    async def allocate_trade_list(self, as_of_date: datetime, trade_list: pd.DataFrame) -> pd.DataFrame:
        positions = self.dao.get_positions(as_of_date)
        sec_coefficients = self.dao.get_security_pb_coefficients(as_of_date)
        normalized_coefficients = self.normalize_coefficients(sec_coefficients)
        metrics = self.calculate_metrics(positions, normalized_coefficients, "PB_A")
        allocations = pd.DataFrame()
        return allocations

    def calculate_metrics(self, positions: pd.DataFrame, coefficients: pd.DataFrame, pb_code: str) -> pd.DataFrame:
        pb_positions = positions.loc[positions['counterparty'] == pb_code, ['security_id', 'market_value']]
        pb_positions.set_index('security_id', inplace=True)
        coefficients_pb = coefficients.loc[coefficients['counterparty'] == pb_code, ['security_id', 'coefficient_name', 'coefficient_value']]
        coefficients_pb = coefficients_pb.set_index(['coefficient_name', 'security_id']).unstack('security_id')
        coefficients_pb = coefficients_pb['coefficient_value']
        coefficients_pb = coefficients_pb.reindex(columns=pb_positions.index)
        metrics = coefficients_pb.dot(pb_positions)
        return metrics

    def normalize_coefficients(self, pb_coefficients: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize pb coefficients so optimization is not dominated by coefficients with large magnitude
        :param pb_coefficients:
        :return:
        """
        group_cols = ['counterparty', 'coefficient_name']
        pb_coefficients['min_val'] = pb_coefficients.groupby(group_cols)['coefficient_value'].transform('min')
        pb_coefficients['max_val'] = pb_coefficients.groupby(group_cols)['coefficient_value'].transform('max')
        # Avoid divide by zero (if min = max)
        pb_coefficients['coefficient_value'] = ((pb_coefficients['coefficient_value'] - pb_coefficients['min_val']) /
                                         (pb_coefficients['max_val'] - pb_coefficients['min_val']).replace(0, 1))
        pb_coefficients = pb_coefficients.drop(columns=['min_val', 'max_val'])
        return pb_coefficients

if __name__ == "__main__":
    sql_client = sqlite3.connect('portfolio.db')
    initialize_mock_data(sql_client)
    data_access_layer = DataAccessLayer(sql_client)
    optimizer = PBOptimizer(data_access_layer)
    as_of_date = datetime(2024,1,15)
    trade_list = pd.DataFrame()
    asyncio.run(optimizer.allocate_trade_list(as_of_date, trade_list))