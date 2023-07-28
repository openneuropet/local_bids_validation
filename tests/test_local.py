from local_bids_validation import local
import pytest
import shutil
import subprocess
from pathlib import Path


# create a temporary folder with a few files in it as a pytest fixture
@pytest.fixture
def tmp_bids_dir(tmpdir):
    # copy over bash download script from one level above and run it
    download_script = "ds004564-1.0.1.sh"
    tmp_download_script = tmpdir / download_script
    cp_file = Path(__file__).parent.parent / download_script
    shutil.copy(cp_file, tmp_download_script)
    subprocess.run(["bash", download_script], cwd=tmpdir)
    return tmpdir


def test_make_manifest(tmp_bids_dir):
    manifest = local.make_manifest(tmp_bids_dir)
    assert len(manifest) == 11


def test_check_bids_valid(tmp_bids_dir):
    manifest = local.make_manifest(tmp_bids_dir)
    check_if_valid = local.check_bids_valid(manifest)
    valid_bids_files = []
    invalid_bids_files = []
    for file, validity in check_if_valid.items():
        if validity['ValidBids']:
            valid_bids_files.append(file)
        if not validity['ValidBids']:
            invalid_bids_files.append(file)
    assert len(valid_bids_files) == 10
    assert len(invalid_bids_files) == 1
