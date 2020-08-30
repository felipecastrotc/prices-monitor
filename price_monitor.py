import argparse
from DriverLib import Scan


def main(product, exclude, include, or_include, filename):

    # Initiate Scan Driver
    scan = Scan()
    # Scan product
    out = scan.scan(product)
    # Organise dataframe
    out.sort_values(by="price", inplace=True)
    out.reset_index(inplace=True, drop=True)
    # Save prices
    out.to_excel("{}.xlsx".format(product))


if __name__ == "__main__":
    # Initialise parser
    parser = argparse.ArgumentParser(
        description="A command line version of a price monitor based on Selenium for some Brazillian shops"
    )

    # Arguments
    parser.add_argument(
        "--product",
        action="store",
        dest="product",
        required=True,
        help="Product to search/scan on websites",
    )

    parser.add_argument(
        "--exclude",
        action="store",
        dest="exclude",
        default=[],
        required=False,
        help='Used when search for generic product, such as TV, and you want to remove findings with certain terms, for instance, "LCD".',
    )

    parser.add_argument(
        "--include",
        action="store",
        dest="include",
        default=[],
        required=False,
        help='Used when search for generic product, such as TV, and you want to find products that contains certain terms, for instance, "4k".',
    )

    parser.add_argument(
        "--or-include",
        action="store",
        dest="or_include",
        default=False,
        required=False,
        help="Used when search for generic product, when True accepts having at least one term of include option",
    )

    parser.add_argument(
        "--filename",
        action="store",
        dest="Filename",
        default="product",
        required=False,
        help="File to store the output",
    )

    # Parse arguments
    arguments = parser.parse_args()

    # Set arguments
    product = arguments.product
    exclude = arguments.exclude
    include = arguments.include
    or_include = arguments.or_include

    filename = arguments.filename

    main(product, exclude, include, or_include, filename)
