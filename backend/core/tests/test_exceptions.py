from core.exceptions import ConflictoError, ReglaDeNegocioError, exception_handler


def test_regla_de_negocio_devuelve_400_con_codigo_y_detalle():
    response = exception_handler(ReglaDeNegocioError("RN-00", "Ejemplo"), {})

    assert response.status_code == 400
    assert response.data == {"codigo": "RN-00", "detalle": "Ejemplo"}


def test_conflicto_devuelve_409():
    response = exception_handler(ConflictoError("RN-00", "Ejemplo"), {})

    assert response.status_code == 409
