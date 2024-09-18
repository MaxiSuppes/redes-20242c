import socket

host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ip = ''
port = 12345

host.bind((ip, port))

host.listen(1)
print('Esperando conexiones...')

connection, address = host.accept()
print(f'Conexión nueva desde: {address}')

while True:
    data = connection.recv(1024)  # Tamaño del buffer
    if not data:
        break
    print(f'Datos recibidos: {data.decode()}')
    response = 'OK'
    connection.sendall(response.encode())

connection.close()
