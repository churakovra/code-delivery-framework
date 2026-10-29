import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
import tarfile
import io
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release_verification', Path(__file__).resolve().parents[1]/'scripts/verify_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseVerificationTests(unittest.TestCase):
    def test_checksum_version_and_revision_must_match(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory)/'release.zip'
            revision = 'a' * 40
            with zipfile.ZipFile(archive, 'w') as output:
                output.writestr('cdf/pyproject.toml', '[project]\nversion = "0.3.0"\n')
                output.writestr('cdf/SOURCE_REVISION', revision+'\n')
            checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(release.verify(archive, checksum, '0.3.0', revision)['revision'], revision)
            for digest, version, ref in [('0'*64, '0.3.0', revision), (checksum, '0.2.0', revision), (checksum, '0.3.0', 'b'*40)]:
                with self.assertRaises(ValueError): release.verify(archive, digest, version, ref)

    def test_tar_and_source_path_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory)/'release.tar'
            replacement = Path(directory)/'replacement.tar'
            revision = 'a'*40
            with tarfile.open(archive, 'w') as output:
                for name, content in [('cdf/pyproject.toml', b'[project]\nversion="0.3.0"\n'), ('cdf/SOURCE_REVISION', revision.encode())]:
                    item = tarfile.TarInfo(name); item.size = len(content)
                    output.addfile(item, io.BytesIO(content))
            replacement.write_bytes(b'not the verified archive')
            checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
            original = release.zipfile.is_zipfile
            def replace_path(stream):
                replacement.replace(archive)
                return original(stream)
            with patch.object(release.zipfile, 'is_zipfile', side_effect=replace_path):
                self.assertEqual(release.verify(archive, checksum, '0.3.0', revision)['revision'], revision)

    def test_archive_root_identity_files(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory)/'root.tar'
            revision = 'b'*40
            with tarfile.open(archive, 'w') as output:
                for name, content in [('pyproject.toml', b'[project]\nversion="0.3.0"\n'), ('SOURCE_REVISION', revision.encode())]:
                    item = tarfile.TarInfo(name); item.size = len(content)
                    output.addfile(item, io.BytesIO(content))
            checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(release.verify(archive, checksum, '0.3.0', revision)['revision'], revision)
