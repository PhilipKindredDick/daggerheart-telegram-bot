from flask import Flask, render_template_string, request, jsonify
import threading
import os
from config import PORT

app = Flask(__name__)

# HTML для Mini App
WEBAPP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daggerheart Game</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
        }
        .card {
            background: var(--tg-theme-secondary-bg-color, #f8f9fa);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .btn {
            background: var(--tg-theme-button-color, #2481cc);
            color: var(--tg-theme-button-text-color, #ffffff);
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            margin-top: 10px;
        }
        .btn:hover {
            opacity: 0.8;
        }
        .character-sheet {
            display: none;
        }
        .dice-result {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: var(--tg-theme-hint-color, #708499);
            border-radius: 8px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .input-group input, .input-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--tg-theme-hint-color, #708499);
            border-radius: 6px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🗡️ Daggerheart</h1>
            <p>Добро пожаловать в мир приключений!</p>
            <div id="user-info"></div>
        </div>

        <div class="card" id="menu">
            <h2>Главное меню</h2>
            <button class="btn" onclick="showCharacterCreation()">Создать персонажа</button>
            <button class="btn" onclick="rollDice()">Бросить кости</button>
            <button class="btn" onclick="showGameSession()">Игровая сессия</button>
        </div>

        <div class="card character-sheet" id="character-creation">
            <h2>Создание персонажа</h2>
            <div class="input-group">
                <label for="char-name">Имя персонажа:</label>
                <input type="text" id="char-name" placeholder="Введите имя">
            </div>
            <div class="input-group">
                <label for="char-class">Класс:</label>
                <select id="char-class">
                    <option value="guardian">Страж</option>
                    <option value="seraph">Серафим</option>
                    <option value="warrior">Воин</option>
                    <option value="ranger">Следопыт</option>
                    <option value="rogue">Плут</option>
                    <option value="sorcerer">Чародей</option>
                </select>
            </div>
            <div class="input-group">
                <label for="char-ancestry">Происхождение:</label>
                <select id="char-ancestry">
                    <option value="human">Человек</option>
                    <option value="elf">Эльф</option>
                    <option value="dwarf">Дворф</option>
                    <option value="orc">Орк</option>
                </select>
            </div>
            <button class="btn" onclick="createCharacter()">Создать персонажа</button>
            <button class="btn" onclick="showMenu()">Назад</button>
        </div>

        <div class="card character-sheet" id="game-session">
            <h2>Игровая сессия</h2>
            <div id="game-log">
                <p>🎲 Ожидание начала игры...</p>
            </div>
            <div class="input-group">
                <label for="action-input">Ваше действие:</label>
                <input type="text" id="action-input" placeholder="Что вы хотите сделать?">
            </div>
            <button class="btn" onclick="sendAction()">Отправить действие</button>
            <button class="btn" onclick="showMenu()">Назад в меню</button>
        </div>

        <div id="dice-result" class="dice-result" style="display: none;"></div>
    </div>

    <script>
        // Инициализация Telegram Web App
        const tg = window.Telegram.WebApp;
        tg.expand();

        // Показать информацию о пользователе
        const userInfo = document.getElementById('user-info');
        if (tg.initDataUnsafe.user) {
            userInfo.innerHTML = `<p>Игрок: ${tg.initDataUnsafe.user.first_name}</p>`;
        }

        function showMenu() {
            document.getElementById('menu').style.display = 'block';
            document.getElementById('character-creation').style.display = 'none';
            document.getElementById('game-session').style.display = 'none';
        }

        function showCharacterCreation() {
            document.getElementById('menu').style.display = 'none';
            document.getElementById('character-creation').style.display = 'block';
            document.getElementById('game-session').style.display = 'none';
        }

        function showGameSession() {
            document.getElementById('menu').style.display = 'none';
            document.getElementById('character-creation').style.display = 'none';
            document.getElementById('game-session').style.display = 'block';
        }

        function createCharacter() {
            const name = document.getElementById('char-name').value;
            const charClass = document.getElementById('char-class').value;
            const ancestry = document.getElementById('char-ancestry').value;

            if (!name.trim()) {
                alert('Введите имя персонажа!');
                return;
            }

            const character = {
                name: name,
                class: charClass,
                ancestry: ancestry
            };

            // Сохранить персонажа (пока что в localStorage)
            localStorage.setItem('character', JSON.stringify(character));

            alert(`Персонаж создан!\\n\\nИмя: ${name}\\nКласс: ${charClass}\\nПроисхождение: ${ancestry}`);

            // Уведомить бота о создании персонажа
            tg.sendData(JSON.stringify({
                action: 'character_created',
                character: character
            }));

            showMenu();
        }

        function rollDice() {
            // Симуляция броска d12
            const result = Math.floor(Math.random() * 12) + 1;
            const diceResult = document.getElementById('dice-result');
            diceResult.innerHTML = `🎲 Результат: ${result}`;
            diceResult.style.display = 'block';

            setTimeout(() => {
                diceResult.style.display = 'none';
            }, 3000);
        }

        function sendAction() {
            const action = document.getElementById('action-input').value;
            if (!action.trim()) {
                alert('Введите действие!');
                return;
            }

            // Добавить действие в лог
            const gameLog = document.getElementById('game-log');
            gameLog.innerHTML += `<p><strong>Вы:</strong> ${action}</p>`;

            // Отправить действие боту
            tg.sendData(JSON.stringify({
                action: 'game_action',
                text: action
            }));

            // Очистить поле ввода
            document.getElementById('action-input').value = '';

            // Имитация ответа ГМ (пока что заглушка)
            setTimeout(() => {
                gameLog.innerHTML += `<p><strong>ГМ:</strong> Интересное решение! (Пока что это заглушка)</p>`;
                gameLog.scrollTop = gameLog.scrollHeight;
            }, 1000);
        }

        // Обработка данных от бота
        tg.onEvent('mainButtonClicked', function() {
            tg.close();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Главная страница Mini App"""
    return render_template_string(WEBAPP_HTML)


@app.route('/api/character', methods=['POST'])
def create_character():
    """API для создания персонажа"""
    data = request.json
    # Пока что просто возвращаем данные
    return jsonify({"status": "success", "character": data})


@app.route('/api/action', methods=['POST'])
def game_action():
    """API для игровых действий"""
    data = request.json
    # Здесь будет интеграция с DeepSeek
    return jsonify({"status": "success", "gm_response": "Пока что заглушка ГМ"})


def run_webapp():
    """Запуск веб-приложения"""
    app.run(host='0.0.0.0', port=PORT, debug=False)


if __name__ == "__main__":
    run_webapp()