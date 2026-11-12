"""ЛР5: Path.rename() vs shutil.move() при перемещении между разными файловыми системами.

Запуск:  python demo_rename_vs_move.py [папка_на_диске_A] [папка_на_диске_B]
Без аргументов: системная temp-папка и /dev/shm (tmpfs, отдельная ФС в Linux).
В Windows передайте две папки на разных дисках, например:  C:\\tmp  D:\\tmp
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> None:
    dir_a = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.gettempdir())
    default_b = "/dev/shm" if Path("/dev/shm").exists() else tempfile.gettempdir()
    dir_b = Path(sys.argv[2] if len(sys.argv) > 2 else default_b)
    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)
    if os.stat(dir_a).st_dev == os.stat(dir_b).st_dev:
        print("Внимание: обе папки на одной файловой системе - ошибка не воспроизведётся.")

    print(f"Источник : {dir_a}\nНазначение: {dir_b}\n")
    for method in ("Path.rename", "shutil.move"):
        src = dir_a / f"demo_{method.split('.')[0]}.txt"
        src.write_text("демо", encoding="utf-8")
        dst = dir_b / src.name
        try:
            if method == "Path.rename":
                src.rename(dst)
            else:
                shutil.move(str(src), str(dst))
            print(f"{method:<12}: OK, файл теперь в {dst}")
        except OSError as error:
            print(f"{method:<12}: OSError -> {error}")
        finally:
            for p in (src, dst):
                p.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
