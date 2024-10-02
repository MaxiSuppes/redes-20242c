from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet


def network():
    net = Mininet(link=TCLink)
    net.addController('controller', ip='127.0.0.1', port=1024)

    server = net.addHost('host_1', ip='10.0.0.1')
    client_1 = net.addHost('host_2', ip='10.0.0.2')
    client_2 = net.addHost('host_3', ip='10.0.0.3')
    client_3 = net.addHost('host_4', ip='10.0.0.4')

    switch = net.addSwitch('switch', dpid='0000000000000001')  # El Datapath ID (dpid) es como la IP del switch

    net.addLink(server, switch)
    net.addLink(client_1, switch)
    net.addLink(client_2, switch)
    net.addLink(client_3, switch)

    net.start()
    net.pingAll()

    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    network()
