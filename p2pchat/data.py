import configparser
from pathlib import Path
config = configparser.ConfigParser()
#doesn't seem to read relative paths correctly
c=config.read(Path(Path(__file__).parent,'cfg.ini'))
port_tcp = int(config.get("connection", "port_tcp"))
port_udp = int(config.get("connection", "port_udp"))
header_size=int(config.get("consts","header_size"))
