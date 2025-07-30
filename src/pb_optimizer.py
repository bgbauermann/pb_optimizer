import asyncio
import sqlite3
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from datetime import datetime
from src.data.data_access_layer import DataAccessLayer
from src.data.initialize_data import initialize_mock_data


class PBOptimizer:

    def __init__(self, data_access_layer: DataAccessLayer):
        self.dao = data_access_layer

    async def allocate_trade_list(self, as_of_date: datetime, trade_list: pd.DataFrame) -> pd.DataFrame:
        """
        Return an array with the allocation of the trade_list by PB
        :param as_of_date:
        :param trade_list:
        :return:
        """
        # Get data
        positions = self.dao.get_positions(as_of_date)
        sec_coefficients = self.dao.get_security_pb_coefficients(as_of_date)
        normalized_coefficients = self.normalize_coefficients(sec_coefficients)
        optimization_priorities = self.dao.get_optimization_priorities()
        optimization_priorities = optimization_priorities['weight'].values
        security_index = self.get_security_universe(positions, normalized_coefficients, trade_list)
        # Call function to format inputs for optimization
        values, coefficients, trade = self.format_optimization_inputs(security_index, positions,
                                                                      normalized_coefficients, trade_list)
        allocations_shape = values.shape
        allocations_flat = np.zeros(shape=allocations_shape).reshape(-1)

        # Individual allocations must be between 0 and 1
        bounds = [(0, 1) for _ in range(allocations_flat.shape[0])]

        # Create constraints
        # TODO: This should be enhanced and defined somewhere else
        def constraint_sum_col(allocations_flat, col, shape, target):
            return sum(allocations_flat[i * shape[1] + col] for i in range(shape[0])) - target
        constraints = []
        for i in range(allocations_shape[1]):
            target = 1 if trade[i] > 0 else 0
            constraints.append({'type': 'eq', 'fun': constraint_sum_col, 'args': (i, allocations_shape, target)})

        result = minimize(self.calculate_metrics, allocations_flat, args=(values, coefficients, optimization_priorities, trade),
                          constraints=constraints, bounds=bounds)

        # Format results
        allocations = result.x.reshape(allocations_shape[0], allocations_shape[1])
        pb_codes = sec_coefficients['counterparty'].unique()
        allocated_trade = self.format_results(allocations, trade, pb_codes, security_index)
        return allocated_trade

    def get_security_universe(self, positions: pd.DataFrame, coefficients: pd.DataFrame, trade: pd.DataFrame) -> pd.Index:
        """
        Return the uinverse of securities to be used in the optimization
        :param positions:
        :param coefficients:
        :param trade:
        :return:
        """
        security_universe = pd.concat([trade['security_id'], positions['security_id'],
                                       coefficients['security_id']]).unique()
        security_index = pd.Index(security_universe)
        return security_index

    def format_optimization_inputs(self, security_index: pd.Index, positions: pd.DataFrame, coefficients: pd.DataFrame,
                                   trade: pd.DataFrame) -> tuple:
        """
        Create matrices to be used in the optimization
        :param security_index:
        :param positions:
        :param coefficients:
        :param optimization_priorities:
        :param trade:
        :return:
        """
        # Reindex trade list
        trade = trade.loc[:, ['security_id', 'market_value']]
        trade = trade.set_index('security_id').reindex(security_index).fillna(0)
        trade = trade['market_value'].values
        # Iterate through PB accounts to build required matrices
        pb_codes = coefficients['counterparty'].unique()
        coefs = []
        vals = []
        for pb in pb_codes:
            pb_positions = positions.loc[positions['counterparty'] == pb, ['security_id', 'market_value']]
            pb_positions.set_index('security_id', inplace=True)
            pb_positions = pb_positions.reindex(security_index).fillna(0)
            coefficients_pb = coefficients.loc[coefficients['counterparty'] == pb, ['security_id', 'metric_name', 'coefficient_value']]
            coefficients_pb = coefficients_pb.set_index(['metric_name', 'security_id']).unstack('security_id')
            coefficients_pb = coefficients_pb['coefficient_value']
            coefficients_pb = coefficients_pb.reindex(columns=security_index)
            coefs.append(coefficients_pb)
            vals.append(pb_positions['market_value'])
        coefficients_matrix = np.stack(coefs)
        values_matrix = np.stack(vals)
        return values_matrix, coefficients_matrix, trade

    def calculate_metrics(self, allocation_vector: np.ndarray, positions_matrix: np.ndarray, coefficients_matrix: np.ndarray,
                          optimization_priorities: np.ndarray, trade: np.ndarray) -> float:
        allocation_matrix = allocation_vector.reshape(positions_matrix.shape[0], positions_matrix.shape[1])
        values_matrix = positions_matrix + allocation_matrix * trade
        metrics = np.einsum('m,pms,ps->',optimization_priorities, coefficients_matrix, values_matrix)
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

    def format_results(self, allocations: np.ndarray, trade: np.ndarray, pb_codes, security_universe) -> dict:
        allocations = np.round(allocations, decimals=2).transpose()
        allocations_df = pd.DataFrame(data=allocations, index=security_universe, columns=pb_codes)
        trade_allocations = allocations_df.mul(trade, axis=0)
        trade_allocations = trade_allocations.loc[~(trade_allocations == 0).all(axis=1)]
        return trade_allocations

if __name__ == "__main__":
    sql_client = sqlite3.connect('portfolio.db')
    initialize_mock_data(sql_client)
    data_access_layer = DataAccessLayer(sql_client)
    optimizer = PBOptimizer(data_access_layer)
    as_of_date = datetime(2024,1,15)
    trade_list = pd.DataFrame({'security_id': [1001, 1002], 'market_value': [50000, 10000]})
    asyncio.run(optimizer.allocate_trade_list(as_of_date, trade_list))