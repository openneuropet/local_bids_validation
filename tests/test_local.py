from local_bids_validation import local
import pytest
import shutil
import subprocess
from pathlib import Path
import os

# create a temporary folder with a few files in it as a pytest fixture
@pytest.fixture(scope="session")
def tmp_bids_dir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("bids")
    # copy over bash download script from one level above and run it
    download_script = "ds004564-1.0.1.sh"
    tmp_download_script = Path(tmpdir) / download_script
    cp_file = Path(__file__).parent.parent / download_script
    shutil.copy(cp_file, tmp_download_script)
    subprocess.run(["bash", download_script], cwd=tmpdir)
    # remove the temporary download script with shutil
    tmp_download_script.unlink()
    return tmpdir


def test_make_manifest(tmp_bids_dir):
    manifest = local.make_manifest(tmp_bids_dir)
    assert len(manifest) == 10


def test_bids_validator_js(tmp_bids_dir):
    total_files = local.report_number_of_files_bids_validator_js_found(tmp_bids_dir)
    assert total_files == 10


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
    assert len(invalid_bids_files) == 0


def test_collect_bids_ignored(tmp_bids_dir):
    manifest = local.make_manifest(tmp_bids_dir)
    shutil.copy(Path(__file__).parent / "testdata" / ".bidsignore", tmp_bids_dir)
    bids_ignored = local.collect_bidsignored(tmp_bids_dir)
    assert 'test_folder' in bids_ignored
    assert 'test_folder/test_file.txt' in bids_ignored
    assert 'random_file.txt' in bids_ignored


def test_add_in_valid_bids_and_ignore(tmp_bids_dir):
    # copy over subjects from testdata folder
    shutil.copytree(Path(__file__).parent / "testdata" / 'eeg_matchingpennies' / 'sub-05', tmp_bids_dir / "sub-05")
    shutil.copytree(Path(__file__).parent / "testdata" / 'eeg_matchingpennies' / 'sub-06', tmp_bids_dir / "sub-06")
    # update bidsignore to include sub-05 and sub-06
    with open(Path(tmp_bids_dir / '.bidsignore'), 'w') as outfile:
        outfile.write('sub-05\n')
        outfile.write('sub-06\n')
    # create a new manifest
    manifest = local.make_manifest(tmp_bids_dir)
    bids_ignored = local.collect_bidsignored(tmp_bids_dir)
    check_if_valid = local.check_bids_valid(manifest)
    valid_bids_files = []
    invalid_bids_files = []
    for file, validity in check_if_valid.items():
        if validity['ValidBids']:
            valid_bids_files.append(file)
        if not validity['ValidBids']:
            invalid_bids_files.append(file)

    num_bids_validator_found = local.report_number_of_files_bids_validator_js_found(tmp_bids_dir)

    assert len(valid_bids_files) == 20
    assert len(valid_bids_files) != num_bids_validator_found
    assert len(invalid_bids_files) == 1 and invalid_bids_files[0] == os.sep + '.bidsignore'
