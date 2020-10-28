import argparse as ap
import logging

from os.path import isdir
from sys import exit

from PyQt5.QtWidgets import QApplication

from jester.classifier import CandClassifier as CandClass

logger = logging.getLogger()

def main():

    parser = ap.ArgumentParser(description="Classifier for MeerTRAP",
                               usage="%(prog)s <options>")

    parser.add_argument("-d", "--directory", help="Input data directory", 
                        required=True,
                        type=str)
    parser.add_argument("-e", "--extension", help="Plot extension",
                        required=False,
                        type=str,
                        default="png")

    arguments = parser.parse_args()

    if not isdir(arguments.directory):
        logger.error(f"Directory {arguments.directory} does not exist!")
        exit()

    app = QApplication([])
    cc = CandClass(arguments.directory, arguments.extension)

    try:
        # Just don't run with Python 2.x
        app.exec()
    except Exception as exc:
        logger.error(exc)

if __name__ == "__main__":
    main()
