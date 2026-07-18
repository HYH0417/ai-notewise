import os
from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///./prompt_workbench.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

conn = engine.connect()
cursor = conn.connection.cursor()

cursor.execute('SELECT COUNT(*) FROM prompts')
result = cursor.fetchone()
print(f'Prompts count in SQLAlchemy DB: {result[0]}')

cursor.execute("PRAGMA database_list")
rows = cursor.fetchall()
print('\nDatabase files:')
for row in rows:
    print(f'  {row}')

conn.close()

print(f'\nCurrent working directory: {os.getcwd()}')
print(f'Database file exists: {os.path.exists("./prompt_workbench.db")}')
print(f'Database file size: {os.path.getsize("./prompt_workbench.db")} bytes')
