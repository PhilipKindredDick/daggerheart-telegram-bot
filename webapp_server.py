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
            line-height: 1.4;
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
            transition: opacity 0.2s;
        }
        .btn:hover {
            opacity: 0.8;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-secondary {
            background: var(--tg-theme-hint-color, #708499);
        }
        .character-sheet {
            display: none;
        }
        .character-sheet.active {
            display: block;
        }
        .dice-result {
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: var(--tg-theme-hint-color, #708499);
            border-radius: 8px;
            animation: fadeIn 0.5s;
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
            box-sizing: border-box;
        }
        .trait-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .trait-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            background: var(--tg-theme-bg-color, #ffffff);
            border-radius: 8px;
            border: 1px solid var(--tg-theme-hint-color, #e0e0e0);
        }
        .trait-controls {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .trait-btn {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: none;
            background: var(--tg-theme-button-color, #2481cc);
            color: white;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .trait-value {
            min-width: 30px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
        }
        .points-info {
            text-align: center;
            padding: 15px;
            background: var(--tg-theme-hint-color, #f0f0f0);
            border-radius: 8px;
            margin: 15px 0;
        }
        .character-preview {
            background: var(--tg-theme-bg-color, #ffffff);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        .error {
            color: #e74c3c;
            font-size: 14px;
            margin-top: 5px;
        }
        .success {
            color: #27ae60;
            font-size: 14px;
            margin-top: 5px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .loading {
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--tg-theme-hint-color, #e0e0e0);
        }
        .tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }
        .tab.active {
            border-bottom-color: var(--tg-theme-button-color, #2481cc);
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🗡️ Daggerheart</h1>
            <p>Создание персонажа и управление игрой</p>
            <div id="user-info"></div>
        </div>

        <!-- Вкладки -->
        <div class="tabs">
            <div class="tab active" onclick="showTab('character')">👤 Персонаж</div>
            <div class="tab" onclick="showTab('game')">🎮 Игра</div>
            <div class="tab" onclick="showTab('dice')">🎲 Кости</div>
        </div>

        <!-- Вкладка персонажа -->
        <div id="tab-character" class="tab-content">
            <div class="card" id="menu">
                <h2>Создание персонажа</h2>
                <button class="btn" onclick="showCharacterCreation()">Создать нового персонажа</button>
                <button class="btn btn-secondary" onclick="loadCharacter()">Загрузить персонажа</button>
            </div>

            <div class="card character-sheet" id="character-creation">
                <h2>Шаг 1: Основная информация</h2>

                <div class="input-group">
                    <label for="char-name">Имя персонажа:</label>
                    <input type="text" id="char-name" placeholder="Введите имя персонажа">
                </div>

                <div class="input-group">
                    <label for="char-class">Класс:</label>
                    <select id="char-class" onchange="updateClassInfo()">
                        <option value="">Выберите класс</option>
                        <option value="guardian">Страж (Guardian)</option>
                        <option value="ranger">Следопыт (Ranger)</option>
                        <option value="rogue">Плут (Rogue)</option>
                        <option value="seraph">Серафим (Seraph)</option>
                        <option value="sorcerer">Чародей (Sorcerer)</option>
                        <option value="warrior">Воин (Warrior)</option>
                    </select>
                    <div id="class-description"></div>
                </div>

                <div class="input-group">
                    <label for="char-ancestry">Происхождение:</label>
                    <select id="char-ancestry" onchange="updateAncestryInfo()">
                        <option value="">Выберите происхождение</option>
                        <option value="human">Человек (Human)</option>
                        <option value="elf">Эльф (Elf)</option>
                        <option value="dwarf">Дворф (Dwarf)</option>
                        <option value="orc">Орк (Orc)</option>
                    </select>
                    <div id="ancestry-description"></div>
                </div>

                <button class="btn" onclick="showTraitsStep()">Далее: Характеристики</button>
                <button class="btn btn-secondary" onclick="showMenu()">Назад</button>
            </div>

            <div class="card character-sheet" id="traits-step">
                <h2>Шаг 2: Характеристики</h2>

                <div class="points-info">
                    <strong>Доступно очков: <span id="available-points">4</span></strong><br>
                    <small>Распределите 4 очка, затем уберите 1 очко из любой характеристики</small>
                </div>

                <div class="trait-grid">
                    <div class="trait-item">
                        <span>💪 Сила</span>
                        <div class="trait-controls">
                            <button class="trait-btn" onclick="changeTrait('strength', -1)">-</button>
                            <span class="trait-value" id="strength-value">0</span>
                            <button class="trait-btn" onclick="changeTrait('strength', 1)">+</button>
                        </div>
                    </div>
                    <div class="trait-item">
                        <span>🤸 Ловкость</span>
                        <div class="trait-controls">
                            <button class="trait-btn" onclick="changeTrait('agility', -1)">-</button>
                            <span class="trait-value" id="agility-value">0</span>
                            <button class="trait-btn" onclick="changeTrait('agility', 1)">+</button>
                        </div>
                    </div>
                    <div class="trait-item">
                        <span>🎯 Точность</span>
                        <div class="trait-controls">
                            <button class="trait-btn" onclick="changeTrait('finesse', -1)">-</button>
                            <span class="trait-value" id="finesse-value">0</span>
                            <button class="trait-btn" onclick="changeTrait('finesse', 1)">+</button>
                        </div>
                    </div>
                    <div class="trait-item">
                        <span>👁️ Интуиция</span>
                        <div class="trait-controls">
                            <button class="trait-btn" onclick="changeTrait('instinct', -1)">-</button>
                            <span class="trait-value" id="instinct-value">0</span>
                            <button class="trait-btn" onclick="changeTrait('instinct', 1)">+</button>
                        </div>
                    </div>
                    <div class="trait-item">
                        <span>👑 Присутствие</span>
                        <div class="trait-controls">
                            <button class="trait-btn" onclick="changeTrait('presence', -1)">-</button>
                            <span class="trait-value" id="presence-value">0</span>
                            <button class="trait-btn" onclick="changeTrait('presence', 1)">+</button>
                        </div>
                    </div>
                    <div class="trait-item">
                        <span>📚 Знания</span>
                        <div class="trait-controls">
                            <button class="trait-btn" onclick="changeTrait('knowledge', -1)">-</button>
                            <span class="trait-value" id="knowledge-value">0</span>
                            <button class="trait-btn" onclick="changeTrait('knowledge', 1)">+</button>
                        </div>
                    </div>
                </div>

                <div id="traits-error" class="error"></div>

                <button class="btn" onclick="showPreview()" id="next-btn" disabled>Далее: Предпросмотр</button>
                <button class="btn btn-secondary" onclick="showCharacterCreation()">Назад</button>
            </div>

            <div class="card character-sheet" id="character-preview">
                <h2>Шаг 3: Предпросмотр персонажа</h2>

                <div class="character-preview" id="preview-content">
                    <!-- Содержимое будет заполнено JavaScript -->
                </div>

                <button class="btn" onclick="createCharacter()">Создать персонажа</button>
                <button class="btn btn-secondary" onclick="showTraitsStep()">Назад</button>
            </div>
        </div>

        <!-- Вкладка игры -->
        <div id="tab-game" class="tab-content character-sheet">
            <div class="card">
                <h2>Игровая сессия</h2>
                <div id="game-status">
                    <p>Информация о текущей игре будет здесь...</p>
                </div>

                <div class="input-group">
                    <label for="action-input">Ваше действие:</label>
                    <input type="text" id="action-input" placeholder="Что вы хотите сделать?">
                </div>
                <button class="btn" onclick="sendAction()">Отправить действие</button>

                <div id="game-log">
                    <!-- Лог игры -->
                </div>
            </div>
        </div>

        <!-- Вкладка костей -->
        <div id="tab-dice" class="tab-content character-sheet">
            <div class="card">
                <h2>Броски костей</h2>

                <div class="input-group">
                    <label for="trait-select">Характеристика:</label>
                    <select id="trait-select">
                        <option value="strength">💪 Сила</option>
                        <option value="agility">🤸 Ловкость</option>
                        <option value="finesse">🎯 Точность</option>
                        <option value="instinct">👁️ Интуиция</option>from flask import Flask, render_template_string, request, jsonify
import threading
import os
from config import PORT

app = Flask(__name__)

                        <option value="presence">👑 Присутствие</option>
                        <option value="knowledge">📚 Знания</option>
                    </select>
                </div>

                <div class="input-group">
                    <label for="difficulty-input">Сложность (по умолчанию 12):</label>
                    <input type="number" id="difficulty-input" value="12" min="5" max="20">
                </div>

                <div class="input-group">
                    <label>
                        <input type="checkbox" id="advantage-check"> Преимущество (+1d6)
                    </label>
                    <label>
                        <input type="checkbox" id="disadvantage-check"> Помеха (-1d6)
                    </label>
                </div>

                <button class="btn" onclick="rollDice()">🎲 Бросить кости</button>

                <div id="dice-result" class="dice-result" style="display: none;"></div>
            </div>
        </div>
    </div>

    <script>
        // Инициализация Telegram Web App
        const tg = window.Telegram.WebApp;
        tg.expand();

        // Данные персонажа
        let characterData = {
            name: '',
            class: '',
            ancestry: '',
            traits: {
                strength: 0,
                agility: 0,
                finesse: 0,
                instinct: 0,
                presence: 0,
                knowledge: 0
            }
        };

        // Доступные очки для распределения
        let availablePoints = 4;
        let pointsSpent = 0;

        // Информация о классах и происхождениях
        const classInfo = {
            guardian: "Страж защищает союзников, бросаясь в опасность. Высокая защита и хиты.",
            ranger: "Следопыт отлично стреляет и выживает в дикой природе. Быстр и точен.",
            rogue: "Плут сражается хитростью и скоростью. Скрытные атаки и ловкость.",
            seraph: "Серафим использует божественную магию для исцеления и защиты.",
            sorcerer: "Чародей обладает врожденной магией и разрушительными заклинаниями.",
            warrior: "Воин - мастер ближнего боя, наносящий мощные удары."
        };

        const ancestryInfo = {
            human: "Люди универсальны и амбициозны. Бонус к присутствию.",
            elf: "Эльфы грациозны и магически одарены. Бонусы к точности и знаниям.",
            dwarf: "Дворфы выносливы и мастеровиты. Бонусы к силе и интуиции.",
            orc: "Орки сильны и свирепы. Большой бонус к силе."
        };

        // Показать информацию о пользователе
        const userInfo = document.getElementById('user-info');
        if (tg.initDataUnsafe.user) {
            userInfo.innerHTML = `<p>👤 ${tg.initDataUnsafe.user.first_name}</p>`;
        }

        // Управление вкладками
        function showTab(tabName) {
            // Скрыть все вкладки
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.style.display = 'none';
            });

            // Убрать активный класс у всех вкладок
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Показать выбранную вкладку
            document.getElementById(`tab-${tabName}`).style.display = 'block';

            // Добавить активный класс
            event.target.classList.add('active');
        }

        function showMenu() {
            hideAllCharacterSheets();
            document.getElementById('menu').style.display = 'block';
        }

        function showCharacterCreation() {
            hideAllCharacterSheets();
            document.getElementById('character-creation').style.display = 'block';
        }

        function showTraitsStep() {
            const name = document.getElementById('char-name').value;
            const charClass = document.getElementById('char-class').value;
            const ancestry = document.getElementById('char-ancestry').value;

            if (!name.trim()) {
                alert('Введите имя персонажа!');
                return;
            }

            if (!charClass) {
                alert('Выберите класс!');
                return;
            }

            if (!ancestry) {
                alert('Выберите происхождение!');
                return;
            }

            characterData.name = name;
            characterData.class = charClass;
            characterData.ancestry = ancestry;

            hideAllCharacterSheets();
            document.getElementById('traits-step').style.display = 'block';

            // Применяем бонусы происхождения
            applyAncestryBonuses();
            updateTraitsDisplay();
        }

        function showPreview() {
            if (!validateTraits()) {
                return;
            }

            hideAllCharacterSheets();
            document.getElementById('character-preview').style.display = 'block';
            updatePreview();
        }

        function hideAllCharacterSheets() {
            document.querySelectorAll('.character-sheet').forEach(sheet => {
                sheet.style.display = 'none';
            });
        }

        function updateClassInfo() {
            const classSelect = document.getElementById('char-class');
            const description = document.getElementById('class-description');
            const selectedClass = classSelect.value;

            if (selectedClass && classInfo[selectedClass]) {
                description.innerHTML = `<small class="success">${classInfo[selectedClass]}</small>`;
            } else {
                description.innerHTML = '';
            }
        }

        function updateAncestryInfo() {
            const ancestrySelect = document.getElementById('char-ancestry');
            const description = document.getElementById('ancestry-description');
            const selectedAncestry = ancestrySelect.value;

            if (selectedAncestry && ancestryInfo[selectedAncestry]) {
                description.innerHTML = `<small class="success">${ancestryInfo[selectedAncestry]}</small>`;
            } else {
                description.innerHTML = '';
            }
        }

        function applyAncestryBonuses() {
            // Сбрасываем бонусы
            resetTraits();

            const ancestry = characterData.ancestry;

            // Применяем бонусы происхождения
            switch (ancestry) {
                case 'human':
                    characterData.traits.presence += 1;
                    break;
                case 'elf':
                    characterData.traits.finesse += 1;
                    characterData.traits.knowledge += 1;
                    break;
                case 'dwarf':
                    characterData.traits.strength += 1;
                    characterData.traits.instinct += 1;
                    break;
                case 'orc':
                    characterData.traits.strength += 2;
                    break;
            }
        }

        function resetTraits() {
            for (let trait in characterData.traits) {
                characterData.traits[trait] = 0;
            }
            availablePoints = 4;
            pointsSpent = 0;
        }

        function changeTrait(traitName, change) {
            const currentValue = characterData.traits[traitName];
            const newValue = currentValue + change;

            // Проверки ограничений
            if (newValue < -3 || newValue > 3) {
                return;
            }

            // Проверка доступных очков
            if (change > 0 && availablePoints <= 0) {
                return;
            }

            if (change < 0 && currentValue <= getAncestryBonus(traitName)) {
                return; // Не можем убрать ниже бонуса происхождения
            }

            characterData.traits[traitName] = newValue;
            availablePoints -= change;
            pointsSpent += change;

            updateTraitsDisplay();
            checkTraitsValidity();
        }

        function getAncestryBonus(traitName) {
            const ancestry = characterData.ancestry;

            switch (ancestry) {
                case 'human':
                    return traitName === 'presence' ? 1 : 0;
                case 'elf':
                    return (traitName === 'finesse' || traitName === 'knowledge') ? 1 : 0;
                case 'dwarf':
                    return (traitName === 'strength' || traitName === 'instinct') ? 1 : 0;
                case 'orc':
                    return traitName === 'strength' ? 2 : 0;
                default:
                    return 0;
            }
        }

        function updateTraitsDisplay() {
            for (let trait in characterData.traits) {
                const valueElement = document.getElementById(`${trait}-value`);
                if (valueElement) {
                    const value = characterData.traits[trait];
                    valueElement.textContent = value >= 0 ? `+${value}` : value;

                    // Подсветка бонусов происхождения
                    const bonus = getAncestryBonus(trait);
                    if (bonus > 0) {
                        valueElement.style.color = '#27ae60';
                    } else {
                        valueElement.style.color = '';
                    }
                }
            }

            document.getElementById('available-points').textContent = availablePoints;
        }

        function checkTraitsValidity() {
            const total = Object.values(characterData.traits).reduce((sum, val) => sum + val, 0);
            const errorElement = document.getElementById('traits-error');
            const nextBtn = document.getElementById('next-btn');

            errorElement.textContent = '';

            if (availablePoints > 0) {
                errorElement.textContent = `Осталось распределить ${availablePoints} очков`;
                nextBtn.disabled = true;
            } else if (total !== 3) {
                errorElement.textContent = `Сумма характеристик должна быть 3 (сейчас ${total}). Уберите 1 очко из любой характеристики.`;
                nextBtn.disabled = true;
            } else {
                nextBtn.disabled = false;
            }
        }

        function validateTraits() {
            const total = Object.values(characterData.traits).reduce((sum, val) => sum + val, 0);
            return total === 3 && availablePoints === 0;
        }

        function updatePreview() {
            const preview = document.getElementById('preview-content');

            preview.innerHTML = `
                <h3>👤 ${characterData.name}</h3>
                <p><strong>Класс:</strong> ${classInfo[characterData.class] ? characterData.class.charAt(0).toUpperCase() + characterData.class.slice(1) : 'Не выбран'}</p>
                <p><strong>Происхождение:</strong> ${characterData.ancestry.charAt(0).toUpperCase() + characterData.ancestry.slice(1)}</p>

                <h4>Характеристики:</h4>
                <div class="trait-grid">
                    ${Object.entries(characterData.traits).map(([trait, value]) => {
                        const traitNames = {
                            strength: '💪 Сила',
                            agility: '🤸 Ловкость', 
                            finesse: '🎯 Точность',
                            instinct: '👁️ Интуиция',
                            presence: '👑 Присутствие',
                            knowledge: '📚 Знания'
                        };
                        return `
                            <div class="trait-item">
                                <span>${traitNames[trait]}</span>
                                <span class="trait-value">${value >= 0 ? '+' + value : value}</span>
                            </div>
                        `;
                    }).join('')}
                </div>

                <p><small>Сумма характеристик: ${Object.values(characterData.traits).reduce((sum, val) => sum + val, 0)}</small></p>
            `;
        }

        function createCharacter() {
            if (!validateTraits()) {
                alert('Ошибка в характеристиках персонажа!');
                return;
            }

            // Отправляем данные боту
            const characterPayload = {
                action: 'character_created',
                character: {
                    name: characterData.name,
                    class: characterData.class,
                    ancestry: characterData.ancestry,
                    ...characterData.traits
                }
            };

            tg.sendData(JSON.stringify(characterPayload));

            // Сохраняем локально
            localStorage.setItem('daggerheart_character', JSON.stringify(characterData));

            alert(`Персонаж ${characterData.name} создан! Возвращайся в чат для начала игры.`);
        }

        function loadCharacter() {
            const saved = localStorage.getItem('daggerheart_character');
            if (saved) {
                characterData = JSON.parse(saved);

                // Заполняем поля
                document.getElementById('char-name').value = characterData.name;
                document.getElementById('char-class').value = characterData.class;
                document.getElementById('char-ancestry').value = characterData.ancestry;

                showTraitsStep();
                updateTraitsDisplay();

                alert('Персонаж загружен!');
            } else {
                alert('Сохраненный персонаж не найден!');
            }
        }

        function rollDice() {
            const trait = document.getElementById('trait-select').value;
            const difficulty = parseInt(document.getElementById('difficulty-input').value) || 12;
            const advantage = document.getElementById('advantage-check').checked;
            const disadvantage = document.getElementById('disadvantage-check').checked;

            // Симуляция броска Hope/Fear (2d12)
            const hopeDie = Math.floor(Math.random() * 12) + 1;
            const fearDie = Math.floor(Math.random() * 12) + 1;

            let bonus = 0;
            if (advantage && !disadvantage) {
                bonus = Math.floor(Math.random() * 6) + 1;
            } else if (disadvantage && !advantage) {
                bonus = -(Math.floor(Math.random() * 6) + 1);
            }

            const total = hopeDie + fearDie + bonus;

            // Определяем результат
            let resultType = '';
            let resultEmoji = '';

            if (hopeDie === fearDie) {
                resultType = 'Критический успех!';
                resultEmoji = '🎯';
            } else if (hopeDie > fearDie) {
                resultType = 'Успех с Hope!';
                resultEmoji = '✨';
            } else {
                resultType = 'Успех с Fear!';
                resultEmoji = '⚡';
            }

            const success = total >= difficulty;

            const resultElement = document.getElementById('dice-result');
            resultElement.innerHTML = `
                ${resultEmoji} <strong>${success ? resultType : 'Неудача'}</strong><br>
                🎲 Hope: ${hopeDie} | Fear: ${fearDie}<br>
                ${bonus !== 0 ? `🎯 Модификатор: ${bonus >= 0 ? '+' + bonus : bonus}<br>` : ''}
                📊 Итого: ${total} (нужно ${difficulty})
            `;
            resultElement.style.display = 'block';

            setTimeout(() => {
                resultElement.style.display = 'none';
            }, 5000);
        }

        function sendAction() {
            const action = document.getElementById('action-input').value;
            if (!action.trim()) {
                alert('Введите действие!');
                return;
            }

            // Отправляем действие боту
            tg.sendData(JSON.stringify({
                action: 'game_action',
                text: action
            }));

            // Очищаем поле
            document.getElementById('action-input').value = '';

            // Добавляем в лог
            const gameLog = document.getElementById('game-log');
            gameLog.innerHTML += `<p><strong>Вы:</strong> ${action}</p>`;
            gameLog.scrollTop = gameLog.scrollHeight;
        }

        // Предотвращаем одновременное выбор преимущества и помехи
        document.getElementById('advantage-check').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('disadvantage-check').checked = false;
            }
        });

        document.getElementById('disadvantage-check').addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('advantage-check').checked = false;
            }
        });

        // Обработка данных от бота
        tg.onEvent('mainButtonClicked', function() {
            tg.close();
        });

        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            // Показываем первую вкладку
            showTab('character');

            // Пытаемся загрузить сохраненного персонажа
            const saved = localStorage.getItem('daggerheart_character');
            if (saved) {
                const menu = document.getElementById('menu');
                menu.innerHTML += '<p class="success">Найден сохраненный персонаж!</p>';
            }
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