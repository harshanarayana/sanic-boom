from cgi import parse_header
from http.cookies import SimpleCookie
from io import BytesIO
from urllib.parse import parse_qs, urlunparse

from httptools import parse_url
from multidict import istr
from sanic.exceptions import InvalidUsage
from sanic.log import error_logger
from sanic.request import (
    DEFAULT_HTTP_CONTENT_TYPE,
    RequestParameters,
    json_loads,
    parse_multipart_form,
)
from sanic_ipware import get_client_ip


# --------------------------------------------------------------------------- #
# used headers
# --------------------------------------------------------------------------- #

_H_CONTENT_TYPE = istr("content-type")
_H_COOKIE = istr("cookie")
_H_UPGRADE = istr("upgrade")
_H_HOST = istr("host")

# --------------------------------------------------------------------------- #
# the request class
# --------------------------------------------------------------------------- #


class BoomRequest(dict):
    """Properties of an HTTP request such as URL, headers, etc."""

    __slots__ = (
        "__weakref__",
        "_body",
        "_cookies",
        "_ip",
        "_path",
        "_parsed_url",
        "_port",
        "_query_string",
        "_remote_addr",
        # "_route_handlers",
        # "_route_params",
        "_socket",
        "_scheme",
        "_app",
        "body",
        "headers",
        "method",
        "parsed_args",
        "parsed_files",
        "parsed_form",
        "parsed_json",
        "raw_url",
        "stream",
        "transport",
        "uri_template",
        "version",
    )

    def __init__(self, url_bytes, headers, version, method, transport):
        self.raw_url = url_bytes
        # TODO: see https://github.com/huge-success/sanic/issues/1329
        self._parsed_url = parse_url(url_bytes)
        # self.app = None

        self.headers = headers
        self.version = version
        self.method = method
        self.transport = transport
        self.stream = None

    def __has(self, key):
        return hasattr(self, key)

    def __repr__(self):
        if self.method is None or not self.path:
            return "<Request>"
        return "<Request: {1} {2}>".format(self.method, self.path)

    def __bool__(self):
        if self.transport:
            return True
        return False

    # ----------------------------------------------------------------------- #
    # methods
    # ----------------------------------------------------------------------- #

    def body_append(self, data):
        if not self.__has("_body"):
            self._body = BytesIO()
        if self._body.closed:
            raise IOError("the body is already closed")  # TODO fix
        self._body.write(data)

    def body_finish(self):
        if self.__has("_body"):
            self.body = self._body.getvalue()
            self._body.close()
        else:
            self.body = b""

    # ----------------------------------------------------------------------- #
    # properties
    # ----------------------------------------------------------------------- #

    @property
    def app(self):
        if self.__has("_app"):
            return self._app
        return None

    @app.setter
    def app(self, value):
        if self.app is None:
            self._app = value

    # @property
    # def route_params(self):
    #     if self.__has("_route_params"):
    #         return self._route_params
    #     return None

    # @route_params.setter
    # def route_params(self, value):
    #     if self.route_params is None:
    #         self._route_params = value

    # @property
    # def route_handlers(self):
    #     if self.__has("_route_handlers"):
    #         return self._route_handlers
    #     return None

    # @route_handlers.setter
    # def route_handlers(self, value):
    #     if self.route_handlers is None:
    #         self._route_handlers = value

    @property
    def json(self):
        if not self.__has("parsed_json"):
            self._load_json()

        return self.parsed_json

    @property
    def form(self):
        if not self.__has("parsed_form"):
            self.parsed_form = RequestParameters()
            self.parsed_files = RequestParameters()
            content_type = self.headers.get(
                _H_CONTENT_TYPE, DEFAULT_HTTP_CONTENT_TYPE
            )
            content_type, parameters = parse_header(content_type)
            try:
                if content_type == "application/x-www-form-urlencoded":
                    self.parsed_form = RequestParameters(
                        parse_qs(self.body.decode("utf-8"))
                    )
                elif content_type == "multipart/form-data":
                    # TODO: Stream this instead of reading to/from memory
                    boundary = parameters["boundary"].encode("utf-8")
                    self.parsed_form, self.parsed_files = parse_multipart_form(
                        self.body, boundary
                    )
            except Exception:
                error_logger.exception("Failed when parsing form")

        return self.parsed_form

    @property
    def files(self):
        if not self.__has("parsed_files"):
            self.form  # compute form to get files

        return self.parsed_files

    @property
    def args(self):
        if not self.__has("parsed_args"):
            if self.query_string:
                self.parsed_args = RequestParameters(
                    parse_qs(self.query_string)
                )
            else:
                self.parsed_args = RequestParameters()
        return self.parsed_args

    @property
    def raw_args(self):
        return {k: v[0] for k, v in self.args.items()}

    @property
    def cookies(self):
        if not self.__has("_cookies"):
            cookie = self.headers.get(_H_COOKIE)
            if cookie is not None:
                cookies = SimpleCookie()
                cookies.load(cookie)
                self._cookies = {
                    name: cookie.value for name, cookie in cookies.items()
                }
            else:
                self._cookies = {}
        return self._cookies

    @property
    def ip(self):
        if not self.__has("_socket"):
            self._get_address()
        return self._ip

    @property
    def port(self):
        if not self.__has("_socket"):
            self._get_address()
        return self._port

    @property
    def socket(self):
        if not self.__has("_socket"):
            self._get_address()
        return self._socket

    def _load_json(self, loads=json_loads):
        try:
            self.parsed_json = loads(self.body)
        except Exception:
            if not self.body:
                return
            raise InvalidUsage("Failed parsing the body as json")

    def _get_address(self):
        self._socket = self.transport.get_extra_info("peername") or (
            None,
            None,
        )
        self._ip, self._port = self._socket[0], self._socket[1]

    @property
    def remote_addr(self):
        if not self.__has("_remote_addr"):
            proxy_count = None
            proxy_trusted_ips = None
            request_header_order = None
            if self.app and self.app.config:
                proxy_count = getattr(
                    self.app.config, "IPWARE_PROXY_COUNT", None
                )
                proxy_trusted_ips = getattr(
                    self.app.config, "IPWARE_PROXY_TRUSTED_IPS", None
                )
                request_header_order = getattr(
                    self.app.config, "IPWARE_REQUEST_HEADER_ORDER", None
                )
            ip, _ = get_client_ip(
                self,
                proxy_count=proxy_count,
                proxy_trusted_ips=proxy_trusted_ips,
                request_header_order=request_header_order,
            )
            self._remote_addr = ip
        return self._remote_addr

    @property
    def scheme(self):
        if not self.__has("_scheme"):
            if (
                self.app
                and self.app.websocket_enabled
                and self.headers.get(_H_UPGRADE) == "websocket"
            ):
                self._scheme = "ws"
            else:
                self._scheme = "http"

            if self.transport.get_extra_info("sslcontext"):
                self._scheme += "s"

        return self._scheme

    @property
    def host(self):
        # it appears that httptools doesn't return the host
        # so pull it from the headers
        return self.headers.get(_H_HOST, "")

    @property
    def content_type(self):
        return self.headers.get(_H_CONTENT_TYPE, DEFAULT_HTTP_CONTENT_TYPE)

    @property
    def path(self):
        if not self.__has("_path"):
            self._path = self._parsed_url.path.decode("utf-8")
        return self._path

    @property
    def query_string(self):
        if not self.__has("_query_string"):
            if self._parsed_url.query:
                self._query_string = self._parsed_url.query.decode("utf-8")
            else:
                self._query_string = ""
        return self._query_string

    @property
    def url(self):
        return urlunparse(
            (self.scheme, self.host, self.path, None, self.query_string, None)
        )
