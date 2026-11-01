# Python Dependencies
import logging

from pyspark.errors import AnalysisException, PySparkException

# Spark Dependencies
from pyspark.sql import DataFrame
from pyspark.sql.functions import asc, col, count, desc, isnan, year
from pyspark.sql.types import StructType

# Self Dependencies
from .exceptions import BusinessRuleError, TransformationError

logger = logging.getLogger(__name__)


class Transformation:
    """
    Classe que contém as transformações e regras de negócio da aplicação.
    """

    @staticmethod
    def _require_columns(df: DataFrame, columns: list[str]) -> None:
        """
        Valida as colunas necessárias para a transformação.

        :Parâmetros:
        df: dataframe que será verificado
        columns: lista de colunas que serão testadas

        :Retorno:
        Nenhum, apenas faz um raise caso ocorra um erro
        """

        missing = [name for name in columns if name not in df.columns]

        if missing:
            raise BusinessRuleError(
                f"Colunas obrigatórias ausentes: {', '.join(missing)}"
            )

    def add_total_value(self, df: DataFrame) -> DataFrame:
        """
        Criando a coluna que calcula o valor total de um pedido, multiplicando quantidade por valor unitário

        :Parâmetros:
        df (DataFrame): Dataframe ao qual deseja aplicar a transformação

        :Retorno:
        Dataframe adicionando a coluna valor_total,
        """

        try:
            self._require_columns(df, ["valor_unitario", "quantidade"])

            invalid_orders = df.filter(
                col("quantidade").isNull()
                | (col("quantidade") <= 0)
                | (col("valor_unitario").isNull())
                | (col("valor_unitario") < 0)
                | (isnan(col("valor_unitario")))
            )

            if invalid_orders.limit(1).count() > 0:
                raise BusinessRuleError(
                    "Foram encontrados pedidos com quantidade ou valor unitário inválidos."
                )

            transformed_df = df.withColumn(
                "valor_total", col("valor_unitario") * col("quantidade")
            )

            logger.info("✅ Coluna valor total calculada com sucesso.")

            return transformed_df

        except BusinessRuleError:
            raise

        except (AnalysisException, PySparkException) as e:
            raise TransformationError(
                "Falha no Spark ao calcular o valor total dos pedidos."
            ) from e

    def year_orders_filter(self, df: DataFrame, target_year: int) -> DataFrame:
        """
        Filtrando os pedidos para um ano específico do relatório.

        :Parâmetros:
        target_year (int): Ano que seja filtrar sobre uma data
        df (DataFrame): Dataframe ao qual deseja aplicar a filtragem

        :Retorno:
        Dataframe filtrado para o período especificado.

        """

        try:
            if type(target_year) is not int or target_year < 1:
                raise BusinessRuleError(f"Ano inválido para o relatório: {target_year}")

            self._require_columns(df, ["data_criacao"])

            transformed_df = df.filter(year(col("data_criacao")) == target_year)

            logger.info(f"✅ Pedidos filtrados para o ano de {target_year}.")

            return transformed_df

        except BusinessRuleError:
            raise

        except (AnalysisException, PySparkException) as e:
            raise TransformationError(
                f"Falha no Spark ao filtrar pedidos do ano {target_year}."
            ) from e

    def false_negative_payments_filter(self, df: DataFrame) -> DataFrame:
        """
        Filtrando pedidos com que tiveram o pagamento negado e não tiveram sinalização de fraude

        :Parâmetros:
        df (DataFrame): Dataframe que armazena as informações de pagamentos

        :Retorno:
        DataFrame filtrando apenas pedidos recusado e não fraudulentos
        """

        try:
            self._require_columns(df, ["status", "avaliacao_fraude"])
            fraud_type = df.schema["avaliacao_fraude"].dataType

            if not isinstance(fraud_type, StructType):
                raise BusinessRuleError("'avaliacao_fraude' deve ser uma estrutura.")

            if "fraude" not in fraud_type.fieldNames():
                raise BusinessRuleError(
                    "Campo obrigatório ausente: 'avaliacao_fraude.fraude'"
                )

            transformed_df = (
                df
                .filter(~col("status"))
                .filter(~col("avaliacao_fraude.fraude"))
            )

            logger.info(
                "✅ Pedidos filtrados para `fraude == False` e `status == False`."
            )

            return transformed_df

        except BusinessRuleError:
            raise

        except (AnalysisException, PySparkException) as e:
            raise TransformationError(
                "Falha no Spark ao filtrar pagamentos recusados."
            ) from e

    def join_information(
        self, orders_df: DataFrame, payments_df: DataFrame
    ) -> DataFrame:
        """
        Unificando as informações de pedidos e pagamentos em uma única tabela e selecione colunas de interesse

        :Parâmetros:
        payments_df (DataFrame): Dataframe que armazena as informações de pagamentos
        orders_df (DataFrame): Dataframe que armazena as informações de pedidos

        :Retorno:
        DataFrame de pagamento enriquecido com as informações referente ao pedido.
        """

        try:
            self._require_columns(
                orders_df, ["id_pedido", "uf", "valor_total", "data_criacao"]
            )
            self._require_columns(payments_df, ["id_pedido", "forma_pagamento"])

            # Chaves duplicadas
            duplicated_orders = (
                orders_df.groupBy("id_pedido")
                .agg(count("*").alias("total"))
                .filter(col("total") > 1)
            )

            if duplicated_orders.limit(1).count() > 0:
                raise BusinessRuleError(
                    "Foram encontrados pedidos com id_pedido duplicado."
                )

            duplicated_payments = (
                payments_df.groupBy("id_pedido")
                .agg(count("*").alias("total"))
                .filter(col("total") > 1)
            )

            if duplicated_payments.limit(1).count() > 0:
                raise BusinessRuleError(
                    "Foram encontrados pagamentos com id_pedido duplicado."
                )

            joined_df = (
                payments_df.alias("p")
                .join(
                    orders_df.alias("o"),
                    col("p.id_pedido") == col("o.id_pedido"),
                    how="inner",
                )
                .select(
                    col("p.id_pedido"),
                    col("o.uf"),
                    col("p.forma_pagamento"),
                    col("o.valor_total"),
                    col("o.data_criacao"),
                )
            )

            logger.info(
                "✅ Unificação das tabelas de pagamentos e pedidos realizada com sucesso."
            )

            return joined_df

        except BusinessRuleError:
            raise

        except (AnalysisException, PySparkException) as e:
            raise TransformationError(
                "Falha no Spark ao unificar pedidos e pagamentos em uma única tabela."
            ) from e

    def priorization(self, df: DataFrame) -> DataFrame:
        """
        Aplicação de um ranqueamento ao dataframe levando em consideração a Unidade Federativa, Forma de Pagamentos e o Valor Total

        :Parâmetros:
        df (Dataframe): Dataframe para priorização

        :Retorno:
        Dataframe ordenado segundo as colunas uf, formna_pagamento e valor_total
        """

        try:
            self._require_columns(df, ["uf", "forma_pagamento", "valor_total"])

            transformed_df = df.orderBy(
                asc(col("uf")), asc(col("forma_pagamento")), desc(col("valor_total"))
            )

            logger.info(
                "✅ Ordenação dos pagamentos por UF, Forma de Pagamento e Valor total realizada com sucesso."
            )

            return transformed_df

        except BusinessRuleError:
            raise

        except (AnalysisException, PySparkException) as e:
            raise TransformationError(
                "Falha no Spark ao priorizar os registros do relatório."
            ) from e
