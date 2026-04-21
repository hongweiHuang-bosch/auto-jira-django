import re
import tarfile
from pathlib import Path


_CYCLE_PATTERN = re.compile(r'cycle_(\d+)')
_TIMESTAMP_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')


def recursive_unpack_archives(root_dir: Path):
    pending = list(root_dir.rglob('*.tgz')) + list(root_dir.rglob('*.tar.gz'))
    unpacked = []
    while pending:
        archive_path = pending.pop()
        target_dir = archive_path.with_suffix('')
        if target_dir.suffix == '.tar':
            target_dir = target_dir.with_suffix('')
        target_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, 'r:*') as archive:
            archive.extractall(target_dir, filter='data')
        unpacked.append(target_dir)
        pending.extend(list(target_dir.rglob('*.tgz')))
        pending.extend(list(target_dir.rglob('*.tar.gz')))
    return unpacked


def select_latest_cycles(cycle_paths, limit=5):
    scored = []
    for cycle_path in cycle_paths:
        match = _CYCLE_PATTERN.search(cycle_path.name)
        if match:
            scored.append((int(match.group(1)), cycle_path))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [path for _, path in scored[:limit]]


def collect_bosch_signal_logs(cycle_paths, signals):
    upper_signals = [signal.upper() for signal in signals]
    grouped = {}
    for cycle_path in cycle_paths:
        matches = []
        for log_file in cycle_path.rglob('Bosch*'):
            if not log_file.is_file():
                continue
            for raw_line in log_file.read_text(encoding='utf-8', errors='ignore').splitlines():
                if not _TIMESTAMP_PATTERN.match(raw_line):
                    continue
                if upper_signals and not any(signal in raw_line.upper() for signal in upper_signals):
                    continue
                matches.append({'timestamp': raw_line[:23], 'file': str(log_file), 'line': raw_line})
        grouped[cycle_path.name] = sorted(matches, key=lambda item: item['timestamp'])
    return grouped
