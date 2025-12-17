from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM fire_iib_rates LIMIT 10'))
    print('iib_code | rate_per_mille')
    print('-' * 40)
    for row in result:
        print(f'{row.iib_code} | {row.rate_per_mille}')
