__version__      = "0.1"
__author__       = "Kurt Neufeld"
__author_email__ = "kneufeld@burgundywall.com"
__license__      = "MIT"
__url__          = ""

# from .engine import Engine
from .spider import Spider
from .http import Request
from .http import Response, TextResponse, HtmlResponse, XmlResponse
