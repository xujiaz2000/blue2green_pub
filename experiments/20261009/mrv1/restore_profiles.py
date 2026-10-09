"""Verify, merge and optionally extract the four profiling archives (Python 3.12+)."""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', default='profiling', type=pathlib.Path)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--extract-to', type=pathlib.Path)
    parser.add_argument('--archive-dir', type=pathlib.Path, help='Directory for merged archives (default: input directory)')
    args = parser.parse_args()
    if args.verify_only and args.extract_to:
        parser.error('--verify-only and --extract-to cannot be combined')
    if args.extract_to and sys.version_info < (3, 12):
        parser.error('Extraction requires Python 3.12+ for the tar data filter')
    folder = args.directory.resolve()
    archive_dir = (args.archive_dir or folder).resolve()
    if not args.verify_only:
        archive_dir.mkdir(parents=True, exist_ok=True)
    records = json.loads((folder/'archives.json').read_text(encoding='utf-8'))
    for record in records:
        name = record['file']
        assert pathlib.Path(name).name == name, 'Unsafe archive name'
        target = archive_dir/name
        temporary = archive_dir/(name+'.tmp')
        whole = hashlib.sha256()
        total = 0
        output = None if args.verify_only else temporary.open('wb')
        try:
            for part in record['parts']:
                partname = part['file']
                assert pathlib.Path(partname).name == partname, 'Unsafe part name'
                digest = hashlib.sha256()
                size = 0
                with (folder/partname).open('rb') as stream:
                    for chunk in iter(lambda:stream.read(1024*1024), b''):
                        digest.update(chunk)
                        whole.update(chunk)
                        size += len(chunk)
                        if output:
                            output.write(chunk)
                assert size == part['bytes'], 'Size mismatch: '+partname
                assert digest.hexdigest() == part['sha256'], 'SHA256 mismatch: '+partname
                total += size
            assert total == record['bytes'], 'Archive size mismatch: '+name
            assert whole.hexdigest() == record['sha256'], 'Archive SHA256 mismatch: '+name
        finally:
            if output:
                output.close()
        if not args.verify_only:
            temporary.replace(target)
        print('VERIFIED', name, total, 'bytes', flush=True)
        if args.extract_to:
            destination = args.extract_to.resolve()
            if os.name == 'nt' and not str(destination).startswith('\\\\?\\'):
                destination = pathlib.Path('\\\\?\\'+str(destination))
            destination.mkdir(parents=True, exist_ok=True)
            with tarfile.open(target, 'r:gz') as tar:
                members = tar.getmembers()
                if os.name == 'nt':
                    for member in members:
                        member.name = member.name.replace('/', os.sep)
                tar.extractall(destination, members=members, filter='data')
            files = json.loads((folder/(record['label']+'-files.json')).read_text(encoding='utf-8'))
            profile = (destination/record['label']/'profiling').resolve()
            for item in files:
                file = (profile/item['path']).resolve()
                assert file.is_relative_to(profile), 'Unsafe original file path'
                assert file.stat().st_size == item['bytes'], 'Extracted size mismatch: '+str(file)
                with file.open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256'], 'Extracted SHA256 mismatch: '+str(file)
            print('EXTRACTED_AND_VERIFIED', record['label'], len(files), 'files', flush=True)


if __name__ == '__main__':
    main()
