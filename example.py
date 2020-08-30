from DriverLib import (
    AmazonDriver,
    AmericanasDriver,
    CasasBahiaDriver,
    GoogleShopDriver,
    KabumDriver,
    MagaLuDriver,
    PontoFrioDriver,
    Scan,
    ShoptimeDriver,
    SubmarinoDriver,
    get_browser,
)

# Example on automatically scan all implemented websites
# Set product name to scan
product = "my232bz"

# Initiate Scan Driver
scan = Scan()

# Scan product
out = scan.scan(product)
out

# Example on generic search on a website
# Initiate a browser
browser = get_browser(headless=True)
# Initiate the shop driver
sub = SubmarinoDriver(browser)
# Search
val = sub.get_product('TV 55" 4k', include=["qled", "oled"], or_include=True)
val_sub = sub.get_product(product)


# Example on search product on a specific website
# Set product name to scan
product = "50UM751C0SB"

ame = AmericanasDriver(browser)
val_ame = ame.get_product(product)

shp = ShoptimeDriver(browser)
val_shp = shp.get_product(product)

mag = MagaLuDriver(browser)
val_mag = mag.get_product(product)

kab = KabumDriver(browser)
val_kab = kab.get_product(product)

ptf = PontoFrio(browser)
val_ptf = ptf.get_product(product)

cba = CasasBahiaDriver(browser)
val_cba = cba.get_product(product)

amz = AmazonDriver(browser)
val_amz = amz.get_product(product)

gog = GoogleShopDriver(browser)
val_gog = gog.get_product(product)
