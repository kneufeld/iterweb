__version__      = "0.3.8"
__author__       = "Kurt Neufeld"
__author_email__ = "kneufeld@burgundywall.com"
__license__      = "MIT"
__url__          = "https://github.com/kneufeld/iterweb"

class DropItem(Exception):
    "drop item but not an error"

class DropItemError(Exception):
    "drop item and it's an error"

from .spider import Spider
from .pipeline import Pipeline
from .reqresp import Request, Response
