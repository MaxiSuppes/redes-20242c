# Trabajo Práctico 1: File transfer
## Introducción a los Sistemas Distribuidos 75.43 - FIUBA
## Segundo Cuatrimestre 2024

## Informe
[Informe parcial](https://docs.google.com/document/d/1BjUDHfSUKQ9G3T0JJl2o70lr9v94gR4wcN5Qd0Qy0Tk/edit?usp=sharing)

## Prerequisitos
- Python 3.8 o superior
- pip
- virtualenv
- mininet
- xterm

## Instalación
Crear un virtualenv con python3 y activarlo:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Copiar el contenido del archivo `.env.example` a un nuevo archivo llamado `.env` y modificar las variables de entorno
según sea necesario.

## Ejecución
### Levantar la red
```bash
sudo python3 network.py
```

### Levantar hosts
La configuración por defecto de la red en mininet asume la existencia de 4 hosts. En el ejemplo de abajo se asume que
se quieren abrir un servidor y dos clientes.

```bash
xterm host_1 host_2 host_3
```

Esto va a abrir 3 terminales, una para cada host.

Nota: El tamaño de la fuente de la terminal por defecto es muy chico. Se puede modificar en el menu que se abre 
apretando CTRL y click derecho a la vez.

### Ejecutar servidor y clientes
En cada terminal, ejecutar el servidor y el cliente:

En el host_1:
```bash
python3 start_server.py [opciones]
```

Y para cada cliente, ejecutar en el host_n (n=2,3,...):
```bash
python3 download.py [opciones]
```


Esto va a iniciar el servidor en el host_1 y los clientes en el host_2 y host_3 respectivamente para efectuar la 
descarga del archivo solicitado. Se usarán los parámetros por defecto. Para cambiarlos se puede modificar el archivo 
`.env` o pasar los parámetros por la terminal.

Si se quiere realizar una subida de archivo cambiar el comando `download.py` por `upload.py`. 

Para conocer las opciones de ejecución de cada script, ejecutar `python3 start_server.py -h`, `python3 upload.py -h` o 
`python3 download.py -h`.

**Ejemplo:**

Iniciar el servidor configurando un directorio específico:
```bash
python3 start_server.py -s server_storage
```

Enviar un archivo al servidor:
```bash
python3 upload.py -s client_storage -n example.txt
```

Descargar un archivo desde servidor:
```bash
python3 download.py -d client_storage -n ejemplo.txt
```