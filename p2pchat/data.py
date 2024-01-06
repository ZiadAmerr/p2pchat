import configparser
from pathlib import Path

config = configparser.ConfigParser()
# doesn't seem to read relative paths correctly

# config.read(Path(Path(__file__).parent, "cfg.ini"))

port_tcp = 15600
port_udp = 15500
header_size = 10
max_udp_packet_size = 4096
