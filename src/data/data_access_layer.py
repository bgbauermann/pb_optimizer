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
        query = f"""
        SELECT * FROM positions 
        WHERE positions.as_of_date = {as_of_date} AND positions.portfolio = {portfolio};"""
        return pd.read_sql(query, self.db)

    def get_security_pb_coefficients(self, as_of_date: datetime, portfolio: Optional[list] = None,
                                     security_id: Optional[list] = None) -> pd.DataFrame:
        query = f""" SELECT * FROM pb_coefficients pbc
                    WHERE pbc.as_of_date = {as_of_date} AND pbc.portfolio = {portfolio} 
                    AND pbc.security_id = {security_id};"""
        return pd.read_sql(query, self.db)