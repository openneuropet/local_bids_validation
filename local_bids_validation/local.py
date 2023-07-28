from argparse import ArgumentParser
from bids_validator import BIDSValidator
from os import walk
from typing import Union
from pathlib import Path
import subprocess


def collect_data_set(curl_download_file):
    """
    Collect the data set from the curl download file.
    """
    subprocess.run(["curl", "-O", curl_download_file])


def make_manifest(input_folder: Union[str, Path]) -> list:
    """
    Make a manifest of all the file within the input folder.
    """
    manifest = []
    for root, dirs, files in walk(input_folder):
        for file in files:
            manifest.append(str(Path(root) / file))
    return manifest


def check_bids_valid(manifest: list) -> dict:
    """
    Check if the manifest is a valid bids folder.
    """
    validity = {}
    validator = BIDSValidator()
    for file in manifest:
        validity[file] = {'ValidBids': validator.is_bids(file), 'bidsignored': False}
    return validity


def search_bidsignore(input_folder:Union[str, Path]):
    """
    Search for .bidsignore file in the current directory and all its parents.
    """
    pass
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input-folder", help="input folder to check for bids files", type=str)
    args = parser.parse_args()
    manifest = make_manifest(args.input_folder)
    check_if_valid = check_bids_valid(manifest)
    print("stop")