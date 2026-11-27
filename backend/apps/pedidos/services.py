"""Business rules (RN-xx) for pedidos, applied inside transactions.

Rules raise core.exceptions.ReglaDeNegocioError (400) or ConflictoError (409).
This is the most tested layer (tests/test_services.py).
"""
