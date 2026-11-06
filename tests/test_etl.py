import logging
import sqlite3

import pandas as pd

from etl import cargar, ejecutar, transformar

HOY = "2026-06-30"


def datos_crudos():
    return pd.DataFrame({
        "id_venta": [1, 2, 2, None],
        "fecha": ["2026-01-05"] * 4,
        "monto": ["100.5", "-20", "-20", "50"],
    })


def test_sin_duplicados_ni_nulos():
    df = transformar(datos_crudos())
    assert df["id_venta"].is_unique
    assert df["id_venta"].notna().all()


def test_montos_positivos():
    df = transformar(datos_crudos())
    assert (df["monto"] > 0).all()


def test_montos_vacios_y_cero_se_descartan():
    crudo = pd.DataFrame({
        "id_venta": [1, 2, 3],
        "fecha": ["2026-01-05"] * 3,
        "monto": [None, 0, 10],
    })
    assert transformar(crudo, HOY)["id_venta"].tolist() == [3]


def test_tipos_convertidos():
    df = transformar(datos_crudos(), HOY)
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"])
    assert pd.api.types.is_float_dtype(df["monto"])


# Reto 1: fechas futuras
def test_rechaza_ventas_con_fecha_futura():
    crudo = pd.DataFrame({
        "id_venta": [1, 2, 3],
        "fecha": ["2026-06-29", HOY, "2026-07-01"],  # ayer, hoy, mañana
        "monto": [10, 20, 30],
    })
    df = transformar(crudo, HOY)
    assert df["id_venta"].tolist() == [1, 2]  # la de hoy sí se conserva
    assert (df["fecha"] <= pd.Timestamp(HOY)).all()


def test_carga_es_idempotente(tmp_path):
    db = tmp_path / "ventas.db"
    df = transformar(datos_crudos(), HOY)
    cargar(df, db)
    cargar(df, db)
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == len(df)


def test_pipeline_completo_con_datos_de_ejemplo(tmp_path):
    db = tmp_path / "ventas.db"
    leidas, cargadas = ejecutar("data/ventas.csv", db, HOY)
    assert (leidas, cargadas) == (5, 2)
    with sqlite3.connect(db) as con:
        filas = con.execute("SELECT id_venta, monto FROM ventas ORDER BY id_venta").fetchall()
    assert filas == [(1, 100.5), (4, 75.0)]


# Reto 2: log de filas leídas frente a cargadas
def test_registra_filas_leidas_y_cargadas(tmp_path, caplog):
    with caplog.at_level(logging.INFO, logger="pipeline_ventas"):
        ejecutar("data/ventas.csv", tmp_path / "ventas.db", HOY)
    assert "filas leídas: 5 | cargadas: 2 | descartadas: 3" in caplog.text
