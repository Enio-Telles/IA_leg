"""
[DEPRECATED] Sobrescreve patches de inicialização de trilha segura.

AVISO: O uso de monkey patches em tempo de importação para selecionar as engines
foi substituído pelo Factory pattern (`ia_leg.app.factory.py`).
Esta abordagem era inaceitável para um sistema jurídico auditável e foi depreciada.

Por favor, configure o comportamento da engine através da variável de ambiente:
    IA_LEG_ENGINE_MODE=standard|safe|safe_audited
"""

import logging

logger = logging.getLogger(__name__)

# Mantido inativo para evitar erros de dependência antigos em imports globais
logger.warning("[IA_leg Warning] O uso do `usercustomize.py` para patches automáticos está desativado.")
logger.warning("Use a variável de ambiente `IA_LEG_ENGINE_MODE` para configurar a engine.")
