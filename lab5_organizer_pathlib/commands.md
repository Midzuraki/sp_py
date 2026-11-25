## 1. Проверка справки и тестовый прогон
```bash
python lab5_organizer_pathlib/organizer_pathlib.py --help
```

```bash
python lab5_organizer_pathlib/organizer_pathlib.py test_files --dry-run
```

## 2. Уборка и проверка конфликтов
```bash
python lab5_organizer_pathlib/organizer_pathlib.py test_files
```

```bash
python -c "from pathlib import Path; (Path('test_files') / 'doc.txt').write_text('new')" && python lab5_organizer_pathlib/organizer_pathlib.py test_files --verbose
```

## 3. Демонстрация rename vs move и очистка
```bash
python lab5_organizer_pathlib/demo_rename_vs_move.py C:\temp D:\temp
```

```bash
python -c "import shutil; shutil.rmtree('test_files', ignore_errors=True)"
```
