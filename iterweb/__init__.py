__version__      = "0.1"
__author__       = "Kurt Neufeld"
__author_email__ = "kneufeld@burgundywall.com"
__license__      = "MIT"
__url__          = "https://github.com/kneufeld/iterweb"

class DropItem(Exception): pass

from .spider import Spider
from .reqresp import Request, Response
