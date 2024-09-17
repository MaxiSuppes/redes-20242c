from mininet.net import Mininet
from mininet.node import Controller
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel


def network():
    net = Mininet(controller=Controller, link=TCLink)
    net.addController('controller', ip='127.0.0.1', port=6653)

    client = net.addHost('host_1', ip='10.0.0.1')
    server = net.addHost('host_2', ip='10.0.0.2')

    switch = net.addSwitch('switch', dpid='0000000000000001')  # El Datapath ID (dpid) es como la IP del switch

    net.addLink(client, switch)
    net.addLink(server, switch)

    net.start()
    net.pingAll()

    CLI(net)

    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    network()
