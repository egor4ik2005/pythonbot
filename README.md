Чтобы запустить проект, выполните файл build.sh.
Пользоваться ботом можно через Telegram, нажимая соответствующие кнопки.
Функционал бота:
1. Сбор информации: бот собирает данные с сайта о героях Dota 2 и запускается викторина.
2. Сбор команды: после выбора героев будет отображаться базовый урон собранной команды.

![image](https://github.com/user-attachments/assets/0c76d3fa-3b3a-4204-ab76-fbeda978dd6f)
![image](https://github.com/user-attachments/assets/17dd38d6-ea1c-46e1-8936-991764558d0d)
![image](https://github.com/user-attachments/assets/c04e43be-c24b-42db-9723-5b947b19dccb)
![image](https://github.com/user-attachments/assets/b2312a1c-a813-4677-855c-946748200117)
![image](https://github.com/user-attachments/assets/cad35261-1f1f-4e33-b7bb-c7cc99a8a686)


При собирание информации используется две таблицы в БД в одной хранится имя персонажа и ссылка на его более подробную информацию во второй
берется эта ссылка и берется с нее информация для викторины

Для того чтобы использовать бота надо  прописать команду export BOT_TOKEN="ваш токен"
выдайте права bush скрипту chmod +x build.sh

