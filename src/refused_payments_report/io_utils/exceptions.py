class DataHandlerException(Exception):
    """Exceção base para qualquer falha na camada de I/O."""
    pass

class LoadSources(DataHandlerException):
    """Lançada especificamente ao falhar o carregamento dos datasets."""
    pass

class WriteOutput(DataHandlerException):
    """Falha na escrita do relatório de saída."""