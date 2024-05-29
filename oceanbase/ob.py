import datetime
from typing import Any, Callable, Iterable, List, Optional, Sequence, Tuple, Type

from sqlalchemy import Column, String, Table, create_engine, insert, text
from sqlalchemy.types import UserDefinedType, String
from sqlalchemy.dialects.mysql import VARCHAR, INTEGER

try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def from_db(value):
    return [float(v) for v in value[1:-1].split(',')]

def to_db(value, dim=None):
    if value is None:
        return value

    return '[' + ','.join([str(float(v)) for v in value]) + ']'

class Vector(UserDefinedType):
    cache_ok = True
    _string = String()

    def __init__(self, dim):
        super(UserDefinedType, self).__init__()
        self.dim = dim

    def get_col_spec(self, **kw):
        return "VECTOR(%d)" % self.dim

    def bind_processor(self, dialect):
        def process(value):
            return to_db(value, self.dim)
        return process

    def literal_processor(self, dialect):
        string_literal_processor = self._string._cached_literal_processor(dialect)

        def process(value):
            return string_literal_processor(to_db(value, self.dim))
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            return from_db(value)
        return process

class ObImgVec:
    def __init__(self, connect_str, table_name, glb_img_id):
        self.ob_vector_db = create_engine(connect_str)
        self.table_name = table_name
        self.embedding_dim = -1
        self.glb_img_id = glb_img_id

    # 创建 img2img 表
    def ob_create_img2img(self, embedding_dim):
        self.embedding_dim = embedding_dim
        img2img_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{self.table_name}` (
                id INT NOT NULL, 
                embedding VECTOR({self.embedding_dim}), 
                path VARCHAR(1024) NOT NULL, 
                PRIMARY KEY (id)
            )
        """
        with self.ob_vector_db.connect() as conn:
            with conn.begin():
                conn.execute(text(img2img_table_query))
                print(f"create table ok: {img2img_table_query}")

    def get_imgid(self):
        return self.glb_img_id + 1

    # 向 img2img 表中插入向量
    def ob_insert_img2img(self, embedding_vec, path):
        if self.embedding_dim == -1:
            self.embedding_dim = len(embedding_vec.tolist())
        if self.embedding_dim != len(embedding_vec.tolist()):
            print(f"dim mismatch!! ---- expect: {self.embedding_dim} while get {len(embedding_vec.tolist())}")
            raise ValueError("embedding dim mismatch")
        self.glb_img_id += 1
        img_id = self.glb_img_id
        img2img_table = Table(
            self.table_name,
            Base.metadata,
            Column("id", INTEGER, primary_key=True),
            Column("embedding", Vector(self.embedding_dim)),
            Column("path", VARCHAR(1024), nullable=False),
            keep_existing=True,
        )
        data = [{
            "id": img_id,
            "embedding": embedding_vec.tolist(),
            "path": path,
        }]
        with self.ob_vector_db.connect() as conn:
            with conn.begin():
                conn.execute(insert(img2img_table).values(data))
    
    # vector_distance_op:
    # <->: 欧式距离； <~>: cosine距离； <@>: 点积 
    # 使用 OceanBase Vector DataBase 进行 ANN 查找
    def ob_ann_search(self, vector_distance_op, query_vector, topk):
        if self.embedding_dim == -1:
            self.embedding_dim = len(query_vector.tolist())
        try:
            from sqlalchemy.engine import Row
        except ImportError:
            raise ImportError(
                "Could not import Row from sqlalchemy.engine. "
                "Please 'pip install sqlalchemy>=1.4'."
            )

        vector_str = to_db(query_vector)
        sql_query = f"""
            SELECT path, embedding {vector_distance_op} '{vector_str}' as distance
            FROM `{self.table_name}`
            ORDER BY embedding {vector_distance_op} '{vector_str}'
            LIMIT {topk}
        """
        sql_query_str_for_print = f"""
            SELECT path, embedding {vector_distance_op} '?' as distance
            FROM `{self.table_name}`
            ORDER BY embedding {vector_distance_op} '?'
            LIMIT {topk}
        """
        with self.ob_vector_db.connect() as conn:
            begin_ts = datetime.datetime.now()
            results: Sequence[Row] = conn.execute(text(sql_query)).fetchall()
            cost = (datetime.datetime.now() - begin_ts).total_seconds()
            print(f"Search {sql_query_str_for_print} cost: {cost} s")
            return [res for res in results], cost
        return [], 0.0