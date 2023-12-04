import configparser

config = configparser.ConfigParser()

config.read('config.ini')

port_tcp = config.get("conncetion", "port_tcp")
port_udp = config.get("conncetion", "port_udp")