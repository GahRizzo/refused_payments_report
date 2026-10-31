from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col
from pyspark.sql.types import (StructType, StructField, StringType, LongType, ArrayType, DateType, DoubleType, FloatType, TimestampType, BooleanType)

class DataHandler:
    """
    Classe responsável pela leitura (input) e escrita (output) de dados.

    :Funções:
    _get_schema_pagamentos: retorna o schema que o arquivo de pagamentos deve conter.
    _get_schema_pedidos: retorna o schema que o arquivo de pedidos deve conter.
    load_pagamentos: faz a leitura e carrega o arquivo de pagamentos baseado no schema declarado.
    load_pedidos: faz a leitura e carrega o arquivo de pedidos baseado no schema declarado.
    write_parquet: faz a escrita de um dataframe em um formato parquet
    """

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def _get_schema_pagamentos(self) -> StructType:
        """
        Define e retorna o schema para o dataframe de clientes.
        """
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
        """
        Define e retorna o schema para o dataframe de pedidos.
        """
        return StructType([
            StructField("id_pedido", StringType(), True),
            StructField("produto", StringType(), True),
            StructField("valor_unitario", FloatType(), True),
            StructField("quantidade", LongType(), True),
            StructField("data_criacao", TimestampType(), True),
            StructField("uf", StringType(), True),
            StructField("id_cliente", LongType(), True)
        ])
    
    def _get_schema_output(self) -> StructType:
        """
        Define o schema esperado para o relatório final de pagamentos recusados.
        """
        return StructType([
            StructField("id_pedido", StringType(), False),
            StructField("uf", StringType(), True),
            StructField("forma_pagamento", StringType(), True),
            StructField("valor_total", DoubleType(), True),
            StructField("data_criacao", TimestampType(), True)
        ])

    def load_pagamentos(self, path: str, compression: str) -> DataFrame:
        """
        Carrega o dataframe de pagamentos a partir de um arquivo JSON.

        :Parâmetros:
        path (str): caminho onde os arquivos que serão lidos estão.
        compression (str): tipo de compressão adotado para os arquivos.
        """
        schema = self._get_schema_pagamentos()
        return self.spark.read.option("compression", compression).json(path, schema=schema)

    def load_pedidos(self, path: str, compression: str, header:bool, sep:str) -> DataFrame:
        """
        Carrega o dataframe de pedidos a partir de um arquivo CSV.

        :Parâmetros:
        path (str): caminho onde os arquivos que serão lidos estão.
        compression (str): tipo de compressão adotado para os arquivos.
        header (bool): sinaliza se o arquivo contém header ou não.
        sep (sep): qual o tipo de separador de colunas adotado.

        :Retorno:
        Dataframe contendo os dados carregados
        """
        schema = self._get_schema_pedidos()
        return self.spark.read.option("compression", compression).csv(path, header=header, schema=schema, sep=sep)

    def apply_output_schema(self, df: DataFrame) -> DataFrame:
        """
        Aplica os tipos e a ordem das colunas definidos no schema de saída.

        :Parâmetros:
        df: Dataframe do relatório de output ao qual deseja-se aplicar o schema.

        :Retorno:
        Dataframe com as colunas convertidas para o formato do schema.
        """
        schema = self._get_schema_output()

        return df.select(
            *[
                col(field.name).cast(field.dataType).alias(field.name)
                for field in schema.fields
            ]
        )
    
    def write_parquet(self, df: DataFrame, path: str):
        """
        Escreve o relatório de output no formato de parquet para um path específico.

        :Parâmetros:
        dataframe (DataFrame): dataframe que deve ser salvo
        path (str): caminho onde os arquivos parquet serão salvos.
        """
        df.write.mode("overwrite").parquet(path)
        print(f"Dados salvos com sucesso em: {path}")