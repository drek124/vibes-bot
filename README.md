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
| `economy` | Cash & bank balances across the platform | `/work` `/crime` `/guesser` `/bal` `/dep` `/with` |
| `leveling` | XP for chatting, levels & a global leaderboard | `/rank` `/top` |
| `community` | Lets streamers link their Discord server | `/discord` `!discord` |
| `discord_notifier` | Posts to a Discord channel when a stream goes live | |

Don't want one? Delete its folder from `extensions/`. Each extension's settings live under its own section in `config.json`.

Official VIBES Discord: https://discord.gg/auygjA53tM
