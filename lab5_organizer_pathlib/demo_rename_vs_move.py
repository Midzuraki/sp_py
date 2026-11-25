import os
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent
    default_b = project_root / "temp_d"

    dir_a = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir())
    dir_b = Path(sys.argv[2] if len(sys.argv) > 2 else default_b)

    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)

    if os.stat(dir_a).st_dev == os.stat(dir_b).st_dev:
        print("Внимание: обе папки на одной файловой системе - ошибка не воспроизведётся.")

    print(f"Источник : {dir_a}\nНазначение: {dir_b}\n")

    for method in ("Path.rename", "shutil.move"):
        src = dir_a / f"demo_{method.split('.')[0]}.txt"
        dst = dir_b / src.name

        if not src.exists():
            print(f"{method:<12}: Исходный файл {src.name} не найден в {dir_a}")
            continue

        if dst.exists():
            print(f"{method:<12}: Пропущено, {dst.name} уже существует в {dir_b}")
            continue

        try:
            if method == "Path.rename":
                src.rename(dst)
            else:
                shutil.move(str(src), str(dst))
            print(f"{method:<12}: OK, файл перенесён в {dst}")
        except OSError as error:
            print(f"{method:<12}: OSError -> {error}")


if __name__ == "__main__":
    main()
