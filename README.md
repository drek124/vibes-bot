# DREKBOT: [VIBES Streaming](https://vibes.stream/) Bot

A chat bot for VIBES streams, built out of extensions you can keep or throw away.

## Setup
1. Install **Python 3.12+** and a **MySQL / MariaDB** database
2. `pip install -r requirements.txt`
3. Create a `.env` file with the variables listed in [`env.txt`](env.txt)
4. Run `python main.py`

On first run, `config-sample.json` becomes your `config.json`. When you update the bot, any new options are added to your config automatically. Database tables are created and updated by themselves too.

## Extensions
| Extension | What it does | Commands |
|---|---|---|
| `economy` | Cash & bank balances across the platform, plus a flag guessing game | `/work` `/crime` `/guesser` `/flag` `/bal` `/dep` `/with` |
| `leveling` | XP for chatting, levels & a global leaderboard | `/rank` `/top` |
| `community` | Lets streamers link their Discord server, and mods count how often words are said in chat | `/discord` `!discord` `/track` `/untrack` |
| `discord_notifier` | Posts to a Discord channel when a stream goes live | |
| `chatinteraction` | Lets commands wait for a user's next chat message as their answer | |

Don't want one? Delete its folder from `extensions/`. Each extension's settings live under its own section in `config.json`. `/flag` needs `chatinteraction` to read guesses, so keep it if you use `economy`.

Official VIBES Discord: https://discord.gg/auygjA53tM
