# Telegram channel mirror via Telegram Client API (telethon)

### Functionality
- No need to be added by the channel's admin
- Listen to update events (new message, message edited, etc)
- Live forwarding and updating messages
- Flexible mapping of source and target channels (one-to-one, many-to-one, many-to-many)

## Prepare
0. It's better ***not to use your main account***. Register a new Telegram account

1. [Create Telegram App](https://my.telegram.org/apps)

2. Obtain **API_ID** and **API_HASH**

    ![Telegram API Credentials](/README.md-images/telegramapp.png)

3. Setup Postgres database or use InMemoryDatabase with `USE_MEMORY_DB=true` parameter in `.env` file

4. Fill [.env-example](.env-example) with your data and rename it to `.env`

    **SESSION_STRING** can be obtained by running [login.py](login.py) locally (on your PC with installed python 3.9+) with putted **API_ID** and **API_HASH** before.

    Channels ID can be fetched by using [@messageinformationsbot](https://t.me/messageinformationsbot) Telegram bot (just send it a message from the desired channel).
    
    <details>
        <summary><b>.env overview</b></summary>

    ```bash
    # Telegram app ID
    API_ID=test
    # Telegram app hash
    API_HASH=test
    # Telegram session string (telethon session, see login.py in root directory)
    SESSION_STRING=test
    # Mapping between source and target channels
    # Channel id can be fetched by using @messageinformationsbot telegram bot
    # and it always starts with -100 prefix
    # [id1, id2, id3:id4] means send messages from id1, id2, id3 to id4
    # id5:id6 means send messages from id5 to id6
    # [id1, id2, id3:id4];[id5:id6] semicolon means AND
    CHAT_MAPPING=[-100999999,-100999999,-100999999:-1009999999];
    # Enable/disable removing URLs on messages
    REMOVE_URLS=false
    # List of URLs to be removed
    REMOVE_URLS_LIST=google.com,twitter.com
    # Remove URLs whitelist, will be ignored if REMOVE_URLS_LIST is not empty
    REMOVE_URLS_WL=youtube.com,youtu.be,vk.com,twitch.tv,instagram.com
    # Disable mirror message deleting
    DISABLE_DELETE=true
    # Disable mirror message editing
    DISABLE_EDIT=true
    # Postgres credentials
    DATABASE_URL=postgres://user:pass@host/dbname
    # or
    DB_NAME=test
    DB_USER=test
    DB_HOST=test
    DB_PASS=test
    # Using in-memory database like dictionary instead of Postgres DB (true or false).
    # Default is false
    USE_MEMORY_DB=false
    # Logger level
    LOG_LEVEL=INFO
    ```
</details> 

5. Make sure the account has joined source and target channels

### Be careful with forwards from channels with [`restricted saving content`](https://telegram.org/blog/protected-content-delete-by-date-and-more). It may lead to an account ban. 

Help is also welcome to work around this limitation. See [sources](/telemirror/messagefilters.py#L84).

## Deploy

### Host on Heroku:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/khoben/telemirror)

or manually:

1. Clone project

    ```bash
    git clone https://github.com/khoben/telemirror.git
    ```
2. Create new heroku app within Heroku CLI

    ```bash
    heroku create {your app name}
    ```
3. Add heroku remote

    ```bash
    heroku git:remote -a {your app name}
    ```
4. Set environment variables to your heroku app from .env by running bash script

    ```bash
    ./set_heroku_env.bash
    ```

5. Upload on heroku host

    ```bash
    git push heroku master
    ```

6. Start heroku app

    ```bash
    heroku ps:scale run=1
    ```

### Locally:
1. Create and activate python virtual environment

    ```bash
    python -m venv myvenv
    source myvenv/Scripts/activate # linux
    myvenv/Scripts/activate # windows
    ```
2. Install dependencies

    ```bash
    pip install -r requirements.txt
    ```
3. Run

    ```bash
    python main.py
    ```

## Keep up-to-date

If you deployed manually, move to step 2.

0. Get project to your PC:

    ```bash
    heroku git:clone -a {your app name}
    ```
1. Init upstream repo

    ```bash
    git remote add origin https://github.com/khoben/telemirror
    ```
2. Get latest changes

    ```bash
    git pull origin master
    ```
3. Push latest changes to heroku

    ```bash
    git push heroku master -f
    ```
