import configparser
from pathlib import Path
config = configparser.ConfigParser()
#doesn't seem to read relative paths correctly
c=config.read(Path(Path(__file__).parent,'cfg.ini'))
port_tcp = config.get("connection", "port_tcp")
port_udp = config.get("connection", "port_udp")