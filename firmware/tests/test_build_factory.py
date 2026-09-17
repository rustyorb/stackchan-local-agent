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
                self.m.endpoint_header(host, 8000, "a" * 64)
        header = self.m.endpoint_header('192.168.1.20', 8000, 'a' * 64)
        self.assertIn('wss://192.168.1.20:8000/xiaozhi/v1/', header)
        self.assertNotIn('ota', header)

if __name__ == '__main__': unittest.main()

class SecureBuildTests(FactoryBuildTests):
    def test_runner_keeps_shell_metacharacters_literal(self):
        import sys
        payload = '$(touch should-not-exist); & echo untrusted'
        result = self.m.run([sys.executable, '-c', 'import sys; print(sys.argv[1])', payload], capture=True)
        self.assertEqual(result.stdout.strip(), payload)
        with self.assertRaises(ValueError):
            self.m.run(['sh', '-c', 'echo untrusted'])

    def test_tls_config_overrides_stale_insecure_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fw = root / 'firmware'; (fw / 'main').mkdir(parents=True)
            build = fw / 'build-stakia'; build.mkdir()
            security = root / 'security'; security.mkdir()
            (security / 'ca.pem').write_text('test public certificate')
            (build / 'sdkconfig').write_text('CONFIG_ESP_TLS_INSECURE=y\nCONFIG_MBEDTLS_CERTIFICATE_BUNDLE_DEFAULT_FULL=y\n')
            self.m.configure_tls(fw, build, security)
            config = (build / 'sdkconfig').read_text()
            self.assertIn('CONFIG_ESP_TLS_INSECURE=n', config)
            self.assertIn('CONFIG_MBEDTLS_CERTIFICATE_BUNDLE_DEFAULT_NONE=y', config)
            self.assertNotIn('CONFIG_MBEDTLS_CERTIFICATE_BUNDLE_DEFAULT_FULL=y', config)
            self.assertEqual((fw / 'main/stakia_ca.pem').read_text(), 'test public certificate')
