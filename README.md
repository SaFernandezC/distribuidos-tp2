# Trabajo Practico 1 - Sistemas distribuidos

**1C 2023**



------



### **Ejecucion** 

Para ejecutar el programa se debe clonar o descargar el repositorio y tambien descargar el data set ([Data set](https://www.kaggle.com/datasets/jeanmidev/public-bike-sharing-in-north-america?resource=download)).

Se debe incluir el data set dentro del directorio `/data` en el cliente con la siguiente estructura:

```
- /client
    - /data
    	- /montreal
    		- trips.csv
    		- stations.csv
    		- weathers.csv
    	- /toronto
    		- trips.csv
    		- stations.csv
    		- weathers.csv
    	- /washington
    		- trips.csv
    		- stations.csv
    		- weathers.csv
```



Ademas es necesario modificar el `docker-compose-client.yaml` dentro del cliente para que pueda reconocer la network de docker donde se ejecutan los contenedores del servidor, para ello se debe indicar la red con el siguiente formato:

```
[nombre_directorio_raiz]_testing_net
```

De esta forma, si el directorio raiz (el que contiene tanto al cliente como al servidor) se llama `distribuidos-tp1` nuestro `docker-compose-client.yaml` quedaria de la siguiente forma:

```
version: '3'
services:
  client:
    container_name: client
    image: client:latest
    networks:
      - distribuidos-tp1_testing_net
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/data

networks:
  distribuidos-tp1_testing_net:
    external: true
```

 

Una vez realizados todos los cambios podemos abrir dos terminales y ejecutar el servidor y el cliente:

- Para el servidor ejecutar en el directorio donde se encuentra `docker-compose-dev.yaml`

```bash
make docker-compose-up
```

- Para el cliente ejecutar en el directorio donde se encuentra `docker-compose-client.yaml`

```bash
make docker-compose-up
```

**Observacion: Previo a iniciar el cliente el servidor debe estar corriendo**

- Para parar los servicios (tanto cliente como servidor)

```bash
make docker-compose-down
```

- Para ver los logs (tanto cliente como servidor)

```bash
make docker-compose-logs
```

------



### Escalamiento

Todos los componentes del servidor distribuido son escalables (excepto el accepter, groupby, eof manager y status controller) y se pueden ejecutar tantas instancias de cada componente como se desee. Se cuenta con un script para poder realizar el escalamiento de forma mas sencilla.

Para usar el script se debe ejecutar el archivo `create_compose.py`, con los siguientes parametros:

```bash
$ python3 create_compose.py [-h] [-ft_1 FILTER_TRIPS_1] [-ft_2 FILTER_TRIPS_2] [-ft_3 FILTER_TRIPS_3] [-fw_1 FILTER_WEATHER_1] [-fs_2 FILTER_STATION_2] [-fs_3 FILTER_STATION_3 [-j_1 JOINER_1] [-j_2 JOINER_2] [-j_3 JOINER_3] [-dm DATE_MODIFIER] [-dc DIST_CALCULATOR [-tp TRIP_PARSER] [-wp WEATHER_PARSER] [-sp STATION_PARSER]
```

Si alguno de de los campos no se indican el valor por defecto es 1.



