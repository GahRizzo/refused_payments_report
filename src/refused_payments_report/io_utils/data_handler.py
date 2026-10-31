from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (StructType, StructField, StringType, LongType, ArrayType, DateType, DoubleType, FloatType, TimestampType, BooleanType)

class DataHandler:
    """
    Classe responsável pela leitura (input) e escrita (output) de dados.
    """

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def _get_schema_pagamentos(self) -> StructType:
        """Define e retorna o schema para o dataframe de clientes."""
        return StructType([
            StructField("id_pedido", StringType(), True),
            StructField("forma_pagamento", StringType(), True),
            StructField("valor_pagamento", DoubleType(), True),
            StructField("status", BooleanType(), True),
            StructField("data_processamento", TimestampType(), True),
            StructField("avaliacao_fraude", StructType([
                StructField("fraude", BooleanType(), True),
                StructField("score", DoubleType(), True)]), True)
        ])

    def _get_schema_pedidos(self) -> StructType:
        """Define e retorna o schema para o dataframe de pedidos."""
        return StructType([
            StructField("id_pedido", StringType(), True),
            StructField("produto", StringType(), True),
            StructField("valor_unitario", FloatType(), True),
            StructField("quantidade", LongType(), True),
            StructField("data_criacao", TimestampType(), True),
            StructField("uf", StringType(), True),
            StructField("id_cliente", LongType(), True)
        ])

    def load_pagamentos(self, path: str, compression: str) -> DataFrame:
        """Carrega o dataframe de pagamentos a partir de um arquivo JSON."""
        schema = self._get_schema_pagamentos()
        return self.spark.read.option("compression", compression).json(path, schema=schema)

    def load_pedidos(self, path: str, compression: str, header:bool, sep:str) -> DataFrame:
        """Carrega o dataframe de pedidos a partir de um arquivo CSV."""
        schema = self._get_schema_pedidos()
        return self.spark.read.option("compression", compression).csv(path, header=header, schema=schema, sep=sep)
    
    def write_parquet(self, dataframe: DataFrame, path: str):
        """
        Write a dataframe in parquet format
        """
        dataframe.write.mode("overwrite").parquet(path)
        print(f"Dados salvos com sucesso em: {path}")