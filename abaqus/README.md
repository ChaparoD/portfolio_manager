# Proceso de postulación ABAQUS
### Nombre: Daniel Chaparro
## Desafío

[Tarea de desarrollo](https://abaquscl.notion.site/Pregunta-t-cnica-d00b3f926b0845edaec7f198919c83d4#05fc6764f6454751886a5f15b5070323)


## Ejecución


1. Crear ambiente virtual. 
``` abaqus %```
```python -m venv venv```
2. Activar ambiente virtual.
- Windows
```.\venv\Scripts\activate```
- MacOS
```source ./venv/bin/activate```
3. Instalar depencias.
```python -m pip install Django```




#### Levantar aplicación. 
4.  (venv) $ Entrar al proyecto Django : ```cd portfolio```
5.  (venv) $ Instalar depencias del proyecto: ```pip install -r requirements.txt```
6.  (venv) $ Construir BBDD y correr migraciones: ```python manage.py migrate```
7.  (venv) $ Levantar servidor: ```python manage.py runserver```
8.  (venv) $ Poblar BBDD: ```python manage.py run_etl```


#### Credenciales de super usuario.
```
user : daniel
email : daniel@abaqus.cl
pwd : work_hard
```

## Direcciones
Se habilita Django rest framework para facilitar la navegación de la información disponible directamente en el modelo de datos propuesto. 
No se configuró un puerto particular, si no que se utilizó el por defecto de django.

-   "http://127.0.0.1:8000/" = Django rest Api Root framework.
-   "http://127.0.0.1:8000/facts/" = Facts serializer view.
-   "http://127.0.0.1:8000/admin/" = Django Admin.
-   "http://127.0.0.1:8000/portfolio/?fecha_inicio=2023-02-12&fecha_fin=2023-02-12" = Get Portfolio values against "fecha_inicio" & "fecha_fin".
-   "http://127.0.0.1:8000/weights/?fecha_inicio=2023-02-12&fecha_fin=2023-02-12" = Asset weights for each date and portfolio.

### Ejemplos de acceso:

#### Portfolio Values
- assets/views.py / PortfolioValues / METHOD = 'GET':

```
http://127.0.0.1:8000/portfolio/?fecha_inicio=2023-02-11&fecha_fin=2023-02-13
```

#### Weights
- assets/views.py / AssetWeight / METHOD = 'GET':
```
http://127.0.0.1:8000/weights/?fecha_inicio=2023-02-11&fecha_fin=2023-02-13
```

### Bonus 1
Gráfico "Lineal" para comportamiento del valor total dentro de un portafolio en el tiempo.
```
   http://127.0.0.1:8000/portfolio_time_series
``` 
Gráfico "Stacked Area" para "weights" o bien participación (%) de activos dentro de un portafolio en el tiempo.
```
   http://127.0.0.1:8000/asset_weights
``` 
### Bonus 2

Herramienta de compra y venta de acciones. 
Al gatillar el submit para las acciones recopiladas:
1. Se guardará un snapshot de los valores de activos anteriores, con el fin de otorgar la posibilidad de analizar "Escenarios".
2. Se guardarán las transacciones.
3. Se actualizarán las cantidades asociadas a los activos.
4. Se actualizará todos los respectivos valores de "asset_value" pertenecientes a facts, los cuales esten asociados a las fechas desde la compra, para los activos y portafolios involucrados.
```
http://127.0.0.1:8000/transactions/
```
## Data Warehouse : Documentación
Visitar portfolio/assets/models.py

### Dimensiones
#### Asset  (_dim_asset_)
    - name
    - initial_weight
    - quantity
    - portfolio_id


#### Portfolio (_dim_portfolio_)
    - name
    - initial_value

### Tablas ETL 

#### Raw Daily Prices  (_raw_daily_prices_)
    - date
    - asset_id
    - price
    - asset_value
#### Facts Daily Prices (_fact_daily_prices_)
    - date
    - asset_name
    - price
    - asset_value
#### Facts Daily Prices Snapshot (_fact_daily_prices_snapshot_)
    - date
    - asset_name
    - price
    - asset_value
    - snapshot_date
#### Transactions (_raw_transactions_)
    - date
    - action
    - amount
    - asset
    - portfolio

### Modelo de datos

![alt text](./portfolio/assets/data/img/facts_model.png "Facts")
![alt text](./portfolio/assets/data/img/dim_asset_portfolio.png "Asset Dimension")
![alt text](./portfolio/assets/data/img/db_tables_extraction.png "DW")


## SQL

#### Query: Valores diarios para cada uno de los portafolios.
```
SELECT fdp.date , dp.name  , SUM(fdp.weight) total_value 
FROM facts_daily_prices fdp 
JOIN dim_asset da on fdp.asset_id = da.id
JOIN dim_portafolio dp on da.portfolio_id = dp.id
GROUP by fdp.date, dp.name 
```
#### Query: "Weights" diarios de cada activo/portafolio
```
SELECT 
    daily_prices.portfolio_name,
    daily_prices.asset_name,
    daily_prices.date,
    (daily_prices.asset_value / portfolios_values.total_value) AS weight
FROM (
    SELECT 
        fdp.date, 
        fdp.price, 
        da.name AS asset_name, 
        dp.id AS portfolio_id, 
        fdp.asset_value, 
        dp.name AS portfolio_name
    FROM 
        facts_daily_prices fdp 
    JOIN dim_asset da ON fdp.asset_id = da.id
    JOIN dim_portafolio dp ON da.portfolio_id = dp.id
) AS daily_prices
LEFT JOIN (
    SELECT 
        fdp.date, 
        dp.id AS portfolio_id, 
        dp.name, 
        SUM(fdp.asset_value) AS total_value
    FROM 
        facts_daily_prices fdp 
    JOIN dim_asset da ON fdp.asset_id = da.id
    JOIN  dim_portafolio dp ON da.portfolio_id = dp.id
    GROUP BY 
        fdp.date, 
        dp.name, 
        dp.id
) AS portfolios_values
ON 
    daily_prices.portfolio_id = portfolios_values.portfolio_id 
    AND daily_prices.date = portfolios_values.date;
```

### Supuestos

- Se aproximaron los valores obtenidos al tercer decimal.
- Se construyó una tabla facts, simulando el proceso de obtención de precios de activos por portafolio.
- Para Optimizar el proceso de obtención de "weights", se sugiere construir una vista particular, como la segunda query entregada en la parte superior, mediante una migración y el comando RunSQL, para la construcción de la variable "Weights" dependiente de Facts.  Sustituyendo parcialmente el uso del ORM para este caso particular. Y manteniendo actualizados los "weights" frente a cambios en Facts.
- Se guardaron snapshots de tablas de valores para cada conjunto de compras o ventas realizadas, con el fin de, a futuro, poder realizar comparaciones entre escenarios.

### Deuda técnica
- Manejar códigos HTTP de responses entre llamados de vistas, para todos los flujos.
- Styling a vistas de gráficos.
- Redirección luego de transacciones al gráfico de linea con los filtros pre definidos con la fecha de transacción dentro, para identificar la variación del valor del portfolio.
- Refactorizar llamados a url hardcodeado con IP por defecto, por variable de ambiente.
- Optimizar visualización Stacked Area para "weights".


## Referencias
- https://realpython.com/get-started-with-django-1/