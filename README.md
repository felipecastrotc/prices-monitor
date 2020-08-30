# Prices monitor

Small library to scan websites for the price of a product. It is mainly focused for the Brazilian market. The functions and base classes can be easily extended for other markets.

## Installation

There is no PyPI package available. However, it is quite simple to install and use just run the following command:

```bash
git clone https://github.com/felipecastrotc/prices-monitor.git
```

After cloning the repository, just copy the `DriverLib.py` into your project folder. If you want a simpler method, just copy the `DriverLib.py` directly from the GitHub repository into your project folder.

## Usage

A simple example on how to use the script.

```python
from DriverLib import Scan

# Set product name to scan
product = "my232bz"

# Initiate Scan Driver
scan = Scan()

# Scan product
out = scan.scan(product)
```

A more complete example can be found at [`example.py`](example.py)


## License

[GPLv3](https://choosealicense.com/licenses/gpl-3.0/)