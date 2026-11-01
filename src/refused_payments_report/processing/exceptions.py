class BusinessException(Exception):
    """Exceção base para qualquer falha na camada de I/O."""



class BusinessRuleError(BusinessException):
    """Configurações ausentes, inválidas ou inacessíveis."""



class TransformationError(BusinessException):
    """Exceção para falhas técnicas nas transformações."""
