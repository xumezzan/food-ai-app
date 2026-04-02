#!/bin/bash
# Скрипт для настройки iOS после flutter create

INFO_PLIST="ios/Runner/Info.plist"

if [ ! -f "$INFO_PLIST" ]; then
    echo "❌ Ошибка: Файл $INFO_PLIST не найден. Сначала запустите 'flutter create --platforms=ios .'"
    exit 1
fi

echo "📸 Добавляю разрешения на камеру и библиотеку в $INFO_PLIST..."

# С помощью простого python скрипта добавляем ключи в plist, чтобы не возиться с sed
python3 -c "
import plistlib
import sys

path = '$INFO_PLIST'
try:
    with open(path, 'rb') as f:
        pl = plistlib.load(f)
    
    pl['NSCameraUsageDescription'] = 'Приложению нужен доступ к камере для сканирования еды и штрихкодов.'
    pl['NSPhotoLibraryUsageDescription'] = 'Приложению нужен доступ к галерее для выбора фотографий еды.'
    
    with open(path, 'wb') as f:
        plistlib.dump(pl, f)
    print('✅ Разрешения успешно добавлены!')
except Exception as e:
    print(f'❌ Ошибка при обновлении plist: {e}')
    sys.exit(1)
"
