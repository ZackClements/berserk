# -*- coding: utf-8 -*-
import logging
import urllib
from typing import Any, Callable, Optional, Union

import requests

from . import exceptions, utils
from .formats import FormatHandler

LOG = logging.getLogger(__name__)


class Requestor:
    """Encapsulates the logic for making a request.

    :param session: the authenticated session object
    :type session: :class:`requests.Session`
    :param str base_url: the base URL for requests
    :param fmt: default format handler to use
    :type fmt: :class:`~berserk.formats.FormatHandler`
    """

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        default_fmt: FormatHandler,
    ) -> None:
        self.session = session
        self.base_url = base_url
        self.default_fmt = default_fmt

    def request(
        self,
        method: str,
        path: str,
        *args: Any,
        fmt: Optional[FormatHandler] = None,
        converter: Callable = utils.noop,
        **kwargs: Any,
    ) -> Union[map, str]:
        """Make a request for a resource in a paticular format.

        :param str method: HTTP verb
        :param str path: the URL suffix
        :param fmt: the format handler
        :type fmt: :class:`~berserk.formats.FormatHandler`
        :param func converter: function to handle field conversions
        :return: response
        :raises berserk.exceptions.ResponseError: if the status is >=400
        """
        fmt = fmt or self.default_fmt
        kwargs['headers'] = fmt.headers
        url = urllib.parse.urljoin(self.base_url, path)

        is_stream = kwargs.get('stream')
        LOG.debug(
            '%s %s %s params=%s data=%s json=%s',
            'stream' if is_stream else 'request',
            method,
            url,
            kwargs.get('params'),
            kwargs.get('data'),
            kwargs.get('json'),
        )
        try:
            response = self.session.request(method, url, *args, **kwargs)
        except requests.RequestException as e:
            raise exceptions.ApiError(e)
        if not response.ok:
            raise exceptions.ResponseError(response)

        return fmt.handle(response, is_stream=is_stream, converter=converter)

    def get(self, *args, **kwargs):
        """Convenience method to make a GET request."""
        return self.request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        """Convenience method to make a POST request."""
        return self.request('POST', *args, **kwargs)


class TokenSession(requests.Session):
    """Session capable of personal API token authentication.

    :param str token: personal API token
    """

    def __init__(self, token: str) -> None:
        super().__init__()
        self.token = token
        self.headers = {'Authorization': f'Bearer {token}'}
