# Python Dependences
import logging
import sys

from refused_payments_report.config.logging import LoggingConfig
from refused_payments_report.config.settings import Configs
from refused_payments_report.io_utils.data_handler import DataHandler
from refused_payments_report.pipeline.pipeline import Pipeline
from refused_payments_report.processing.transformations import Transformation

# Self Dependencies
from refused_payments_report.session.spark_session import SparkSessionManager


def main() -> int:

    # Variáveis iniciais
    spark = None
    exit_code = 0

    # Configuração independente do settings.yaml
    LoggingConfig.configure("./config/logging.yaml")
    logger = logging.getLogger(__name__)

    try:
        # Carregando configurações
        configs_pipeline = Configs()
        print(configs_pipeline)
        configs = configs_pipeline.configs

        logger.info("▶️  Iniciando execução do pipeline.")

        APP_NAME = configs.get("spark", {}).get("app_name")

        spark = SparkSessionManager.get_spark_session(app_name=APP_NAME)

        data_handler = DataHandler(spark=spark)
        data_transformer = Transformation()
        pipeline = Pipeline(
            data_handler=data_handler, data_transformer=data_transformer
        )

        pipeline.run(configs=configs)

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
