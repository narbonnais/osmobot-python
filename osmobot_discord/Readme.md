---
Title: Osmobot price tracker  
Author: Alexis Fabre
Subtitle: How to program a bot that synchronise with Osmobot's balance   
Date: 2022-03-20  
Tags: discord, bot, osmosis
---

# Osmobit price tracker for discord

## How to run

Install python packages:

```sh
pip3 install -t discordbot_osmobot/requirements.txt
```

Run the bot as a module (will start `__main__.py`):

```sh
python3 -m discordbot_osmobot
```

## Development tutorial

### Discord developer's pannel

Discord developers portal: https://discord.com/developers/applications

Create application and give a name (`osmobot`): [General Information](https://discord.com/developers/applications/955047845793239110/information).

Go to the [Bot section](https://discord.com/developers/applications/955047845793239110/bot) and press `Add Bot`.

We created a new bot called `osmobot#8945`.

Now we have to invite the bot to our discord server. For that we need to activate `oauth` url authorization: go to [OAuth2 URL generator](https://discord.com/developers/applications/955047845793239110/oauth2/url-generator) and select the scope `bot`. I also add the possibility to send messages, embed links and mention everyone.

The generated URL is then: <https://discord.com/api/oauth2/authorize?client_id=955047845793239110&permissions=2048&scope=bot>. We just put that URL in the browser and discord will prompt us what server to put the bot in.

On the bot pannel, generate a token token and store in into [.env](.env) file.

### Python development

The bot will inherit from `discord.Client` and implement the following methods:

- on_ready: will start the background task
- on_message: react to a message on the discord

We add a background task to query our ATOM balance and change nickname of the bot accordingly.