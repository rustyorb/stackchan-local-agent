import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'build_factory.py'
class FactoryBuildTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('build_factory', SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_local_endpoint_rejects_public_or_loopback_hosts(self):
        for host in ['127.0.0.1', '8.8.8.8', 'localhost', 'api.tenclass.net', '192.168.1.1/evil']:
            with self.subTest(host=host), self.assertRaises(ValueError):
                self.m.endpoint_header(host, 8000)
        header = self.m.endpoint_header('192.168.1.20', 8000)
        self.assertIn('ws://192.168.1.20:8000/xiaozhi/v1/', header)
        self.assertNotIn('ota', header)

if __name__ == '__main__': unittest.main()
