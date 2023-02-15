import environs, psycopg2

env = environs.Env()
env.read_env('.env')

try:
    connection = psycopg2.connect(
        user=env('USER'),
        password=env('PASSWORD'),
        database=env('DB_NAME'),
        host=env('HOST'),
        port=env('PORT'),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT version();"
        )
        print(f'Server version: {cursor.fetchone()}')
except Exception as _ex:
    print(f'[Error connection PostgreSQL]', _ex)
""" finally:
    if connection:
        connection.close()
        print('PostgreSQL connection closed') """