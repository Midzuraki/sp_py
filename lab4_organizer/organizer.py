"""ЛР4. Автоматический «Уборщик» файловой системы (только модули os и sys).

Запуск:
    python organizer.py [путь_к_папке]
Если путь не указан, берётся текущая рабочая директория.
Код возврата: 0 - всё в порядке, 1 - путь не существует / не папка.
"""
import os
import sys

# Категории и расширения (в нижнем регистре, с точкой)
CATEGORIES = {
    "Documents": {".txt", ".pdf", ".docx", ".md"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp"},
    "Audio": {".mp3", ".wav", ".flac", ".aac"},
    "Video": {".mp4", ".avi", ".mkv", ".mov"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
}
OTHER = "Other"  # всё, что не попало в категории выше
SERVICE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def get_target_directory() -> str:
    """Разбор sys.argv: путь к папке или текущая директория, если аргумента нет.

    Если путь содержит пробелы и пользователь забыл кавычки, shell разобьёт его
    на несколько аргументов - склеиваем их обратно через пробел.
    """
    if len(sys.argv) > 1:
        path = " ".join(sys.argv[1:])
    else:
        path = os.getcwd()
    return os.path.abspath(path)


def get_category(filename: str) -> str:
    """Определяет категорию по расширению (регистр не важен)."""
    extension = os.path.splitext(filename)[1].lower()
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return OTHER


def free_name(directory: str, filename: str) -> str:
    """Подбирает свободное имя: name.ext -> name_1.ext -> name_2.ext ..."""
    base, extension = os.path.splitext(filename)
    candidate = filename
    counter = 0
    while os.path.exists(os.path.join(directory, candidate)):
        counter += 1
        candidate = f"{base}_{counter}{extension}"
    return candidate


def safe_move(src: str, dst_dir: str) -> tuple:
    """Перемещает файл в dst_dir, не перезаписывая существующие файлы.

    Возвращает (успех, итоговое_имя, было_переименование).
    os.rename не работает между разными дисками - такая ошибка (OSError)
    перехватывается, файл считается пропущенным.
    """
    original_name = os.path.basename(src)
    new_name = free_name(dst_dir, original_name)
    try:
        os.rename(src, os.path.join(dst_dir, new_name))
    except OSError as error:
        print(f"  ! Не удалось переместить {original_name}: {error}")
        return False, original_name, False
    return True, new_name, new_name != original_name


def list_files(directory: str) -> list:
    """Только файлы верхнего уровня (подкаталоги не трогаем), без служебных."""
    script_name = os.path.basename(__file__)
    files = []
    for name in sorted(os.listdir(directory)):
        full_path = os.path.join(directory, name)
        if not os.path.isfile(full_path):
            continue
        if name == script_name or name in SERVICE_FILES:
            continue
        files.append(name)
    return files


def categorize_files(directory: str) -> dict:
    """Создаёт папки категорий и раскладывает файлы. Возвращает статистику."""
    stats = {
        "moved": {category: 0 for category in [*CATEGORIES, OTHER]},
        "skipped": 0,
        "renamed": 0,
        "total": 0,
    }
    for category in stats["moved"]:
        os.makedirs(os.path.join(directory, category), exist_ok=True)

    for name in list_files(directory):
        stats["total"] += 1
        category = get_category(name)
        ok, _, renamed = safe_move(
            os.path.join(directory, name), os.path.join(directory, category)
        )
        if ok:
            stats["moved"][category] += 1
            stats["renamed"] += int(renamed)
        else:
            stats["skipped"] += 1
    return stats


def print_report(directory: str, stats: dict) -> None:
    print(f"Обработка директории: {directory}")
    for category, count in stats["moved"].items():
        print(f"  {category + ':':<11}{count} файл(ов)")
    moved = sum(stats["moved"].values())
    print(f"Всего обработано файлов: {stats['total']}")
    print(f"Перемещено: {moved} (из них переименовано из-за конфликта имён: {stats['renamed']})")
    print(f"Пропущено: {stats['skipped']}")


def main() -> None:
    directory = get_target_directory()
    if not os.path.exists(directory):
        print(f"Ошибка: путь не существует: {directory}")
        sys.exit(1)
    if not os.path.isdir(directory):
        print(f"Ошибка: это не директория: {directory}")
        sys.exit(1)
    if not list_files(directory):
        print(f"В директории нет файлов для обработки: {directory}")
        return  # подкаталоги не создаём, код возврата 0
    try:
        stats = categorize_files(directory)
    except OSError as error:
        print(f"Ошибка при подготовке папок категорий: {error}")
        sys.exit(1)
    print_report(directory, stats)


if __name__ == "__main__":
    main()
