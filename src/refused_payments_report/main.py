from session.spark_session import SparkSessionManager
from config.settings import load_config
from io_utils.data_handler import DataHandler
from processing.transformations import Transformation
from pipeline.pipeline import Pipeline

def main():

    configs = load_config(path = "./config/settings.yaml")

    APP_NAME = configs.get("spark",{}).get("app_name")

    spark = SparkSessionManager.get_spark_session(app_name = APP_NAME)

    data_handler = DataHandler(spark = spark)
    data_transformer = Transformation()
    pipeline = Pipeline(data_handler = data_handler, data_transformer = data_transformer)
    pipeline.run(configs = configs)

    spark.stop()

if __name__ == "__main__":
    main()