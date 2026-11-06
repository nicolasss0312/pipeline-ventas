# pipeline-ventas

![CI](https://github.com/nicolasss0312/pipeline-ventas/actions/workflows/ci.yml/badge.svg)

Pipeline ETL de ventas en Python: lee un CSV diario con datos sucios, aplica reglas de calidad y carga el resultado en SQLite. Cada `push` dispara pruebas automáticas y el pipeline completo en GitHub Actions.

**Autores:** Nicolás Cuervo · Jacobo Ramirez · Arquitectura de Datos · DevOps

## Ejecutar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v        # 8 pruebas
python etl.py              # genera ventas.db
# o con Docker
docker build -t pipeline-ventas . && docker run --rm pipeline-ventas
```

## Informe · Reglas de calidad y decisiones

### Reglas de calidad (`transformar`)

| # | Regla | Implementación | Prueba |
|---|---|---|---|
| 1 | Sin `id_venta` ni `monto` vacíos | `dropna(subset=["id_venta", "monto"])` | `test_sin_duplicados_ni_nulos`, `test_montos_vacios_y_cero_se_descartan` |
| 2 | Una venta por `id_venta` | `drop_duplicates(subset="id_venta")` | `test_sin_duplicados_ni_nulos` |
| 3 | Tipos correctos | `fecha` como fecha, `monto` como número decimal | `test_tipos_convertidos` |
| 4 | Monto estrictamente positivo | `monto > 0` (el 0 también se descarta) | `test_montos_positivos` |
| 5 | **Reto 1:** sin fechas futuras | `fecha <= hoy` | `test_rechaza_ventas_con_fecha_futura` |

Con `data/ventas.csv` se **leen 5 filas y se cargan 2** (ventas 1 y 4). Se descartan: el duplicado de la venta 2, la venta 2 por monto negativo y la venta 3 por monto vacío.

### Decisiones tomadas

- **Carga idempotente.** `to_sql(if_exists="replace")` reemplaza la tabla en cada ejecución, así que reprocesar el mismo archivo no duplica datos (`test_carga_es_idempotente`).
- **"Hoy" como parámetro.** `transformar(df, hoy=None)` usa la fecha actual por defecto, pero las pruebas fijan `hoy`. Si dependieran del reloj, una prueba pasaría hoy y fallaría mañana.
- **El día de hoy es válido.** Una venta con fecha de hoy se conserva; solo se rechazan las posteriores.
- **Observabilidad (reto 2).** `ejecutar()` registra `filas leídas | cargadas | descartadas`. Es la métrica de **volumen** de los 5 pilares: si un día se descarta casi todo, el log lo deja ver.
- **Datos inválidos detienen el pipeline.** Una fecha con formato inválido hace fallar `pd.to_datetime` en vez de cargarse en silencio.
- **Limitación conocida.** Los duplicados se eliminan antes de filtrar montos. Si la primera aparición de un `id` fuera inválida y la segunda válida, se perdería la venta. Con los datos actuales los duplicados son idénticos.
- **Versiones fijadas** en `requirements.txt` (pandas 3.1.1, pytest 9.2.0) para que el CI y la máquina local den el mismo resultado.

### Integración continua (`.github/workflows/ci.yml`)

1. **Job `pruebas`:** Ubuntu limpio con Python 3.12; instala dependencias, ejecuta `pytest` y, si todo pasa, corre `python etl.py`.
2. **Job `docker` (reto 3):** solo corre si `pruebas` pasó (`needs`). Construye la imagen del `Dockerfile` y ejecuta el pipeline en el contenedor.
3. **Reto 4:** se rompió una prueba a propósito y el CI quedó **en rojo**; el job `docker` ni siquiera arrancó. Tras corregirla volvió a verde. Ambas ejecuciones están en la pestaña *Actions*.
