from argparse import ArgumentParser
from bids_validator import BIDSValidator
from os import walk, sep, listdir
from typing import Union
from pathlib import Path
import json
import subprocess


def collect_data_set(curl_download_file):
    """
    Collect the data set from the curl download file.
    """
    subprocess.run(["curl", "-O", curl_download_file])


def check_for_bids_validator_js():
    status = subprocess.run(["bids-validator", "-h"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
    if status == 0:
        return True
    else:
        return False


def report_number_of_files_bids_validator_js_found(input_folder: Union[str, Path]) -> int:
    if check_for_bids_validator_js:
        # run the js bids validator on the folder
        js = subprocess.check_output(["bids-validator", str(input_folder), "--json"])
        validator_output = json.loads(js)
        totalFiles = validator_output.get('summary', {}).get('totalFiles')
    else:
        raise FileNotFoundError("Unable to locate bids-validator, try installing from npm\n"
                                "npm install -g bids-validator")
    return totalFiles


def make_manifest(input_folder: Union[str, Path]) -> list:
    """
    Make a manifest of all the file within the input folder.
    """
    manifest = []
    for root, dirs, files in walk(input_folder):
        for file in files:
            # remove common path from input folder and manifest file
            full_file_path = Path(root) / file
            manifest.append(sep + str(full_file_path.relative_to(input_folder)))
    return manifest


def check_bids_valid(manifest: list) -> dict:
    """
    Check if the manifest contains ~valid~ bids file entities.
    """
    validity = {}
    validator = BIDSValidator()
    for file in manifest:
        validity[str(file)] = {'ValidBids': validator.is_bids(str(file)), 'bidsignored': False}
    return validity


def collect_bidsignored(input_folder: Union[str, Path]) -> list:
    """
    Search for .bidsignore file in the current directory and all its parents.
    """
    input_folder_contents = listdir(input_folder)
    if '.bidsignore' in input_folder_contents:
        with open(Path(input_folder) / '.bidsignore', 'r') as infile:
            ignored = infile.readlines()
            # strip newlines off of each entry in ignored
            ignored = [entry.strip() for entry in ignored]
    else:
        ignored = []
        print("No .bidsignore file found")

    return ignored


def determine_if_file_is_ignored(validity: dict, bidsignore: list) -> dict:
    """
    Given a dict from check_bids_valid, determine if the valid file falls under the scope of the .bidsignore file
    """
    for k, v in validity.items():
        print(f"{k}: {v}")



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input-folder", help="input folder to check for bids files", type=str)
    args = parser.parse_args()
    manifest = make_manifest(args.input_folder)
    check_if_valid = check_bids_valid(manifest)



    print("stop")