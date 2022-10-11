<h4>Настройка телеграм бота</h4>
Вы должны иметь телеграм бота, а именно "HTTP API" это ваш TOKEN и chat_id, если его у Вас нет, порядок создания:<br>
Открываете телеграм<br>
В поиске ищете @botFather<br>
присоединяетесь<br>
Вводите /newbot <br>
Придумываете имя бота на латинском и должен заканчиваться на _bot <br>
Например, haqq_marina_bot <br>
botFather даст Вам HTTP API  вида <br>
5611744630:AAFF9pC9674111D_oDTSteJQfS8m7_O0bcQ <br>
и еще вам нужен chat_id <br>
его можно получить водив на браузере <a href="#">https://api.telegram.org/bot<HTTP API>/getUpdates</a> <br>
ответбудет примерно таким:<br>

{"ok":true,"result":[{"update_id":461136221,
"message":{"message_id":5,"from":{"id":1410371666,"is_bot":false,"first_name":"\u0410\u043d","last_name":"\u043c\u0438\u0441\u0441","username":"nadyatarabukina","language_code":"ru"},"chat":{"id":1410371666,"first_name":"\u0410\u043d","last_name":"\u043c\u0438\u0441\u0441","username":"nadyatarabukina","type":"private"},"date":1665454393,"text":"/start","entities":[{"offset":0,"length":6,"type":"bot_command"}]}},{"update_id":461136222,<br>

находим '"from":{"id":1410371666,', ваш id_chat: 1410371666<br>

  <h4>Открытие rpc ноды</h4>

nano ~/.haqqd/config/config.toml<br>
в разделе [rpc] (примерно 109 строка)<br>
поменять laddr = "tcp://127.0.0.1:26657" на laddr = "tcp://0.0.0.0:26657"<br>
И перезагружаем ноду<br>
sudo systemctl restart haqq<br>
  
  <h4>Установка PANIC BOT</h4>

Проверяем, есть ли на сервере python<br>
python3 --version<br>
с дистрибутива ubuntu 20.04 python идет в коробке с ОС<br><br>

Устанавливаем PIP и Redis Database Server<br>
sudo apt-get install python3-pip redis-server -y<br><br>

Устанавливаем Pipenv и включаем Redis<br>
sudo pip3 install pipenv<br>
sudo systemctl enable redis-server.service<br><br>

<code>
cd
git clone https://github.com/tarabukinvanya739/tarpanic
cd tarpanic
git checkout master
</code>
<br><br>
обновляем pip и запускаем установку<br>

сразу настроим конфиги вручную:<br>
nano config/user_config_main.ini<br>
Исправляем строчки<br>
строка1 - любое имя вместо Name:<br>
unique_alerter_identifier = Name <br>
строка6 - ставим TOKEN с телеграм бота:<br>
bot_token = [TOKEN] <br>
строка7 - ставим id_chat с телеграм бота<br>
bot_chat_id = [id_chat]<br>
строка32 - ставим TOKEN с телеграм бота:<br>
bot_token = [TOKEN]<br>
строка33 - ставим id_chat с телеграм бота<br>
bot_chat_id = [id_chat]<br><br>

сохраняемся и закрываем, CTRL+X,Y<br>
<br>
nano config/user_config_nodes.ini<br>
в строке 2 вводим свой moniker<br>
в строке 3 вводим rpc своей ноды, например<br>
node_rpc_url = http://<ip>:26657<br>
<br><br>
pipenv update<br>
pipenv run python run_setup.py<br><br>

отвечаем 5 раз n, потом когда спрасит "Telegram commands are already set up. Do you wish to clear the current config? (Y/n)" отвечаем Y
потом n, n, n, n
<br><br>
проверяем запуск:<br>
/usr/local/bin/pipenv run python /$USER/tarpanic/run_alerter.py<br>

должно выйти Node monitor (Moniker) started.<br><br>

создаем сервисный файл для запуска в фоновом режиме:<br>
  
<code>
  
    printf "[Unit]
    Description=BOT
    After=network.target
    StartLimitIntervalSec=0

    [Service]
    Type=simple
    Restart=always
    User=$USER
    TimeoutStopSec=90s
    WorkingDirectory=/$USER/tarpanic
    ExecStart=/usr/local/bin/pipenv run python /$USER/tarpanic/run_alerter.py
  
    [Install]
    WantedBy=multi-user.target" > /etc/systemd/system/panic.service 
  
 </code>
  <br>
Запускаем и смотрим логи:<br>
  
  sudo systemctl daemon-reload<br>
  sudo systemctl enable panic<br>
  sudo systemctl start panic<br>
  sudo journalctl -u panic -f<br>
  

  <br>
Здесь тоже должно выйти "Node monitor (Moniker) started"
