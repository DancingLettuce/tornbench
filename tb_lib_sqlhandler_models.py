"""This filename is tb_lib_sqlhandler_models.py."""

# setup alembic

"""In your terminal, run the initialization command. This creates an alembic.ini file and an alembic/ folder.
alembic init alembic

4. Create and Run the Migration
Now that Alembic knows about your model and your database credentials, let's create the table.
Generate the migration script (Django's makemigrations):
alembic revision --autogenerate -m "create my_table"

For critical existing databases, this is the safest workflow:
    Autogenerate the Python script (Online): alembic revision --autogenerate -m "create my_table" (This requires an online connection to compare your models to the DB).
    Review the Python script: Open alembic/versions/xxxx_create_my_table.py and ensure there are no drop_table commands.
    Generate the SQL (Offline): alembic upgrade head --sql > migration.sql
    Review the SQL: Open migration.sql and verify exactly what will happen.
    Execute: If the SQL is perfect, you can either run the migration.sql script manually via sqlcmd / DBeaver, OR you can safely run alembic upgrade head (Online) knowing exactly what it will do.

#pip install sqlalchemy 
## alembic pyodbc tomli
# check driver installed with cat /etc/odbcinst.ini

"""

from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, String, JSON, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.mssql import DATETIMEOFFSET # Import the specific MS SQL type


# 1. Define the Base class (Your equivalent of models.Model in Django)
class Base(DeclarativeBase):
    pass


class FactionBasic(Base):
    __tablename__ = "torn_factionbasic"
    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Datetimes
    created_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    updated_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    faction_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    tag: Mapped[Optional[str]] = mapped_column(String(200))
    leader_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    co_leader_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    co_leader_name: Mapped[Optional[str]] = mapped_column(String(200))
    is_destroyed: Mapped[Optional[str]] = mapped_column(String(20))
    update_on_viafactionbasicapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viaplayerprofileapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viafactionsearchapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viafactionmembersapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)


