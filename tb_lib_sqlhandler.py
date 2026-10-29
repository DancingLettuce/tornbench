"""This filename is lib_sqlhandler.py"""

#pip install sqlalchemy alembic pyodbc tomli
# check driver installed with cat /etc/odbcinst.ini
# pip install pymysql



from dataclasses import dataclass, field
from datetime import datetime, timezone
import textwrap
import csv
import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import insert
import tb_lib_sqlhandler_models 
from tb_lib_helper_lib import batched
from sqlalchemy.exc import IntegrityError



myvar = textwrap.dedent("""\
        This is a long multi-line string inside a function.
        The backslash after the opening quotes prevents an 
        initial blank line, and dedent removes leading indentation.
    """)


@dataclass
class SqlAService():
    database_name: str=""
    database_host: str=""
    database_user: str=""
    database_password: str=""
    database_driver:str = ""

    @property
    def db_url(self):
        # db_url = (f"mssql+pyodbc://{self.database_user}:" 
        #           f"{self.database_password}@"
        #           f"{self.database_host}/{self.database_name}?"
        #           f"driver={self.database_driver}")
        db_url = (f"mysql+pymysql://{self.database_user}:" 
                  f"{self.database_password}@"
                  f"{self.database_host}/{self.database_name}")
        return db_url
        """pip install mysqlclient -- mysql+mysqldb://"""
 
    @property 
    def engine(self):
        return create_engine(self.db_url) 
    
    def execute_sql(self, sql:str):
        # command line version, comes with the ODBC driver
        # sqlcmd -S 1.2.3.4 -U sqlserver -P "your_password" -d my_database -Q "SELECT * FROM Mytable;"
        """
        # 2. Open a session (Transaction block)
        with Session(engine) as session:
            
            print("\n--- INSERTING DATA ---")
            # Instantiate your model
            new_record = MyTable(my_field="hello world")
            
            # Add to session and commit (Django's new_record.save())
            session.add(new_record)
            session.commit()
            print("Inserted successfully!")

            print("\n--- SELECTING DATA ---")
            # Build the query (Django's MyTable.objects.all())
            statement = select(MyTable)
            
            # Execute and get scalar results
            results = session.execute(statement).scalars().all()
            
            for row in results:
                print(f"ID: {row.id} | Field: {row.my_field}")
        """
        # allow bulk inserts
        engine = self.engine
        """with engine.connect() as connection:
            # Wrap your raw SQL string in the text() function
            result = connection.execute(text(sql))
            connection.commit()
        """  
        with engine.begin() as connection:
            result = connection.execute(text(sql)) 
            print(f"Affected {result.rowcount} rows.")
            # Check if the query actually returned data (like a SELECT) before looping
            return result 
            if result.returns_rows:
                for row in result:
                    print(dict(row._mapping))

    def get_dataset(self, sql:str):
        with Session(self.engine) as session:
            # Execute the query and immediately fetch all results into a list.
            # The list of Row objects is detached from the session.
            result = session.execute(text(sql))
            # .all() returns a list of Row objects, which behave like tuples.
            # This list can be safely returned and used after the session is closed.
            return result.all()
            
    def truncate_table(self, tablename:str):
        engine = create_engine(self.db_url)
        with Session(engine) as session:
            # 1. Execute the raw TRUNCATE statement using your table name
            session.execute(text(f"TRUNCATE TABLE {tablename};"))
            # 2. Commit the transaction
            session.commit()
            print(f"Table {tablename} truncated.")

def get_or_create(session, model, defaults=None, **kwargs):
    """
    Fetches an object or creates it if it doesn't exist.
    Matches Django's get_or_create signature.
    """
    # 1. Try to find the existing record
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    
    if instance:
        return instance, False
        
    # 2. If not found, prepare parameters for a new instance
    params = {k: v for k, v in kwargs.items()}
    if defaults:
        params.update(defaults)
        
    instance = model(**params)
    
    try:
        # 3. Add and safely flush to the database
        session.add(instance)
        session.flush() # Flushes pending changes to DB, generating an ID without committing
        return instance, True
        
    except IntegrityError:
        # 4. Handle race conditions (another process created it between step 1 and 3)
        session.rollback()
        instance = session.query(model).filter_by(**kwargs).one()
        return instance, False
        """Key differences from Django to note:
                Passing the Session: Unlike Django's Active Record pattern (Model.objects...), 
                SQLAlchemy uses the Unit of Work pattern, meaning you must pass your active session object into the helper.

                Commit vs. Flush: The helper uses session.flush() instead of session.commit(). 
                This safely pushes the SQL INSERT statement to the database so the object gets a 
                Primary Key (ID), but keeps the transaction open. This allows you to chain multiple 
                operations together and commit them all at once at the end of your script."""


def update_or_create(session, model, defaults=None, **kwargs):
    """
    Updates an object if it exists, otherwise creates it.
    Matches Django's update_or_create signature.
    """
    defaults = defaults or {}
    
    # 1. Try to find the existing record
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    
    if instance:
        # 2. If found, update its attributes with the new defaults
        for key, value in defaults.items():
            setattr(instance, key, value)
        
        session.flush() # Push the UPDATE to the database
        return instance, False
        
    # 3. If not found, combine kwargs and defaults to create a new one
    params = {**kwargs, **defaults}
    instance = model(**params)
    
    try:
        # 4. Add and safely flush to generate an ID
        session.add(instance)
        session.flush()
        return instance, True
        
    except IntegrityError:
        # 5. Handle race conditions (another process created it while we were trying to)
        session.rollback()
        
        # Fetch the one the other process just created
        instance = session.query(model).filter_by(**kwargs).one()
        
        # Apply our updates to it
        for key, value in defaults.items():
            setattr(instance, key, value)
            
        session.flush()
        return instance, False
        
#