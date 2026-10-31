from pyspark.sql import DataFrame
from pyspark.sql.functions import col, year, asc, desc

class Transformation:
    """
    Classe que contém as transformações e regras de negócio da aplicação.
    """

    def add_total_value(self, df: DataFrame) -> DataFrame:
        """
        Criando a coluna que calcula o valor total de um pedido, multiplicando quantidade por valor unitário

        :Parâmetros:
        df (DataFrame): Dataframe ao qual deseja aplicar a transformação

        :Retorno:
        Dataframe adicionando a coluna valor_total,
        """
        return(
            df.withColumn(
                "valor_total", 
                col("valor_unitario") * col("quantidade")
            )
        )
    
    def year_orders_filter(self, target_year: int, df: DataFrame) -> DataFrame:
        """
        Filtrando os pedidos para um ano específico do relatório.

        :Parâmetros:
        target_year (int): Ano que seja filtrar sobre uma data
        df (DataFrame): Dataframe ao qual deseja aplicar a filtragem

        :Retorno:
        Dataframe filtrado para o período especificado.
        
        """
        return(
            df
            .filter(year(col("data_criacao")) == target_year)
        )
    
    def false_negative_payments_filter(self, df: DataFrame) -> DataFrame:
        """
        Filtrando pedidos com que tiveram o pagamento negado e não tiveram sinalização de fraude

        :Parâmetros:
        df (DataFrame): Dataframe que armazena as informações de pagamentos

        :Retorno:
        DataFrame filtrando apenas pedidos recusado e não fraudulentos
        """
        return(
            df
            .filter(col("status") == False)
            .filter(col("avaliacao_fraude.fraude") == False)
        )
    
    def join_information(self, payments_df: DataFrame, orders_df: DataFrame) -> DataFrame:
        """
        Unificando as informações de pedidos e pagamentos em uma única tabela e selecione colunas de interesse

        :Parâmetros:
        payments_df (DataFrame): Dataframe que armazena as informações de pagamentos
        orders_df (DataFrame): Dataframe que armazena as informações de pedidos

        :Retorno:
        DataFrame de pagamento enriquecido com as informações referente ao pedido.
        """
        return(
            payments_df.alias("p")
            .join(
                orders_df.alias("o"),
                (col("p.id_pedido") == col("o.id_pedido")),
                how = "inner"
            )
            .select(
                col("p.id_pedido"),
                col("o.uf"),
                col("p.forma_pagamento"),
                col("o.valor_total"),
                col("o.data_criacao")
            )
        )
    
    def priorization(self, df: DataFrame) -> DataFrame:
        """
        Aplicação de um ranqueamento ao dataframe levando em consideração a Unidade Federativa, Forma de Pagamentos e o Valor Total

        :Parâmetros:
        df (Dataframe): Dataframe para priorização

        :Retorno:
        Dataframe ordenado segundo as colunas uf, formna_pagamento e valor_total
        """
        return (
            dataframe
            .orderBy(
                asc(col("uf")), 
                asc(col("forma_pagamento")), 
                desc(col("valor_total"))
            )
        )