import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

CATEGORIES: Dict[str, set] = {
    "Documents": {".txt", ".pdf", ".docx", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp"},
    "Audio": {".mp3", ".wav", ".flac", ".aac"},
    "Video": {".mp4", ".avi", ".mkv", ".mov"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
}
OTHER = "Other"
SERVICE_FILES = {".ds_store", "thumbs.db", "desktop.ini"}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Раскладывает файлы папки по категориям (Documents, Images, ...)."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        type=Path,
        help="папка для уборки (по умолчанию - текущая)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="только показать, что будет перемещено, ничего не менять",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="подробный вывод по каждому файлу"
    )
    return parser.parse_args(argv)


def get_category(suffix: str) -> str:
    suffix = suffix.lower()
    for category, extensions in CATEGORIES.items():
        if suffix in extensions:
            return category
    return OTHER


def resolve_conflict(dst: Path) -> Path:
    if not dst.exists():
        return dst
    counter = 1
    candidate = dst.with_stem(f"{dst.stem}_{counter}")
    while candidate.exists():
        counter += 1
        candidate = dst.with_stem(f"{dst.stem}_{counter}")
    return candidate


def plural_files(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        word = "файл"
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        word = "файла"
    else:
        word = "файлов"
    return f"{n} {word}"


def collect_files(directory: Path) -> List[Path]:
    script_name = Path(__file__).name
    return sorted(
        item
        for item in directory.iterdir()
        if item.is_file()
        and item.name != script_name
        and item.name.lower() not in SERVICE_FILES
    )


def organize(directory: Path, dry_run: bool = False, verbose: bool = False) -> Dict:
    stats: Dict = {
        "moved": {category: 0 for category in [*CATEGORIES, OTHER]},
        "skipped": 0,
        "renamed": 0,
    }
    files = collect_files(directory)
    if not files:
        stats["empty"] = True
        return stats

    if not dry_run:
        for category in stats["moved"]:
            (directory / category).mkdir(parents=True, exist_ok=True)

    for file in files:
        category = get_category(file.suffix)
        target = resolve_conflict(directory / category / file.name)
        conflict = target.name != file.name
        relative = f"{category}/{target.name}"

        if dry_run:
            print(f"[DRY-RUN] {file.name:<16} -> {relative}")
            stats["moved"][category] += 1
            stats["renamed"] += int(conflict)
            continue

        try:
            shutil.move(str(file), str(target))
        except (OSError, shutil.Error) as error:
            print(f"Ошибка:     {file.name} -> {relative} ({error})")
            stats["skipped"] += 1
            continue

        stats["moved"][category] += 1
        stats["renamed"] += int(conflict)
        if verbose:
            if conflict:
                print(f"Конфликт:   {file.name} -> {relative} (переименовано)")
            else:
                print(f"Перемещено: {file.name} -> {relative}")
    return stats


def print_report(directory: Path, stats: Dict, dry_run: bool) -> None:
    if dry_run:
        print("Ничего не изменено")
        return
    print(f"Обработка директории: {directory}")
    for category, count in stats["moved"].items():
        print(f"  {category + ':':<10} {plural_files(count)}")
    print(f"Итого перемещено: {sum(stats['moved'].values())}")
    if stats["renamed"]:
        print(f"Из них переименовано из-за конфликта имён: {stats['renamed']}")
    print(f"Пропущено: {stats['skipped']}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    directory: Path = args.directory.resolve()
    if not directory.exists():
        print(f"Ошибка: путь не существует: {directory}", file=sys.stderr)
        return 1
    if not directory.is_dir():
        print(f"Ошибка: это не директория: {directory}", file=sys.stderr)
        return 1

    stats = organize(directory, dry_run=args.dry_run, verbose=args.verbose)
    if stats.get("empty"):
        print(f"В директории нет файлов для обработки: {directory}")
        return 0
    print_report(directory, stats, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
