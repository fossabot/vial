import psycopg2

from .base import SQL


class Postgresql(SQL):
    """
    """
    engine_name = 'PostgreSQL'
    type_mapping = {
        'int': 'integer',
        'str': 'varchar',
        'float': 'real',
        'bool': 'bool',
        'date': 'date',
        'time': 'time',
        'datetime': 'timestamp',
        'uuid': 'uuid',
    }

    def __init__(self, dbname, user, password, host, port, *args, **kwargs):
        super(Postgresql, self).__init__(*args, **kwargs)
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def __enter__(self):
        self._conn = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
        return self

    @classmethod
    def _tables_query(cls):
        query = ' '.join(f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        """.split())
        return query

    @classmethod
    def _create_query(cls, table_name, serial=False, fields=None):
        fields = fields or {}
        query = ' '.join(f"""
        CREATE TABLE {table_name}
        ( {'id SERIAL PRIMARY KEY' if serial else ''}
        {', ' if serial and fields else ''}
        {' , '.join([
            f'''{k}
            {Postgresql.type_mapping.get(v.get('type', 'json'))}
            {' PRIMARY KEY' if v.get('primary') else ''}
            {' NOT NULL' if v.get('not_null') else ''}
            {' UNIQUE' if v.get('unique') else ''}''' for k, v in fields.items()
        ])});
        """.split())
        return query

    @classmethod
    def _insert_query(cls, table_name, fields=None):
        query = ' '.join(f"""
        INSERT INTO {table_name} ({', '.join(fields)})
        VALUES ({', '.join(["%s" for _ in fields])})
        """.split())
        return query

    @classmethod
    def _select_query(cls, table_name, fields=None, where=None, like=None, offset=None, limit=None):
        def stringify(v, like=False):
            if like:
                return f"'%{v}%'"
            return f"'{v}'"

        query = ' '.join(f"""
        SELECT {', '.join(fields) if fields else '*'} FROM {table_name}
        {f' WHERE {" AND ".join([f"{k}={v if isinstance(v, (int, float, bool)) else stringify(v)}" for k, v in where.items()])}' if where else ''}
        {f' {"AND" if where else "WHERE"} {" AND ".join([f"{k} ILIKE {stringify(v, like=True)}" for k, v in like.items()])}' if like else ''}
        {f' OFFSET {offset}' if offset else ''}
        {f' LIMIT {limit}' if limit else ''};
        """.split())
        return query

    @classmethod
    def _update_query(cls, table_name, where=None, updation=None):
        query = ' '.join(f"""
        UPDATE {table_name}
        {f' SET {", ".join([f"{k}=(%s)" for k in updation.keys()])}' if updation else ''}
        {f' WHERE {" AND ".join([f"{k}=(%s)" for k in where.keys()])}' if where else ''}
        """.split())
        return query

    def update(self, table_name, where=None, updation=None):
        cur = self._conn.cursor()
        cur.execute(Postgresql._update_query(
            table_name, where=where, updation=updation
        ), (tuple(updation.values()), tuple(where.values())))
        self._conn.commit()
        cur.close()
        return True

    @classmethod
    def _delete_query(cls, table_name, where=None):
        query = ' '.join(f"""
        DELETE FROM {table_name}
        {f' WHERE {" AND ".join([f"{k}=(%s)" for k in where.keys()])}' if where else ''}
        """.split())
        return query
