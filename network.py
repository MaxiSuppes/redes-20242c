from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet

from src.settings import settings


def network():
    net = Mininet(link=TCLink)
    net.addController('controller', ip='127.0.0.1', port=1024)
    switch = net.addSwitch('switch', dpid='0000000000000001')  # El Datapath ID (dpid) es como la IP del switch

    server = net.addHost('host_1', ip='10.0.0.1')
    net.addLink(server, switch, loss=settings.network_loss_percentage())

    clients_ip = ['10.0.0.2', '10.0.0.3', '10.0.0.4']
    for index, client_ip in enumerate(clients_ip):
        host_number = index + 2  # Index empieza en 0 y tenemos que crear los hosts host_2, host_3, host_4
        client = net.addHost(f'host_{host_number}', ip=client_ip)
        net.addLink(client, switch, loss=settings.network_loss_percentage())

    net.start()
    net.pingAll()

    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    network()
