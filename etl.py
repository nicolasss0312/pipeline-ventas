import logging
import sqlite3

import pandas as pd

log = logging.getLogger("pipeline_ventas")


def extraer(ruta):
    return pd.read_csv(ruta)


def transformar(df, hoy=None):
    hoy = pd.Timestamp.today().normalize() if hoy is None else pd.Timestamp(hoy)
    df = df.dropna(subset=["id_venta", "monto"])
    df = df.drop_duplicates(subset="id_venta").copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["monto"] = df["monto"].astype(float)
    # Reto 1: una venta no puede tener fecha posterior a hoy.
    return df[(df["monto"] > 0) & (df["fecha"] <= hoy)]


def cargar(df, ruta_db):
    with sqlite3.connect(ruta_db) as con:
        df.to_sql("ventas", con, if_exists="replace", index=False)


def ejecutar(ruta_csv, ruta_db, hoy=None):
    crudo = extraer(ruta_csv)
    limpio = transformar(crudo, hoy)
    cargar(limpio, ruta_db)
    # Reto 2: registrar filas leídas frente a cargadas.
    log.info("filas leídas: %d | cargadas: %d | descartadas: %d",
             len(crudo), len(limpio), len(crudo) - len(limpio))
    return len(crudo), len(limpio)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    ejecutar("data/ventas.csv", "ventas.db")
