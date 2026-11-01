from pyspark.sql import SparkSession

class SparkSessionManager:
    """
    Gerencia a criação e o acesso à sessão Spark.

    :Parâmetros:
    app_name (str): nome da aplicação desejado

    :Retorno:
    SparkSession configurada com o nome da sessão.
    """
    @staticmethod
    def get_spark_session(app_name: str = "refused-payments-report") -> SparkSession:
        """
        Cria e retorna uma sessão Spark.

        :param app_name: Nome da aplicação Spark.
        :return: Instância da SparkSession.
        """

        spark = SparkSession.builder.appName(app_name).master("local[*]").getOrCreate()
        spark.sparkContext.setLogLevel("ERROR")

        return spark