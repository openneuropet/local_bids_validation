from argparse import ArgumentParser
from bids_validator import BIDSValidator
from os import walk, sep, listdir, path
from typing import Union
from pathlib import Path
import json
import subprocess
import glob


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

    pop_index = []
    for entry in ignored:
        if entry.startswith('#'):
            pop_index.append(entry)
        elif entry == '':
            pop_index.append(entry)

    for index in pop_index:
        ignored.remove(index)

    return ignored


def expand_bids_ignored(ignored: list, root_path: Union[str, Path]) -> list:
    """given a bidsignore file, expand the entries to include all files that match the pattern"""
    expanded_paths = []
    for entry in ignored:
        if '*' in entry:
            matching_paths = glob.glob(str(Path(root_path) / entry))
            for path in matching_paths:
                if Path(path).is_dir():
                    # if the path is a directory, add a trailing slash
                    for root, dirs, files in walk(path):
                        for file in files:
                            expanded_paths.append(str(Path(root) / file))
                if Path(path).is_file():
                    expanded_paths.append(path)
        else:
            pass

    # create a set from the expanded paths to remove duplicates
    expanded_paths = set(expanded_paths)

    return list(expanded_paths)


def determine_ignored_files(validity: dict, bidsignore: list, print_output=False) -> dict:
    """
    Given a dict from check_bids_valid, determine if the valid file falls under the scope of the .bidsignore file
    """
    common_path = path.commonpath(bidsignore)
    all_bids_ignored = expand_bids_ignored(bidsignore, common_path)

    for key in validity.keys():
        for ignored in all_bids_ignored:
            if key in ignored:
                validity[key]['bidsignored'] = True

        # count the number of valid but ignored files
    valid_and_ignored = []
    valid_bids_files = []
    valid_bids_files_not_ignored = []
    invalid_bids_files_and_ignored = []
    invalid_and_not_ignored = []

    for k, v in validity.items():
        if v['ValidBids'] and v['bidsignored']:
            valid_and_ignored.append(k)
        if v['ValidBids']:
            valid_bids_files.append(k)
        if v['ValidBids'] and not v['bidsignored']:
            valid_bids_files_not_ignored.append(k)
        if not v['ValidBids'] and v['bidsignored']:
            invalid_bids_files_and_ignored.append(k)
        if not v['ValidBids'] and not v['bidsignored']:
            invalid_and_not_ignored.append(k)

    output = {
        'valid_and_ignored': valid_and_ignored,
        'valid_bids_files': valid_bids_files,
        'valid_bids_files_not_ignored': valid_bids_files_not_ignored,
        'invalid_bids_files_and_ignored': invalid_bids_files_and_ignored,
        'invalid': invalid_and_not_ignored
    }

    if print_output:
        for k, v in output.items():
            print(f"Found {len(v)} files that are {k}")
            for file in v:
                print(file)
            print("\n")

    return output


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("input-folder", help="input folder to check for bids files", type=str)
    parser.add_argument("--show-valid-and-ignored", help="show all valid and ignored files", action="store_true")
    parser.add_argument("--show-valid-bids-files", help="show all valid bids files", action="store_true")
    parser.add_argument("--show-valid-bids-files-not-ignored", help="show all valid bids files that are not ignored",
                        action="store_true")
    parser.add_argument("--show-invalid-bids-files-and-ignored", help="show all invalid bids files that are ignored",
                        action="store_true")
    parser.add_argument("--show-invalid-and-not-ignored", help="show all invalid and ignored files", action="store_true")

    args = parser.parse_args()
    manifest = make_manifest(args.input_folder)
    check_if_valid = check_bids_valid(manifest)
    bidsignore = collect_bidsignored(args.input_folder)
    output = determine_ignored_files(check_if_valid, bidsignore, print_output=False)
    if not args.show_valid_and_ignored and not args.show_valid_bids_files and not args.show_valid_bids_files_not_ignored and not args.show_invalid_bids_files_and_ignored and not args.show_invalid_and_ignored:
        output = determine_ignored_files(check_if_valid, bidsignore, print_output=True)
    elif args.show_valid_and_ignored:
        print("Found the following valid and ignored files:")
        for file in output.get('valid_and_ignored'):
            print(file)
    elif args.show_valid_bids_files:
        print("Found the following valid bids files:")
        for file in output.get('valid_bids_files'):
            print(file)
    elif args.show_valid_bids_files_not_ignored:
        print("Found the following valid bids files that are not ignored:")
        for file in output.get('valid_bids_files_not_ignored'):
            print(file)
    elif args.show_invalid_bids_files_and_ignored:
        print("Found the following invalid bids files that are ignored:")
        for file in output.get('invalid_bids_files_and_ignored'):
            print(file)
    elif args.show_invalid_and_ignored:
        print("Found the following invalid and ignored files:")
        for file in output.get('invalid'):
            print(file)
    else:
        pass

