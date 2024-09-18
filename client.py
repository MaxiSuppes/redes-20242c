import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

host_ip = '10.0.0.1'  # IP del host en la red de Mininet
puerto = 12345
client.connect((host_ip, puerto))

message = 'Holaaaaa!'
client.sendall(message.encode())

response = client.recv(1024)
print(f'Respuesta del servidor: {response.decode()}')

client.close()
