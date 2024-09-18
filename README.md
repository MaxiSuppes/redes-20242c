## Trabajo Práctico 1: File transfer
### Introducción a los Sistemas Distribuidos 75.43 - FIUBA
### Segundo Cuatrimestre 2024

### Informe
[Informe parcial](https://docs.google.com/document/d/1BjUDHfSUKQ9G3T0JJl2o70lr9v94gR4wcN5Qd0Qy0Tk/edit?usp=sharing)

### Prerequisitos
- Python 3.8 o superior
- pip
- virtualenv
- mininet
- xterm

### Instalación
Crear un virtualenv con python3 y activarlo:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

### Instalación
#### Levantar la red
```bash
sudo python3 network.py
```

#### Levantar ambos hosts
```bash
xterm host_1 host_2
```
Esto va a abrir dos terminales, una para cada host.

#### Ejecutar cliente y servidor
En cada terminal, ejecutar el servidor y el cliente:

En el host_1:
```bash
python3 server.py
```

En el host_2:
```bash
python3 client.py
```

Esto va a iniciar el servidor en el host_1 y el cliente en el host_2. El cliente va a enviar un mensaje al servidor.

