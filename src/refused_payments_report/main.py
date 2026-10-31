# Python Libs
import logging
import sys

# Pipeline App
from session.spark_session import SparkSessionManager
from config.settings import Configs
from config.logging_config import LoggingConfig
from io_utils.data_handler import DataHandler
from processing.transformations import Transformation
from pipeline.pipeline import Pipeline


def main():

    spark = None
    exit_code = 0

    try:
        # Carregando configurações
        configs_pipeline = Configs()
        print(configs_pipeline)
        configs = configs_pipeline.configs

        # Configurando Logging
        LoggingConfig.configure(configs["logging"])
        

        # Inicializando Logger
        logger = logging.getLogger(__name__)
        logger.info("▶️ Iniciando execução do pipeline.")

        APP_NAME = configs.get("spark",{}).get("app_name")

        spark = SparkSessionManager.get_spark_session(app_name = APP_NAME)

        data_handler = DataHandler(spark = spark)
        data_transformer = Transformation()
        pipeline = Pipeline(data_handler = data_handler, data_transformer = data_transformer)

        pipeline.run(configs = configs)

        logger.info("✅ Pipeline executado com sucesso.")
    
    except Exception:
        logger.exception("Falha durante a execução do pipeline.")
        exit_code = 1

    finally:
        if spark is not None:
            try:
                spark.stop()
                logger.info("⭐ Sessão Spark encerrada.")

            except Exception:
                logger.exception("❌ Falha ao encerrar a sessão Spark.")
                exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())