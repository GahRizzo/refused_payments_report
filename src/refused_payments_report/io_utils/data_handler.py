# PySpark Package
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col
from pyspark.sql.types import (StructType, StructField, StringType, LongType, ArrayType, DateType, DoubleType, FloatType, TimestampType, BooleanType)
from pyspark.errors import AnalysisException, PySparkException

# Self Dependencies
from .exceptions import LoadSources

# Python Dependencies
import logging

logger = logging.getLogger(__name__)

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

    def load_pagamentos(self, path: str, compression: str | None = None) -> DataFrame:
        """
        Carrega o dataframe de pagamentos a partir de um arquivo JSON.

        :Parâmetros:
        path (str): caminho onde os arquivos que serão lidos estão.
        compression (str): tipo de compressão adotado para os arquivos.
        """
        try:
            schema = self._get_schema_pagamentos()

            reader = self.spark.read
            
            if compression is not None:
                reader = reader.option("compression", compression)

            df = reader.json(path, schema=schema)

            logger.info("✅ DataFrame de pagamentos carregado com sucesso.")
            
            return df

        except AnalysisException as e:
            raise LoadSources(f"Falha de análise ao carregar pagamentos em '{path}'") from e

        except PySparkException as e:
            raise LoadSources(f"Falha no Spark ao carregar pagamentos em '{path}'") from e

    def load_pedidos(self, path: str, header:bool, sep:str, compression: str | None = None) -> DataFrame:
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
        try:
            schema = self._get_schema_pedidos()

            reader = self.spark.read.option("header", header).option("sep", sep)

            if compression is not None:
                reader = reader.option("compression", compression)
            
            df = reader.csv(path,schema=schema)
            
            logger.info("✅ DataFrame de pedidos carregado com sucesso.")
            
            return df

        except AnalysisException as e:
            raise LoadSources(f"Falha de análise ao carregar pedidos em '{path}'") from e

        except PySparkException as e:
            raise LoadSources(f"Falha no Spark ao carregar pedidos em '{path}'") from e

    def apply_output_schema(self, df: DataFrame) -> DataFrame:
        """
        Aplica os tipos e a ordem das colunas definidos no schema de saída.

        :Parâmetros:
        df: Dataframe do relatório de output ao qual deseja-se aplicar o schema.

        :Retorno:
        Dataframe com as colunas convertidas para o formato do schema.
        """
        schema = self._get_schema_output()

        expected_columns = [field.name for field in schema.fields]
        missing_columns = [name for name in expected_columns if name not in df.columns]

        if missing_columns:
            raise ValueError("Colunas obrigatórias ausentes no relatório: "f"{', '.join(missing_columns)}")

        return df.select(
            *[
                col(field.name)
                .cast(field.dataType)
                .alias(field.name)
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

        try:
            df.write.mode("overwrite").parquet(path)
            logger.info("✅ Relatório escrito e salvo com sucesso em: %s", path)
        
        except AnalysisException as e:
            raise WriteOutput(f"Falha de análise ao escrever relatório em '{path}'") from e

        except PySparkException as e:
            raise WriteOutput(f"Falha no Spark ao escrever relatório em '{path}'") from e

        except OSError as e:
            raise WriteOutput(f"Falha de I/O ao escrever relatório em '{path}'") from e