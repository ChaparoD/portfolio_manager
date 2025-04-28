# Proceso de postulación ABAQUS
Daniel chaparro
## Desafío

[Tarea de desarrollo](https://abaquscl.notion.site/Pregunta-t-cnica-d00b3f926b0845edaec7f198919c83d4#05fc6764f6454751886a5f15b5070323)


## Ejecución

#### Windows
1. Crear ambiente virtual.
```python -m venv venv```
2. Activar ambiente virtual.
```.\venv\Scripts\activate```
2. Instalar depencias.
```python -m pip install Django```

#### MacOS
1. Crear ambiente virtual.
```python -m venv venv```
2. Activar ambiente virtual.
```source ./venv/bin/activate```
2. Instalar Django.
```python -m pip install Django```


#### Runserver 
4. ``` (venv) $ cd portafolio```
5. ``` (venv) $ pip install -r requirements.txt```
6. ``` (venv) $ python manage.py migrate```
7. ``` (venv) $ python manage.py runserver```
8. ``` (venv) $ python manage.py run_etl```


Super User Credentials:
user : daniel
email : daniel@abaqus.cl
pwd : work_hardd


## Data Warehouse

#### Weights

```
http://127.0.0.1:8000/weights/?fecha_inicio=2023-02-11&fecha_fin=2023-02-13
```

#### Portfolio Values

```
http://127.0.0.1:8000/portfolio/?fecha_inicio=2023-02-11&fecha_fin=2023-02-13
```
#### Dimensions
##### dim_asset
    - name
    - initial_weight
    - quantity
    - portfolio_id


##### dim_portfolio
    - name
    - initial_value

### Facts
    - date
    - asset_id
    - price
    - asset_value

Se habilita Django rest framework para facilitar la navegación de la información disponible directamente en el modelo de datos propuesto. 
```
http://127.0.0.1:8000/facts/
```

## Direcciones

-   "http://127.0.0.1:8000/" = Django rest Api Root framework.
-   "http://127.0.0.1:8000/admin/" = Django Admin.
-   "http://127.0.0.1:8000/portfolio/?fecha_inicio=2023-02-12&fecha_fin=2023-02-12" = Get Portfolio values against "fecha_inicio" & "fecha_fin".
-   "http://127.0.0.1:8000/weights/?fecha_inicio=2023-02-12&fecha_fin=2023-02-12" = Asset weights for each date and portfolio.
-   "http://127.0.0.1:8000/asset_weights" = Stacked area asset weight graph.
-   "http://127.0.0.1:8000/portfolio_time_series" = Line portfolio value graph.


## SQL

#### Query daily portfolio value
```
SELECT fdp.date , dp.name  , SUM(fdp.weight) total_value 
FROM facts_daily_prices fdp 
JOIN dim_asset da on fdp.asset_id = da.id
JOIN dim_portafolio dp on da.portfolio_id = dp.id
GROUP by fdp.date, dp.name 
```
#### Query daily asset weights for each portfolio 
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

## Supuestos

- Se aproximaron los valores obtenidos al tercer decimal.
- Se construyó una tabla facts, simulando el proceso de obtención de precios de activos.
- Se sugiere construir una vista particular mediante una migración de query SQL, para la construcción de la variables "weight"

## Referencias
- https://realpython.com/get-started-with-django-1/