import sys
from threading import Thread

from modules.config import config, load_config_from_directory
from modules.console import console
from modules.context import context
from modules.memory import get_game_state, GameState
from modules.pokemon import opponent_changed, get_opponent
from modules.profiles import Profile
from modules.stats import init_stats, encounter_pokemon
from modules.temp import temp_run_from_battle


def main_loop(profile: Profile) -> None:
    """
    This function is run after the user has selected a profile and the emulator has been started.
    :param profile: The profile selected by the user
    """
    mode = None
    load_config_from_directory(profile.path, allow_missing_files=True)
    init_stats(profile)

    try:
        if config["discord"]["rich_presence"]:
            from modules.discord import discord_rich_presence

            Thread(target=discord_rich_presence).start()

        if config["obs"]["http_server"]["enable"]:
            from modules.http import http_server

            Thread(target=http_server).start()
    except:
        console.print_exception(show_locals=True)

    while True:
        try:
            if not mode and get_game_state() == GameState.BATTLE and context.bot_mode != "starters":
                if opponent_changed():
                    encounter_pokemon(get_opponent())
                if context.bot_mode != "manual":
                    temp_run_from_battle()

            if context.bot_mode == "manual":
                if mode:
                    mode = None

            elif not mode:
                match context.bot_mode:
                    case "spin":
                        from modules.modes.general import ModeSpin

                        mode = ModeSpin()

                    case "starters":
                        from modules.modes.starters import ModeStarters

                        mode = ModeStarters()

                    case "fishing":
                        from modules.modes.general import ModeFishing

                        mode = ModeFishing()

                    case "bunny_hop":
                        from modules.modes.general import ModeBunnyHop

                        mode = ModeBunnyHop()

            try:
                if mode:
                    next(mode.step())
            except StopIteration:
                mode = None
                continue
            except:
                console.print_exception(show_locals=True)
                mode = None
                context.bot_mode = "manual"

            context.emulator.run_single_frame()

        except SystemExit:
            raise
        except:
            console.print_exception(show_locals=True)
            sys.exit(1)
