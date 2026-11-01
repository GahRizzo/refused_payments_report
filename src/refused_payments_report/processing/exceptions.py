class BusinessException(Exception):
    """Exceção base para qualquer falha na camada de I/O."""
    pass

class BusinessRuleError(BusinessException):
    """Configurações ausentes, inválidas ou inacessíveis."""
    pass

class TransformationError(BusinessException):
    """Exceção para falhas técnicas nas transformações."""