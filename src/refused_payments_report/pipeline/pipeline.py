# Self Dependencies
from refused_payments_report.io_utils.data_handler import DataHandler
from refused_payments_report.processing.transformations import Transformation

class Pipeline:
    """
    Encapsula a lógica de execução do pipeline de dados.
    """
    def __init__(self, data_handler: DataHandler, data_transformer: Transformation):
        self.data_handler = data_handler
        self.data_transformer = data_transformer

    def run(self, configs):
        """
        Executa o pipeline completo: carga das sources, transformação dos dados e materialização.

        :Parâmetros:
        data_handler (Class): Classe para carga e escrita dos dados de pagamentos e pedidos
        data_transformer (Class): Classe para transformação dos dados de pagamentos e pedidos
        """

        # Declaração de variáveis
        ## Paths configs
        PATH_PAGAMENTO = configs.get("paths",{}).get("pagamentos")
        PATH_PEDIDOS = configs.get("paths",{}).get("pedidos")
        PATH_OUTPUT = configs.get("paths",{}).get("output")

        ## Load Configs
        COMPRESSION_PAGAMENTOS = configs.get("file_options",{}).get("pagamentos_json", {}).get("compression")
        HEADER_PEDIDOS = configs.get("file_options",{}).get("pedidos_csv", {}).get("header")
        SEPARATOR_PEDIDOS = configs.get("file_options",{}).get("pedidos_csv", {}).get("sep")
        COMPRESSION_PEDIDOS = configs.get("file_options",{}).get("pedidos_csv", {}).get("compression")

        ## Load Transformer Configs
        TARGET_YEAR = configs.get("transformer",{}).get("target_year")

        # Carregando dataframes
        ## Pedidos
        raw_pedidos = self.data_handler.load_pedidos(
            path = PATH_PEDIDOS, 
            header = HEADER_PEDIDOS, 
            sep = SEPARATOR_PEDIDOS, 
            compression = COMPRESSION_PEDIDOS)

        ## Pagamentos
        raw_pagamentos = self.data_handler.load_pagamentos(
            path = PATH_PAGAMENTO, 
            compression = COMPRESSION_PAGAMENTOS
        )

        # Criando a coluna de valor total
        pedidos = (
            raw_pedidos
            .transform(self.data_transformer.add_total_value)
            .transform(self.data_transformer.year_orders_filter, target_year = TARGET_YEAR)
        )

        # Filtrando dataset de pagamentos
        pagamentos = (
            raw_pagamentos
            .transform(self.data_transformer.false_negative_payments_filter)
        )

        # Unificando os dados
        relatorio = (
            pedidos
            .transform(self.data_transformer.join_information, payments_df = pagamentos)
            .transform(self.data_transformer.priorization)
            .transform(self.data_handler.apply_output_schema)
        )

        # Escrevendo o relatório na pasta de output
        self.data_handler.write_parquet(df=relatorio, path=PATH_OUTPUT)