__version__      = "0.0.1"
__author__       = "Kurt Neufeld"
__author_email__ = "kneufeld@burgundywall.com"
__license__      = "MIT"
__url__          = ""

class DropItem(Exception): pass

from .spider import Spider
from .reqresp import Request, Response
