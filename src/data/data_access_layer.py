import sqlite3
import pandas as pd
from typing import Optional
from datetime import datetime

class DataAccessLayer:

    def __init__(self, db_client):
        self.db = db_client.cursor()

    def get_positions(self, as_of_date: datetime, portfolio: Optional[list] = None) -> pd.DataFrame:
        """
        Return the positions
        :param as_of_date:
        :param portfolio: [Optional] list of portfolios
        :return: dataframe with position data
        """
        if portfolio:
            portfolio_filter = " AND portfolio IN ({})".format(','.join(['?' for _ in portfolio]))
            params = [as_of_date.strftime('%Y-%m-%d')] + portfolio
        else:
            portfolio_filter = ""
            params = [as_of_date.strftime('%Y-%m-%d')]
            
        query = f"SELECT * FROM positions WHERE as_of_date = ?{portfolio_filter}"
        return pd.read_sql(query, self.db.connection, params=params)

    def get_security_pb_coefficients(self, as_of_date: datetime, portfolio: Optional[list] = None,
                                     security_id: Optional[list] = None) -> pd.DataFrame:
        conditions = ["as_of_date = ?"]
        params = [as_of_date.strftime('%Y-%m-%d')]
        
        if portfolio:
            conditions.append("portfolio IN ({})".format(','.join(['?' for _ in portfolio])))
            params.extend(portfolio)
            
        if security_id:
            conditions.append("security_id IN ({})".format(','.join(['?' for _ in security_id])))
            params.extend(security_id)
            
        query = f"SELECT * FROM pb_coefficients WHERE {' AND '.join(conditions)}"
        return pd.read_sql(query, self.db.connection, params=params)