class DataHandlerException(Exception):
    """Exceção base para qualquer falha na camada de I/O."""



class LoadSources(DataHandlerException):
    """Lançada especificamente ao falhar o carregamento dos datasets."""



class WriteOutput(DataHandlerException):
    """Falha na escrita do relatório de saída."""
