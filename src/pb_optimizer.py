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
        optimization_priorities = pd.DataFrame()
        allocations = pd.DataFrame(1, index=[1001], columns=['allocation'])
        metrics = self.calculate_metrics(positions, normalized_coefficients, optimization_priorities,
                                         trade_list, allocations)
        allocations = pd.DataFrame()
        return allocations

    def calculate_metrics(self, positions: pd.DataFrame, coefficients: pd.DataFrame, optimization_priorities: pd.DataFrame,
                          trade: pd.DataFrame, allocations: pd.DataFrame) -> pd.DataFrame:
        pb_codes = coefficients['counterparty'].unique()
        # Get universe of security to ensure same matrix dimensions for different pb accounts
        security_universe = pd.concat([trade['security_id'], positions['security_id'], coefficients['security_id']]).unique()
        security_index = pd.Index(security_universe)
        trade = trade.loc[:, ['security_id', 'market_value']]
        trade = trade.set_index('security_id').reindex(security_index).fillna(0)
        # Iterate through PB accounts to build required matrices
        for pb in pb_codes:
            pb_positions = positions.loc[positions['counterparty'] == pb, ['security_id', 'market_value']]
            pb_positions.set_index('security_id', inplace=True)
            pb_positions = pb_positions.reindex(security_index).fillna(0)
            final_val = pb_positions['market_value'] + trade['market_value'] * allocations['allocation']
            coefficients_pb = coefficients.loc[coefficients['counterparty'] == pb, ['security_id', 'metric_name', 'coefficient_value']]
            coefficients_pb = coefficients_pb.set_index(['metric_name', 'security_id']).unstack('security_id')
            coefficients_pb = coefficients_pb['coefficient_value']
            coefficients_pb = coefficients_pb.reindex(columns=pb_positions.index)
        metrics = np.einsum('ij,j->i', coefficients_pb.values, final_val.values)
        return metrics

    def normalize_coefficients(self, pb_coefficients: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize pb coefficients so optimization is not dominated by coefficients with large magnitude
        :param pb_coefficients:
        :return:
        """
        group_cols = ['counterparty', 'metric_name']
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
    trade_list = pd.DataFrame({'security_id': [1001], 'market_value': 1500})
    asyncio.run(optimizer.allocate_trade_list(as_of_date, trade_list))