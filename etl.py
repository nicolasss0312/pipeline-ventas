import sqlite3

import pandas as pd


def extraer(ruta):
    return pd.read_csv(ruta)


def transformar(df):
    df = df.dropna(subset=["id_venta", "monto"])
    df = df.drop_duplicates(subset="id_venta").copy()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["monto"] = df["monto"].astype(float)
    return df[df["monto"] > 0]


def cargar(df, ruta_db):
    with sqlite3.connect(ruta_db) as con:
        df.to_sql("ventas", con, if_exists="replace", index=False)


if __name__ == "__main__":
    cargar(transformar(extraer("data/ventas.csv")), "ventas.db")
