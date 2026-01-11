from __future__ import annotations
from data_sources.mssql_orm_source import SqlAlchemyMSSQLDataSource
from data_sources.const_source import ConstDataSource
from data_sources.csv_source import CSVDataSource
from data_sources.sqlite_source import SQLiteDataSource


class DataSourceFactory:
    @staticmethod
    def create(kind: str, path: str):
        kind = (kind or "").strip().lower()

        if kind == "const":
            return ConstDataSource()

        if kind == "csv":
            return CSVDataSource(folder=path)

        if kind == "sqlite":
            return SQLiteDataSource(db_path=path)
        if kind == "mssql_orm":
            return SqlAlchemyMSSQLDataSource(sqlalchemy_url=path)

        raise ValueError(f"Unknown data source kind: {kind}")
