#!/usr/bin/env python3
"""
Скрипт для автоматической настройки проекта Daggerheart Bot
"""

import os
import shutil
import subprocess
import sys


def create_directories():
    """Создание необходимых директорий"""
    directories = [
        'game',
        'deepseek',
        'logs',
        'temp'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

        # Создание __init__.py для Python пакетов
        if directory in ['game', 'deepseek']:
            init_file = os.path.join(directory, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write('# Daggerheart Bot module\n')


def create_env_file():
    """Создание .env файла если его нет"""
    if not os.path.exists('.env'):
        print("📝 Создаю .env файл...")
        shutil.copy('.env.example', '.env')
        print("✅ .env файл создан! Не забудь заполнить токены.")
    else:
        print("✅ .env файл уже существует")


def install_dependencies():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                       check=True)
        print("✅ Зависимости установлены успешно!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False
    return True


def check_tokens():
    """Проверка наличия токенов"""
    print("🔍 Проверка токенов...")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        bot_token = os.getenv('BOT_TOKEN')
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        webapp_url = os.getenv('WEBAPP_URL')

        issues = []

        if not bot_token or bot_token == 'your_bot_token_here':
            issues.append("❌ BOT_TOKEN не настроен")
        else:
            print("✅ BOT_TOKEN найден")

        if not deepseek_key or deepseek_key == 'your_deepseek_api_key_here':
            issues.append("❌ DEEPSEEK_API_KEY не настроен")
        else:
            print("✅ DEEPSEEK_API_KEY найден")

        if not webapp_url or 'your-replit' in webapp_url:
            issues.append("❌ WEBAPP_URL не настроен")
        else:
            print("✅ WEBAPP_URL найден")

        if issues:
            print("\n⚠️  Найдены проблемы с конфигурацией:")
            for issue in issues:
                print(f"   {issue}")
            print("\n📝 Отредактируй файл .env и заполни необходимые токены")
            return False
        else:
            print("✅ Все токены настроены!")
            return True

    except ImportError:
        print("❌ Не удалось загрузить dotenv. Установи зависимости сначала.")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке токенов: {e}")
        return False


def main():
    """Основная функция настройки"""
    print("🚀 Настройка Daggerheart Bot...")
    print("=" * 50)

    # Создание директорий
    print("📁 Создание директорий...")
    create_directories()
    print("✅ Директории созданы!")

    # Создание .env файла
    create_env_file()

    # Установка зависимостей
    if not install_dependencies():
        print("❌ Не удалось установить зависимости. Завершение.")
        sys.exit(1)

    # Проверка токенов
    tokens_ok = check_tokens()

    print("\n" + "=" * 50)
    print("🎉 Настройка завершена!")

    if tokens_ok:
        print("\n✅ Все готово для запуска!")
        print("🚀 Запускай бота командой: python run_bot.py")
    else:
        print("\n⚠️  Нужно настроить токены в .env файле")
        print("📝 Инструкции:")
        print("   1. Получи BOT_TOKEN у @BotFather в Telegram")
        print("   2. Получи DEEPSEEK_API_KEY на https://platform.deepseek.com/")
        print("   3. Обнови WEBAPP_URL с URL твоего Replit проекта")
        print("   4. Запусти: python run_bot.py")

    print("\n📚 Документация: README.md")
    print("🐛 Баги и предложения: GitHub Issues")


if __name__ == "__main__":
    main()