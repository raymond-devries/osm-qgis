import os
import subprocess

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

POSTGRES_PORT = os.getenv("POSTGRES_PORT", 5432)


def get_connection(db_name):
    conn = psycopg2.connect(dbname=db_name, user="postgres", password="qgis", port=POSTGRES_PORT, host="0.0.0.0")
    return conn


def execute_isolation_query(query, db_name: str = "postgres"):
    conn = get_connection(db_name)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()


def create_db(db_name: str):
    execute_isolation_query(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(db_name)))
    execute_isolation_query("CREATE EXTENSION postgis", db_name)


def drop_db(db_name: str):
    execute_isolation_query(sql.SQL("DROP DATABASE {};").format(sql.Identifier(db_name)))


def execute_query(query: str, db_name: str):
    with get_connection(db_name) as conn:
        with conn.cursor() as curs:
            curs.execute(query)
    conn.close()


def fetch_all_query(query: str, db_name: str):
    with get_connection(db_name) as conn:
        with conn.cursor() as curs:
            curs.execute(query)
            data = curs.fetchall()
    conn.close()
    return data


def get_all_databases():
    return [
        x[0]
        for x in fetch_all_query(
            "SELECT datname FROM pg_database WHERE datistemplate = false and datname != 'postgres';", "postgres"
        )
    ]


def import_osm(path_name: str, db_name: str):
    create_db(db_name)
    subprocess.call([f"osm2pgsql {path_name} -H 0.0.0.0 -P {POSTGRES_PORT} -d {db_name} -U postgres"], shell=True)
    # executing this query ensures you can edit the data in qgis if needed
    execute_query(
        "ALTER TABLE planet_osm_point ADD gid serial PRIMARY KEY;"
        "ALTER TABLE planet_osm_line ADD gid serial PRIMARY KEY;"
        "ALTER TABLE planet_osm_polygon ADD gid serial PRIMARY KEY;"
        "ALTER TABLE planet_osm_roads ADD gid serial PRIMARY KEY;",
        db_name,
    )
