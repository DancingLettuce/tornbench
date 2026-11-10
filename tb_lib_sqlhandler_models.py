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
    latest_factionmembersapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)

class PlayerProfile(Base):
    __tablename__ = "torn_playerprofile"
    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Datetimes
    created_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    updated_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    name: Mapped[Optional[str]] = mapped_column(String(200))
    player_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    level: Mapped[Optional[int]] = mapped_column(BigInteger)
    signup_truedate: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    age: Mapped[Optional[int]] = mapped_column(BigInteger)
    friends: Mapped[Optional[int]] = mapped_column(BigInteger)
    enemies: Mapped[Optional[int]] = mapped_column(BigInteger)
    karma: Mapped[Optional[int]] = mapped_column(BigInteger)
    forum_posts: Mapped[Optional[int]] = mapped_column(BigInteger)
    role: Mapped[Optional[str]] = mapped_column(String(200))
    life_current: Mapped[Optional[int]] = mapped_column(BigInteger)
    life_maximum: Mapped[Optional[int]] = mapped_column(BigInteger)
    status_description: Mapped[Optional[str]] = mapped_column(String(200))
    status_details: Mapped[Optional[str]] = mapped_column(String(200))
    status_state: Mapped[Optional[str]] = mapped_column(String(200))
    status_color: Mapped[Optional[str]] = mapped_column(String(200))
    status_until: Mapped[Optional[int]] = mapped_column(BigInteger)
    status_until_truedate: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET) 
    job_company_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    job_company_type: Mapped[Optional[int]] = mapped_column(BigInteger)
    faction_id: Mapped[Optional[int]] = mapped_column(BigInteger)    
    faction_faction_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    faction_faction_name: Mapped[Optional[str]] = mapped_column(String(200))
    married_spouse_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    married_spouse_name: Mapped[Optional[str]] = mapped_column(String(200))
    basicicons_icon8: Mapped[Optional[str]] = mapped_column(String(200))
    basicicons_icon35: Mapped[Optional[str]] = mapped_column(String(200))
    basicicons_icon71: Mapped[Optional[str]] = mapped_column(String(200))
    basicicons_icon15: Mapped[Optional[str]] = mapped_column(String(200))
    basicicons_icon27: Mapped[Optional[str]] = mapped_column(String(200))
    states_hospital_timestamp: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_action_status: Mapped[Optional[str]] = mapped_column(String(200))
    last_action_timestamp: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_action_truedate : Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viacompanyapi : Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viafactionapi : Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viafactionmemberapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viafactionsearchapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viaplayerpersonalstatsapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viaplayerprofileapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viauserapi_v1: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    update_on_viasnapshotapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    status_plane_image_type: Mapped[Optional[str]] = mapped_column(String(200))
    donator: Mapped[Optional[int]] = mapped_column(BigInteger)
    bazaar_snapshot: Mapped[Optional[int]] = mapped_column(BigInteger)

class PlayerSnapshotStaging(Base):
    #id,name,gender,signed_up,level,rank,donator,faction,company,job,spouse,display_case,bazaar,fed,fed_reason,time_played,awards
    __tablename__ = "tb_player_snapshot_staging"
    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Datetimes
    created_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    updated_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    player_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    gender: Mapped[Optional[str]] = mapped_column(String(200))
    signed_up: Mapped[Optional[str]] = mapped_column(String(200))
    level: Mapped[Optional[str]] = mapped_column(String(200))
    player_rank: Mapped[Optional[str]] = mapped_column(String(200))
    donator: Mapped[Optional[str]] = mapped_column(String(200))
    faction: Mapped[Optional[str]] = mapped_column(String(200))
    company: Mapped[Optional[str]] = mapped_column(String(200))
    job: Mapped[Optional[str]] = mapped_column(String(200))
    spouse: Mapped[Optional[str]] = mapped_column(String(200))
    display_case: Mapped[Optional[str]] = mapped_column(String(200))
    bazaar: Mapped[Optional[str]] = mapped_column(String(200))
    fed: Mapped[Optional[str]] = mapped_column(String(200))
    fed_reason: Mapped[Optional[str]] = mapped_column(String(200))
    time_played: Mapped[Optional[str]] = mapped_column(String(200))
    awards: Mapped[Optional[str]] = mapped_column(String(200))
    update_on_viasnapshotapi: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
 
class Item(Base):
    __tablename__ = "torn_item"  
    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Datetimes
    created_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    updated_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    item_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(200))
    effect: Mapped[Optional[str]] = mapped_column(String(200))
    type: Mapped[Optional[str]] = mapped_column(String(200))
    requirement: Mapped[Optional[str]] = mapped_column(String(200))
    sub_type: Mapped[Optional[str]] = mapped_column(String(200))
    value_buy_price: Mapped[Optional[int]] = mapped_column(BigInteger)
    value_sell_price: Mapped[Optional[int]] = mapped_column(BigInteger)
    value_market_price: Mapped[Optional[int]] = mapped_column(BigInteger)
    circulation: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_tradable: Mapped[Optional[str]] = mapped_column(String(200))
    image: Mapped[Optional[str]] = mapped_column(String(200))
    is_masked: Mapped[Optional[str]] = mapped_column(String(200))
    is_found_in_city: Mapped[Optional[str]] = mapped_column(String(200))
   
class Bounty(Base):
    __tablename__ = "torn_bounty"
    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Datetimes
    created_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    updated_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    reward: Mapped[Optional[int]] = mapped_column(BigInteger)
    reason: Mapped[Optional[str]] = mapped_column(String(200))
    quantity: Mapped[Optional[int]] = mapped_column(BigInteger)
    valid_until: Mapped[Optional[int]] = mapped_column(BigInteger)
    valid_until_truedate: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    lister_player_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    target_player_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    

class PlayerStakeout(Base):
    __tablename__ = "torn_playerstakeout"
    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Datetimes
    created_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    updated_on: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET, server_default=text("getdate()") )
    state: Mapped[Optional[str]] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(200))
    last_action_relative: Mapped[Optional[str]] = mapped_column(String(200))
    last_action_truedate: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    transition_datetime: Mapped[Optional[datetime]] = mapped_column(DATETIMEOFFSET)
    comment: Mapped[Optional[str]] = mapped_column(String(200))
    details: Mapped[Optional[str]] = mapped_column(String(200))
    torn_player_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    