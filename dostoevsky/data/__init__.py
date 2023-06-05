import os
import lzma
import ssl
import typing
import tarfile
import urllib.request


DATA_BASE_PATH: str = os.path.dirname(os.path.abspath(__file__))
STORAGE_BASE_URL: str = 'https://storage.b-labs.pro/'


AVAILABLE_FILES: typing.Dict[str, typing.Tuple[str, str]] = {
    'cnn-social-network-model': ('models/cnn-social-network-model.tar.xz', 'models/cnn-social-network-model.tar.xz'),
    'fasttext-social-network-model': (
        'models/fasttext-social-network-model.tar.xz',
        'models/fasttext-social-network-model.tar.xz',
    ),
    'fasttext-toxic-model': ('models/fasttext-toxic-model.tar.xz', 'models/fasttext-toxic-model.tar.xz'),
}


class DataDownloader:

    USERAGENT: str = 'Dostoevsky / 1.0'
    CHUNK_SIZE: int = 1024 * 32

    def download(self, source: str, destination: str) -> int:
        destination_path: str = os.path.join(DATA_BASE_PATH, destination)
        url: str = os.path.join(STORAGE_BASE_URL, source)
        request = urllib.request.Request(url)
        request.add_header('User-Agent', self.USERAGENT)
        response = urllib.request.urlopen(request, context=self._ssl_context())
        with open(destination_path, 'wb') as output:
            filesize: int = 0
            while source:
                chunk = response.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                filesize += len(chunk)
                output.write(chunk)
        # assume that we always distribute data as .tar.xz archives
        with lzma.open(destination_path) as f:
            with tarfile.open(fileobj=f) as tar:
                tar.extractall(os.path.dirname(destination_path))
        return filesize

    @staticmethod
    def _ssl_context() -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
