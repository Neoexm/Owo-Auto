import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
import discord, time, requests, asyncio, random, json, colorama
import re
from discord.ext import commands
from discord.ext import tasks
import wonderwords
from wonderwords import RandomSentence
from datetime import timedelta
from io import BytesIO
import base64
from solver import auth, solve_owo
from captcha_solver import ImageToTextSolver, solve_image_by_scrappey, fetch_hcaptcha_balance, fetch_texttoimage_balance, solve_huntbot_with_2captcha
from colorama import Fore
import sys
sentences = RandomSentence()


version = "1.0"

def clear():
    os.system("title Advanced Auto OwO && cls" if os.name == "nt" else "clear")


with open("config.json") as f:
    config = json.load(f)
try:
    prefix = config.get("prefix")
    token = config.get("token")
    owodm = config['settings']['owodm_channelid']
    captcha_hook_url = config["notifications"]["captcha_alerts"]
    daily_hook_url = config["notifications"]["daily_claim_alerts"]
    huntbot_hook_url = config["notifications"]["huntbot_alert"]
    funds_hook_url = config["notifications"]["funds_alerts"]
    
except:
    print("no token found")
owochannels = config["settings"]["channel_ids"]
change_channel_after = config["settings"]["channel_change_interval"]
owochannel = 0



    
banner = r"""

              _                               _                 _           ____                
     /\      | |                             | |     /\        | |         / __ \               
    /  \   __| |_   ____ _ _ __   ___ ___  __| |    /  \  _   _| |_ ___   | |  | |_      _____  
   / /\ \ / _` \ \ / / _` | '_ \ / __/ _ \/ _` |   / /\ \| | | | __/ _ \  | |  | \ \ /\ / / _ \ 
  / ____ \ (_| |\ V / (_| | | | | (_|  __/ (_| |  / ____ \ |_| | || (_) | | |__| |\ V  V / (_) |
 /_/    \_\__,_| \_/ \__,_|_| |_|\___\___|\__,_| /_/    \_\__,_|\__\___/   \____/  \_/\_/ \___/ 
                  ____                           _                 _     _               
                 |  _ \                         (_)               (_)   | |              
                 | |_) |_   _    _ __ ___   __ _ _ _ __ ___   __ _ _  __| |_  _____ _ __ 
                 |  _ <| | | |  | '_ ` _ \ / _` | | '_ ` _ \ / _` | |/ _` \ \/ / _ \ '__|
                 | |_) | |_| |  | | | | | | (_| | | | | | | | (_| | | (_| |>  <  __/ |   
                 |____/ \__, |  |_| |_| |_|\__,_|_|_| |_| |_|\__,_|_|\__,_/_/\_\___|_|   
                         __/ |                                                           
                        |___/                                                            

"""
user_data = requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token}).json()
globalname = user_data["global_name"]
if not globalname:
    print(f"{Fore.RED}[Error] Incorrect Token Provided{Fore.RESET}")
    os.system('exit')

all_tasks = []
all_tasks_stop = []

OWO_BOT_ID = 408785106942164992
REQUIRED_GEM_TYPES = ("1", "3", "4")
GEM_TYPE_LABELS = {
    "1": "hunting",
    "3": "empowering",
    "4": "lucky",
}
GEM_RARITY_PRIORITY = {
    "f": 6,
    "l": 5,
    "m": 4,
    "e": 3,
    "r": 2,
    "u": 1,
    "c": 0,
}
CUSTOM_GEM_REGEX = re.compile(r"<a?:([flmeruc])gem([134]):\d+>", re.IGNORECASE)
HUNT_BRACKET_REGEX = re.compile(r"\[\s*(\d+)\s*/\s*(\d+)\s*\]")
SUPERSCRIPT_DIGIT_TRANSLATION = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
gem_manager_lock = None
gem_manager_state = {
    "inventory": {gem_type: [] for gem_type in REQUIRED_GEM_TYPES},
    "active": {gem_type: None for gem_type in REQUIRED_GEM_TYPES},
    "hunt_status_known": False,
    "inventory_requested": False,
    "last_inventory_message_id": None,
    "last_inventory_refresh": 0.0,
    "last_inventory_request": 0.0,
    "last_lb_all": 0.0,
    "recovery_running": False,
}


def create_tasks():
    global all_tasks
    global all_tasks_stop
    plugins = config["plugins"]
    try:
        all_tasks.append(autogemmanager)
        all_tasks_stop.append(autogemmanager)
        if plugins["autohunt"] == "true":
            all_tasks.append(autohunter)
            all_tasks_stop.append(autohunter)
        if plugins["autolevelup"] == "true":
            all_tasks.append(autolevelup)
            all_tasks_stop.append(autolevelup)
        if plugins["autoslot"] == "true":
            all_tasks.append(autoslot)
            all_tasks_stop.append(autoslot)
        if plugins["autocoinflip"] == "true":
            all_tasks.append(autocf)
            all_tasks_stop.append(autocf)
        if plugins["autopray"] == "true":
            all_tasks.append(autopray)
            all_tasks_stop.append(autopray)
        if plugins["autosell"] == "true":
            all_tasks.append(autosell)
            all_tasks_stop.append(autosell)
        if plugins["use_random_commands"] == "true":
            all_tasks.append(autorandomcommand)
            all_tasks_stop.append(autorandomcommand)
        if plugins["autohuntbot"] == "true":
            all_tasks.append(autohuntbot)
            all_tasks_stop.append(autohuntbot)
    except Exception as e:
        print(e)
    print("")
    try:
       
        all_tasks.append(owobalace)
        all_tasks.append(autodaily)
        all_tasks.append(autosleep)
        all_tasks.append(auto_channelchange)
        all_tasks.append(balanace_alerts)
        all_tasks_stop.append(autodaily)
        all_tasks_stop.append(owobalace)
        all_tasks_stop.append(autosleep)
        all_tasks_stop.append(auto_channelchange)
        all_tasks_stop.append(balanace_alerts)

    except Exception as e:
        print(e)


client = commands.Bot(
    description="Advanced Auto OwO",
    command_prefix=prefix,
    case_insensitive=True,
    self_bot=True,
    help_command=None,
    sync_presence=False
)


def check_version():
    r = requests.get(
        "https://raw.githubusercontent.com/Neoexm/Auto-Owo/main/Current-version.txt"
    )
    if r.text.rstrip() == version:
        return ""
    else:
        print(r.text)
        return f"{Fore.LIGHTMAGENTA_EX}A Newer Version Is Available: {r.text}\nConsider updating it: https://github.com/Neoexm/Auto-Owo{Fore.RESET}"


def get_entry():
    file_path = "entry.json"
    # Robust read with retries in case the file is temporarily locked or permissions are flaky
    attempts = 3
    for _ in range(attempts):
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                cowoncy = data.get("cowoncy", "")
                nextdaily = data.get("nextdaily", "")
                cookie = data.get("cookie", "")
                nexthuntbot = data.get("nexthuntbot", 0)
                return cowoncy, nextdaily, cookie, nexthuntbot
        except PermissionError:
            time.sleep(0.5)
            try:
                os.chmod(file_path, 0o666)
            except Exception:
                pass
        except FileNotFoundError:
            # create a default entry file if missing
            default = {"cowoncy": "0", "nextdaily": 0, "cookie": "", "nexthuntbot": 0}
            try:
                with open(file_path, "w") as file:
                    json.dump(default, file, indent=4)
            except Exception:
                pass
            return default["cowoncy"], default["nextdaily"], default["cookie"], default["nexthuntbot"]

    # Final attempt — if still failing, try to set permissive mode then read or return defaults
    try:
        os.chmod(file_path, 0o666)
    except Exception:
        pass
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("cowoncy", ""), data.get("nextdaily", ""), data.get("cookie", ""), data.get("nexthuntbot", 0)
    except Exception:
        # Give sensible defaults instead of crashing the bot
        return "0", 0, "", 0


def update_entry(new_cowoncy=None, new_nextdaily=None, new_cookie=None, new_nexthuntbot=None):
    file_path = "entry.json"
    try:
        with open(file_path, "r+") as file:
            data = json.load(file)
            if new_cowoncy is not None:
                data["cowoncy"] = new_cowoncy
            if new_nextdaily is not None:
                data["nextdaily"] = new_nextdaily
            if new_cookie is not None:
                data["cookie"] = new_cookie
            if new_nexthuntbot is not None:
                data["nexthuntbot"] = new_nexthuntbot
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
    except (PermissionError, OSError):
        # Try to relax permissions and retry once
        try:
            os.chmod(file_path, 0o666)
            with open(file_path, "r+") as file:
                data = json.load(file)
                if new_cowoncy is not None:
                    data["cowoncy"] = new_cowoncy
                if new_nextdaily is not None:
                    data["nextdaily"] = new_nextdaily
                if new_cookie is not None:
                    data["cookie"] = new_cookie
                if new_nexthuntbot is not None:
                    data["nexthuntbot"] = new_nexthuntbot
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        except Exception:
            # As a last resort, overwrite the file with the new values merged into defaults
            data = {
                "cowoncy": new_cowoncy if new_cowoncy is not None else "0",
                "nextdaily": new_nextdaily if new_nextdaily is not None else 0,
                "cookie": new_cookie if new_cookie is not None else "",
                "nexthuntbot": new_nexthuntbot if new_nexthuntbot is not None else 0,
            }
            try:
                with open(file_path, "w") as file:
                    json.dump(data, file, indent=4)
            except Exception:
                pass


def solvecap(problem, lambaa=None):
    print(f"{Fore.CYAN}[solvecap] invoked with problem={problem}, lambaa={lambaa}{Fore.RESET}")
    if problem == "https://owobot.com/captcha":
        print(f"{Fore.CYAN}[solvecap] detected hcaptcha flow{Fore.RESET}")
        # Get stored cookie; if unavailable, try to re-auth and persist
        try:
            print(f"{Fore.CYAN}[solvecap] attempting to read stored cookie from entry.json{Fore.RESET}")
            cooked = get_entry()[2]
            print(f"{Fore.CYAN}[solvecap] stored cookie found={bool(cooked)}, preview={cooked[:24] + '...' if cooked else 'None'}{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}[solvecap] failed to read stored cookie: {e}{Fore.RESET}")
            cooked = ""

        if not cooked:
            print(f"{Fore.YELLOW}[solvecap] no stored cookie available, calling auth(){Fore.RESET}")
            try:
                cook = auth(token=token)
                print(f"{Fore.CYAN}[solvecap] auth() returned cookie={bool(cook)}{Fore.RESET}")
                if cook:
                    update_entry(new_cookie=cook)
                    print(f"{Fore.CYAN}[solvecap] updated entry.json with fresh cookie{Fore.RESET}")
                    cooked = cook
            except Exception as e:
                print(f"{Fore.RED}[solvecap] auth() raised an exception: {e}{Fore.RESET}")
                cooked = ""

        if not cooked:
            print(f"{Fore.RED}[Solver] No cookie available for hcaptcha solver; skipping{Fore.RESET}")
            return "error|hcap"

        try:
            print(f"{Fore.CYAN}[solvecap] calling solve_owo() with cookie preview={cooked[:24] + '...' if cooked else 'None'}{Fore.RESET}")
            sol = solve_owo(cooked)
            print(f"{Fore.CYAN}[solvecap] solve_owo() returned: {sol}{Fore.RESET}")
            return f"{sol}|hcap"
        except Exception as e:
            print(f"{Fore.RED}[Solver] solve_owo failed: {e}{Fore.RESET}")
            return "error|hcap"
    else:
        print(f"{Fore.CYAN}[solvecap] detected image captcha flow, source={problem}{Fore.RESET}")
        try:
            print(f"{Fore.CYAN}[solvecap] calling ImageToTextSolver() with length={lambaa}{Fore.RESET}")
            sol = ImageToTextSolver(image=problem, length=lambaa, mode='captcha')
            print(f"{Fore.CYAN}[solvecap] ImageToTextSolver() returned: {sol}{Fore.RESET}")
            return f"{sol}|image"
        except Exception as e:
            print(f"{Fore.RED}[Solver] ImageToTextSolver failed: {e}{Fore.RESET}")
            return "error|image"


def sendhook(hook_url, content, description, image_url):
    print(f"{Fore.CYAN}[Notification] Preparing webhook request{Fore.RESET}")
    print(f"{Fore.CYAN}[Notification] Webhook URL preview: {hook_url[:60] + '...' if hook_url else 'None'}{Fore.RESET}")
    print(f"{Fore.CYAN}[Notification] Content: {truncate_log_text(content)}{Fore.RESET}")
    print(f"{Fore.CYAN}[Notification] Description: {truncate_log_text(description)}{Fore.RESET}")
    print(f"{Fore.CYAN}[Notification] Image URL: {image_url}{Fore.RESET}")
    payload = {
        "username": "OwO Logger",  # Set the username here
        "content": content,
        "embeds": [
            {
                "title": "Auto OwO",
                "description": description,
                "image": {
                    "url": image_url
                },
                "footer": {
                    "text": "Made By maimaidxer",
                    "icon_url": "https://images-ext-1.discordapp.net/external/LEdJvbRy1zsqteshdxeKJ9sk5GCksjlNwiEO5_bCYhk/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/824522317899235360/2cbb4933cb3c03a205f4ed85167a8530.png?format=webp&quality=lossless&width=291&height=291",  # Replace with your footer icon URL
                },
            }
        ],
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(hook_url, data=json.dumps(payload), headers=headers)
        print(f"{Fore.CYAN}[Notification] Webhook response status: {response.status_code}{Fore.RESET}")
        print(f"{Fore.CYAN}[Notification] Webhook response body: {truncate_log_text(response.text)}{Fore.RESET}")
        response.raise_for_status()
        print(f"{Fore.LIGHTGREEN_EX}[Notification] Sent A Webhook{Fore.RESET}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[Notification] Unable to Sent A Webhook: {e}{Fore.RESET}")


@client.event
async def on_connect():
    print("please wait, bot loading")
    create_tasks()
    
    clear()
    print(f"{Fore.LIGHTCYAN_EX}{banner}{Fore.RESET}")
    print(f"Account : {globalname}")
    print(f"prefix : {prefix}")
    print(check_version())
    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Auto OwO",
            details="Made By maimaidxer",
            timestamps={"start": time.time()},
            assets=
    {"large_image": "https://media.discordapp.net/attachments/1336378795665657958/1341091056351051776/2cbb4933cb3c03a205f4ed85167a8530.png?ex=67b4bbe0&is=67b36a60&hm=b47625464d95638d8b40be15d6502b719117506a051ea329dbc724208efb9580&=&format=webp&quality=lossless&width=291&height=291",
    "small_image": "https://media.discordapp.net/attachments/1115605458602971157/1341089828187668572/1a449430e3a9a830efebb8c57917f943.png?ex=67b4babb&is=67b3693b&hm=d8cf73451fc368c56439986d608a33e382f1090d02d3d41bd56627490ca0b435&=&format=webp&quality=lossless&width=530&height=530",
    "small_text": "uwuuwu"
        }), 
    )

def normalize_message(content):
    # Remove zero-width characters or any unintended space splitting
    return re.sub(r"\s+", " ", content.replace("\u200b", ""))


def normalize_multiline_message(content):
    content = str(content or "").replace("\u200b", "").replace("\r", "")
    lines = []
    for raw_line in content.split("\n"):
        cleaned_line = re.sub(r"\s+", " ", raw_line).strip()
        if cleaned_line:
            lines.append(cleaned_line)
    return "\n".join(lines)


def extract_owo_message_text(message):
    parts = []
    if getattr(message, "content", None):
        parts.append(message.content)

    for embed in getattr(message, "embeds", []):
        if getattr(embed, "title", None):
            parts.append(embed.title)
        if getattr(embed, "description", None):
            parts.append(embed.description)
        for field in getattr(embed, "fields", []):
            if getattr(field, "name", None):
                parts.append(field.name)
            if getattr(field, "value", None):
                parts.append(field.value)
        footer = getattr(embed, "footer", None)
        if footer and getattr(footer, "text", None):
            parts.append(footer.text)

    return normalize_multiline_message("\n".join(part for part in parts if part))


def sort_gem_items(items):
    return sorted(
        items,
        key=lambda item: (-GEM_RARITY_PRIORITY.get(item["rarity"], -1), int(item["item_id"])),
    )


def parse_gem_inventory(text):
    entries = []
    normalized_text = normalize_multiline_message(text)

    for emoji_match in CUSTOM_GEM_REGEX.finditer(normalized_text):
        match_start = emoji_match.start()
        match_end = emoji_match.end()

        prefix_text = normalized_text[max(0, match_start - 12):match_start]
        item_id_match = re.search(r"`(\d{3})`", prefix_text)
        if not item_id_match:
            continue

        suffix_text = normalized_text[match_end:match_end + 15]
        translated_suffix = suffix_text.translate(SUPERSCRIPT_DIGIT_TRANSLATION)
        quantity_match = re.match(r"\s*(\d+)", translated_suffix)
        quantity = int(quantity_match.group(1)) if quantity_match else 1

        rarity = emoji_match.group(1).lower()
        gem_type = emoji_match.group(2)

        entries.append(
            {
                "item_id": item_id_match.group(1),
                "gem_type": gem_type,
                "rarity": rarity,
                "emoji_name": f"{rarity}gem{gem_type}",
                "quantity": max(quantity, 0),
            }
        )
    return entries


def build_gem_inventory_snapshot(entries):
    inventory = {gem_type: {} for gem_type in REQUIRED_GEM_TYPES}
    for entry in entries:
        gem_type = entry.get("gem_type")
        if gem_type not in inventory:
            continue

        item_id = entry["item_id"]
        if item_id in inventory[gem_type]:
            inventory[gem_type][item_id]["quantity"] += entry["quantity"]
        else:
            inventory[gem_type][item_id] = dict(entry)

    return {
        gem_type: sort_gem_items(list(items.values()))
        for gem_type, items in inventory.items()
    }


def parse_hunt_gem_statuses(text):
    statuses = []
    normalized_text = normalize_multiline_message(text)

    for line in normalized_text.splitlines():
        bracket_matches = list(HUNT_BRACKET_REGEX.finditer(line))
        if not bracket_matches:
            continue

        line_lower = line.lower()
        if "empowered" not in line_lower and "hunt" not in line_lower:
            continue

        for position, bracket_match in enumerate(bracket_matches):
            remaining = int(bracket_match.group(1))
            total = int(bracket_match.group(2))
            bracket_start = bracket_match.start()

            prefix = line[:bracket_start]
            gem_match = None
            for match in CUSTOM_GEM_REGEX.finditer(prefix):
                gem_match = match

            if gem_match:
                rarity = gem_match.group(1).lower()
                gem_type = gem_match.group(2)
            else:
                fallback_types = ["1", "3", "4"]
                if position >= len(fallback_types):
                    continue
                gem_type = fallback_types[position]
                rarity = "c"

            statuses.append(
                {
                    "rarity": rarity,
                    "gem_type": gem_type,
                    "emoji_name": f"{rarity}gem{gem_type}",
                    "remaining_uses": remaining,
                    "total_uses": total,
                }
            )
    return statuses


def looks_like_inventory_message(text):
    normalized_text = normalize_multiline_message(text)
    lowered = normalized_text.lower()
    if any(keyword in lowered for keyword in ("inventory", "backpack")):
        return True

    if CUSTOM_GEM_REGEX.search(normalized_text):
        return True

    stripped_text = CUSTOM_GEM_REGEX.sub(" ", normalized_text.translate(SUPERSCRIPT_DIGIT_TRANSLATION))
    item_ids = re.findall(r"`?(\d{3})`?", stripped_text)
    return len(item_ids) >= 2 and ("`" in normalized_text or "\n" in normalized_text)


def looks_like_hunt_result(text):
    lowered = normalize_multiline_message(text).lower()
    if not lowered:
        return False
    if "autohunt" in lowered or "huntbot" in lowered:
        return False
    if "activated" in lowered and "gem" in lowered:
        return False
    if "hunts will be" in lowered:
        return False
    if "manual hunt" in lowered:
        return False
    return globalname.lower() in lowered and any(keyword in lowered for keyword in (" hunt", "hunt ", "hunted"))


def gem_slot_has_remaining_uses(active_gem):
    if not active_gem:
        return False
    if active_gem.get("pending"):
        return True
    remaining_uses = active_gem.get("remaining_uses")
    return remaining_uses is None or remaining_uses > 0


def inventory_has_available_gems(inventory_snapshot):
    return any(inventory_snapshot.get(gem_type) for gem_type in REQUIRED_GEM_TYPES)


def get_inventory_summary(inventory_snapshot):
    parts = []
    for gem_type in REQUIRED_GEM_TYPES:
        total_quantity = sum(item["quantity"] for item in inventory_snapshot.get(gem_type, []))
        parts.append(f"{GEM_TYPE_LABELS[gem_type]}={total_quantity}")
    return ", ".join(parts)


async def get_gem_manager_lock():
    global gem_manager_lock
    if gem_manager_lock is None:
        gem_manager_lock = asyncio.Lock()
    return gem_manager_lock


async def process_inventory_message(message, text=None, reason="inventory"):
    inventory_text = text or extract_owo_message_text(message)
    inventory_entries = parse_gem_inventory(inventory_text)
    message_id = getattr(message, "id", None)

    if not inventory_entries and CUSTOM_GEM_REGEX.search(inventory_text):
        lock = await get_gem_manager_lock()
        async with lock:
            gem_manager_state["inventory_requested"] = False
        print(f"{Fore.YELLOW}[gem-manager] skipped malformed inventory payload during {reason}{Fore.RESET}")
        return

    inventory_snapshot = build_gem_inventory_snapshot(inventory_entries)

    lock = await get_gem_manager_lock()
    async with lock:
        if message_id is not None and gem_manager_state["last_inventory_message_id"] == message_id:
            return
        gem_manager_state["inventory"] = inventory_snapshot
        gem_manager_state["inventory_requested"] = False
        gem_manager_state["last_inventory_message_id"] = message_id
        gem_manager_state["last_inventory_refresh"] = time.time()

    print(
        f"{Fore.CYAN}[gem-manager] inventory refreshed ({reason}): {get_inventory_summary(inventory_snapshot)}{Fore.RESET}"
    )
    await activate_missing_gems(message.channel, reason=f"{reason}-refresh")
    await maybe_trigger_lb_recovery(message.channel, reason=f"{reason}-refresh")


async def request_inventory_refresh(channel, reason="inventory-check"):
    if channel is None:
        return

    lock = await get_gem_manager_lock()
    async with lock:
        now = time.time()
        if gem_manager_state["inventory_requested"] and (now - gem_manager_state["last_inventory_request"] < 20):
            return
        if now - gem_manager_state["last_inventory_request"] < 8:
            return
        gem_manager_state["inventory_requested"] = True
        gem_manager_state["last_inventory_request"] = now

    print(f"{Fore.CYAN}[gem-manager] requesting inventory refresh ({reason}){Fore.RESET}")
    await channel.typing()
    await asyncio.sleep(1)
    await channel.send("owo inv")

    try:
        inventory_message = await asyncio.wait_for(
            client.wait_for(
                "message",
                check=lambda m: m.author.id == OWO_BOT_ID
                and m.channel.id == channel.id
                and looks_like_inventory_message(extract_owo_message_text(m)),
            ),
            timeout=30,
        )
    except asyncio.TimeoutError:
        lock = await get_gem_manager_lock()
        async with lock:
            gem_manager_state["inventory_requested"] = False
        print(f"{Fore.YELLOW}[gem-manager] inventory refresh timed out ({reason}){Fore.RESET}")
        return

    await process_inventory_message(inventory_message, reason=reason)


async def activate_missing_gems(channel, reason="gem-check"):
    if channel is None:
        return

    commands_to_send = []
    lock = await get_gem_manager_lock()
    async with lock:
        if not gem_manager_state["hunt_status_known"]:
            return

        for gem_type in REQUIRED_GEM_TYPES:
            if gem_slot_has_remaining_uses(gem_manager_state["active"].get(gem_type)):
                continue

            available_gems = gem_manager_state["inventory"].get(gem_type, [])
            if not available_gems:
                gem_manager_state["active"][gem_type] = None
                continue

            selected_gem = dict(available_gems[0])
            gem_manager_state["active"][gem_type] = {
                "item_id": selected_gem["item_id"],
                "rarity": selected_gem["rarity"],
                "emoji_name": selected_gem["emoji_name"],
                "remaining_uses": None,
                "total_uses": None,
                "pending": True,
                "activated_at": time.time(),
            }

            if selected_gem["quantity"] > 1:
                gem_manager_state["inventory"][gem_type][0]["quantity"] -= 1
            else:
                gem_manager_state["inventory"][gem_type].pop(0)

            commands_to_send.append((gem_type, selected_gem["item_id"], selected_gem["rarity"]))

    for gem_type, item_id, rarity in commands_to_send:
        try:
            print(
                f"{Fore.GREEN}[gem-manager] activating {rarity}{gem_type} gem with item id {item_id} ({reason}){Fore.RESET}"
            )
            await channel.send(f"owo use {item_id}")
            await asyncio.sleep(10)
        except Exception as error:
            print(
                f"{Fore.RED}[gem-manager] failed to send activation for gem type {gem_type} ({item_id}): {error}{Fore.RESET}"
            )
            lock = await get_gem_manager_lock()
            async with lock:
                gem_manager_state["active"][gem_type] = None


async def run_lb_recovery(channel, reason="recovery"):
    try:
        while True:
            print(f"{Fore.YELLOW}[gem-manager] all gem stocks empty, running owo lb all ({reason}){Fore.RESET}")
            await channel.send("owo lb all")
            await asyncio.sleep(20)
            await request_inventory_refresh(channel, reason=f"{reason}-lb-all")
            await activate_missing_gems(channel, reason=f"{reason}-lb-all")

            lock = await get_gem_manager_lock()
            async with lock:
                inventory_empty = not inventory_has_available_gems(gem_manager_state["inventory"])
                no_active_gems = not any(
                    gem_slot_has_remaining_uses(gem_manager_state["active"].get(gem_type))
                    for gem_type in REQUIRED_GEM_TYPES
                )
                if not (inventory_empty and no_active_gems):
                    break

            await asyncio.sleep(5)
    finally:
        lock = await get_gem_manager_lock()
        async with lock:
            gem_manager_state["recovery_running"] = False


async def maybe_trigger_lb_recovery(channel, reason="gem-check"):
    if channel is None:
        return

    lock = await get_gem_manager_lock()
    async with lock:
        hunt_status_known = gem_manager_state["hunt_status_known"]
        inventory_known = gem_manager_state["last_inventory_refresh"] > 0
        inventory_empty = not inventory_has_available_gems(gem_manager_state["inventory"])
        no_active_gems = not any(
            gem_slot_has_remaining_uses(gem_manager_state["active"].get(gem_type))
            for gem_type in REQUIRED_GEM_TYPES
        )
        recently_triggered = time.time() - gem_manager_state["last_lb_all"] < 25

        if (
            gem_manager_state["recovery_running"]
            or recently_triggered
            or not hunt_status_known
            or not inventory_known
            or not inventory_empty
            or not no_active_gems
        ):
            return

        gem_manager_state["recovery_running"] = True
        gem_manager_state["last_lb_all"] = time.time()

    asyncio.create_task(run_lb_recovery(channel, reason=reason))


async def ensure_gem_readiness(channel, reason="gem-check"):
    if channel is None:
        return

    lock = await get_gem_manager_lock()
    async with lock:
        missing_types = [
            gem_type
            for gem_type in REQUIRED_GEM_TYPES
            if not gem_slot_has_remaining_uses(gem_manager_state["active"].get(gem_type))
        ]
        inventory_known = gem_manager_state["last_inventory_refresh"] > 0
        inventory_stale = inventory_known and (time.time() - gem_manager_state["last_inventory_refresh"] >= 300)
        inventory_empty = not inventory_has_available_gems(gem_manager_state["inventory"])

    if missing_types and (not inventory_known or inventory_stale or inventory_empty):
        await request_inventory_refresh(channel, reason=reason)

    await activate_missing_gems(channel, reason=reason)
    await maybe_trigger_lb_recovery(channel, reason=reason)


async def handle_hunt_gem_statuses(message, statuses):
    reported_types = {status["gem_type"] for status in statuses}
    depleted_types = []
    status_summaries = []

    lock = await get_gem_manager_lock()
    async with lock:
        gem_manager_state["hunt_status_known"] = True

        for gem_type in REQUIRED_GEM_TYPES:
            if gem_type not in reported_types:
                active_gem = gem_manager_state["active"].get(gem_type)
                if (
                    active_gem
                    and active_gem.get("pending")
                    and (time.time() - active_gem.get("activated_at", 0) < 120)
                ):
                    continue
                gem_manager_state["active"][gem_type] = None

        for status in statuses:
            gem_type = status["gem_type"]
            active_gem = gem_manager_state["active"].get(gem_type) or {}
            status_summaries.append(
                f"{GEM_TYPE_LABELS[gem_type]}={status['remaining_uses']}/{status['total_uses']}"
            )

            if status["remaining_uses"] <= 0:
                gem_manager_state["active"][gem_type] = None
                depleted_types.append(gem_type)
                continue

            gem_manager_state["active"][gem_type] = {
                "item_id": active_gem.get("item_id"),
                "rarity": status["rarity"],
                "emoji_name": status["emoji_name"],
                "remaining_uses": status["remaining_uses"],
                "total_uses": status["total_uses"],
                "pending": False,
                "activated_at": active_gem.get("activated_at", time.time()),
            }

    if status_summaries:
        print(
            f"{Fore.CYAN}[gem-manager] hunt gem status update: {', '.join(status_summaries)}{Fore.RESET}"
        )
    else:
        print(f"{Fore.YELLOW}[gem-manager] hunt result reported no active gem effects{Fore.RESET}")

    if depleted_types:
        print(
            f"{Fore.YELLOW}[gem-manager] depleted gem types detected: {', '.join(depleted_types)}{Fore.RESET}"
        )

    await ensure_gem_readiness(message.channel, reason="hunt-status")


async def handle_gem_message(message, text=None):
    owo_text = text or extract_owo_message_text(message)
    inventory_entries = parse_gem_inventory(owo_text)

    lock = await get_gem_manager_lock()
    async with lock:
        inventory_requested = gem_manager_state["inventory_requested"]

    if inventory_entries or (inventory_requested and looks_like_inventory_message(owo_text)):
        await process_inventory_message(message, text=owo_text, reason="owo-message")
        return

    hunt_statuses = parse_hunt_gem_statuses(owo_text)
    if hunt_statuses or looks_like_hunt_result(owo_text):
        await handle_hunt_gem_statuses(message, hunt_statuses)

@client.event
async def on_message(message):
    await client.process_commands(message)

    if not message.author.bot or message.author.id != OWO_BOT_ID:
        return

    if message.channel.id not in owochannels and message.channel.id != owodm:
        return

    normalized_content = normalize_message(message.content)
    normalized_lower = normalized_content.lower()
    owo_message_text = extract_owo_message_text(message)

    if ("⚠️" in normalized_content) and (("letter word" in normalized_content)
        or ("link" in normalized_content or "https://owobot.com" in normalized_content)
    ):
        print(f"{Fore.CYAN}[captcha] captcha trigger detected: {summarize_message(message)}{Fore.RESET}")
        print(f"{Fore.CYAN}[captcha] stopping {len(all_tasks_stop)} running tasks before solve{Fore.RESET}")
        for task in all_tasks_stop:
            print(f"{Fore.CYAN}[captcha] cancelling task: {getattr(task, '__name__', str(task))}{Fore.RESET}")
            task.cancel()
        captchamsg = message.jump_url
        try:
            captcha = message.attachments[0].url
            print(f"{Fore.CYAN}[captcha] attachment count: {len(message.attachments)}{Fore.RESET}")
            print(f"{Fore.CYAN}[captcha] captcha attachment url: {captcha}{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.YELLOW}[captcha] no attachment found, defaulting to owobot captcha page: {e}{Fore.RESET}")
            captcha = "https://owobot.com/captcha"
        print(f"{Fore.CYAN}[captcha] sending detection webhook for message: {captchamsg}{Fore.RESET}")
        sendhook(
            hook_url=captcha_hook_url,
            content=f"@everyone Captcha Alert!",
            description=f"A Captcha Has Been Detected!\n*Captcha Message*: [Jump to Message]({captchamsg})",
            image_url="https://images-ext-1.discordapp.net/external/mflqo1HcoLk6g1HEXdHLOBbKSVZ8Lq690mXrNA3yeX4/https/repository-images.githubusercontent.com/520888256/df57c468-cb50-4f1e-bb10-be6d7341b262?format=webp&width=797&height=448",
        )

        if "letter word" in normalized_content:
            captcha_length = normalized_content[normalized_content.find("letter word") - 2]
            print(f"{Fore.CYAN}[captcha] image captcha detected with expected length={captcha_length}{Fore.RESET}")
            solution = solvecap(captcha, lambaa=captcha_length)
        else:
            print(f"{Fore.CYAN}[captcha] hcaptcha/link challenge detected, requesting fresh cookie via auth(){Fore.RESET}")
            cook = auth(token=token)
            if cook is None:
                print(f"{Fore.RED}[captcha] auth() returned None, aborting captcha flow{Fore.RESET}")
                return
            update_entry(new_cookie=cook)
            print(f"{Fore.CYAN}[captcha] stored fresh cookie from auth(){Fore.RESET}")
            print(f"{Fore.GREEN}Solving Hcaptcha{Fore.RESET}")
            solution = solvecap(captcha, lambaa=None)

        print(f"{Fore.CYAN}[captcha] solvecap() returned raw solution: {solution}{Fore.RESET}")
        solution_parts = solution.split("|") if isinstance(solution, str) else ["error", "unknown"]
        if len(solution_parts) < 2:
            solution_parts.append("unknown")
        print(f"{Fore.CYAN}[captcha] parsed solution parts: {solution_parts}{Fore.RESET}")
        user = client.get_user(OWO_BOT_ID)
        print(f"{Fore.CYAN}[captcha] resolved OwO user object: {user}{Fore.RESET}")

        if solution_parts[1] == "image":
            print(f"{Fore.CYAN}[captcha] sending image captcha answer to OwO DM: {solution_parts[0]}{Fore.RESET}")
            await user.send(solution_parts[0])
            try:
                print(f"{Fore.CYAN}[captcha] waiting for human-verification confirmation from OwO{Fore.RESET}")
                verification_message = await asyncio.wait_for(
                    client.wait_for(
                        "message",
                        check=lambda m: m.author == message.author
                        and "I have verified that you are human! Thank you! :3" in m.content,
                    ),
                    timeout=240,
                )
                print(f"{Fore.CYAN}[captcha] verification message received: {summarize_message(verification_message)}{Fore.RESET}")
                if "I have verified" in verification_message.content:
                    channel = client.get_channel(owochannel)
                    print(f"{Fore.CYAN}[captcha] captcha solved successfully, resuming autoowo in channel {owochannel}{Fore.RESET}")
                    sendhook(
                        hook_url=captcha_hook_url,
                        content=f"@everyone Captcha Alert!",
                        description=f"Captcha Has Been Solved!",
                        image_url="https://images-ext-1.discordapp.net/external/mflqo1HcoLk6g1HEXdHLOBbKSVZ8Lq690mXrNA3yeX4/https/repository-images.githubusercontent.com/520888256/df57c468-cb50-4f1e-bb10-be6d7341b262?format=webp&width=797&height=448",
                    )
                    await channel.send(f"{prefix}autoowo")
                else:
                    print(f"{Fore.RED}[captcha] received unexpected verification content, exiting bot{Fore.RESET}")
                    sendhook(
                        hook_url=captcha_hook_url,
                        image_url="https://images-ext-1.discordapp.net/external/mflqo1HcoLk6g1HEXdHLOBbKSVZ8Lq690mXrNA3yeX4/https/repository-images.githubusercontent.com/520888256/df57c468-cb50-4f1e-bb10-be6d7341b262?format=webp&width=797&height=448",
                        content=f"@everyone Captcha Alert!",
                        description=f"A Captcha Cant Be Solved, Bot Has Been Stopped!",
                    )
                    time.sleep(4)
                    sys.exit()
            except asyncio.TimeoutError:
                print(f"{Fore.RED}[Timeout] captcha timed out.{Fore.RESET}")
                sendhook(
                    hook_url=captcha_hook_url,
                    image_url="https://images-ext-1.discordapp.net/external/mflqo1HcoLk6g1HEXdHLOBbKSVZ8Lq690mXrNA3yeX4/https/repository-images.githubusercontent.com/520888256/df57c468-cb50-4f1e-bb10-be6d7341b262?format=webp&width=797&height=448",
                    content=f"@everyone Captcha Alert!",
                    description=f"A Captcha Cant Be Solved, Bot Has Been Stopped!, Reason: Captcha Took Too Long Too Solve",
                )
                time.sleep(5)
                sys.exit()
        elif solution_parts[0] == "solved":
            channel = client.get_channel(owochannel)
            print(f"{Fore.CYAN}[captcha] hcaptcha solve returned success, resuming autoowo in channel {owochannel}{Fore.RESET}")
            sendhook(
                hook_url=captcha_hook_url,
                content=f"@everyone Captcha Alert!",
                description=f"Captcha Has Been Solved!",
                image_url="https://images-ext-1.discordapp.net/external/mflqo1HcoLk6g1HEXdHLOBbKSVZ8Lq690mXrNA3yeX4/https/repository-images.githubusercontent.com/520888256/df57c468-cb50-4f1e-bb10-be6d7341b262?format=webp&width=797&height=448",
            )
            await channel.send(f"{prefix}autoowo")
        else:
            print(f"{Fore.RED}[captcha] solver returned failure state: {solution_parts}{Fore.RESET}")
            sendhook(
                hook_url=captcha_hook_url,
                image_url="https://images-ext-1.discordapp.net/external/mflqo1HcoLk6g1HEXdHLOBbKSVZ8Lq690mXrNA3yeX4/https/repository-images.githubusercontent.com/520888256/df57c468-cb50-4f1e-bb10-be6d7341b262?format=webp&width=797&height=448",
                content=f"@everyone Captcha Alert!",
                description=f"A Captcha Cant Be Solved, Bot Has Been Stopped!",
            )
            time.sleep(4)
            sys.exit()
        return

    if any(k in normalized_lower for k in ("nu", "your next", "your daily")) and globalname in normalized_content:
        if "nu" in normalized_lower:
            pattern = r"(\d+)H (\d+)M (\d+)S"
            match = re.search(pattern, normalized_content)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                next_daily = time.time() + total_seconds
                update_entry(new_nextdaily=next_daily)
                print(
                    f"{Fore.LIGHTYELLOW_EX}[Logger] Your Next Daily: {str(timedelta(seconds=total_seconds))}s{Fore.RESET}"
                )

    await handle_gem_message(message, owo_message_text)


def change_channel():
    global owochannel
    new_owochannel = random.choice(owochannels)
    after = client.get_channel(new_owochannel)
    owochannel = new_owochannel
    print(f"{Fore.YELLOW}[Logger] Set OwO Channel To #{after.name}")

@tasks.loop(seconds=random.randrange(16, 45))
async def autohunter():
    channel = client.get_channel(owochannel)
    await ensure_gem_readiness(channel, reason="before-hunt")
    await channel.typing()
    await asyncio.sleep(2)
    await channel.send("owo hunt")
    await asyncio.sleep(15)
    await channel.send("owo battle")


@tasks.loop(seconds=45)
async def autogemmanager():
    channel = client.get_channel(owochannel)
    await ensure_gem_readiness(channel, reason="scheduled-check")


@tasks.loop(minutes=random.randrange(5, 7))
async def autopray():
    channel = client.get_channel(owochannel)
    await asyncio.sleep(15)
    await channel.typing()
    await channel.send("owo pray")


@tasks.loop(seconds=random.randrange(15, 60))
async def autolevelup():
    channel = client.get_channel(owochannel)
    await channel.typing()
    await asyncio.sleep(11)
    xp = random.choice(("owo", "UwUUwU", "uwu"))
    message = random.choice((xp, f"{sentences.sentence()}owo"))
    await channel.send(message)
    await asyncio.sleep(3)


@tasks.loop(minutes=5)
async def autodaily():
    channel = client.get_channel(owochannel)
    if not get_entry()[1] - time.time() <= 0:
        return
    await channel.typing()
    await asyncio.sleep(3)
    await channel.send("owo daily")
    daily_message = await asyncio.wait_for(
                            client.wait_for(
                                "message",
                                check=lambda m: "Here is your daily"
                                in m.content,
                            ),
                            timeout=60,
                        )
    if daily_message:
        sendhook(content="Daily Alert!!", description="A Daily Has been Claimed", hook_url=daily_hook_url, image_url="https://cdn.discordapp.com/emojis/427352600476647425.webp?size=56&quality=lossless")
    await channel.send("owo cookie <@408785106942164992>")


@tasks.loop(minutes=10)
async def autosell():
    channel = client.get_channel(owochannel)
    await asyncio.sleep(16)
    await channel.send(f"owo sell {config['settings']['animal_types']}")


@tasks.loop(minutes=8)
async def autoslot():
    channel = client.get_channel(owochannel)
    amount = random.choice(config["settings"]["slotamount"])
    await channel.send(f"owo s {amount}")

@tasks.loop(minutes=5)
async def autocf():
    channel = client.get_channel(owochannel)
    amount = random.choice(config["settings"]["autocoinflip_amount"])
    await channel.send(f"owo cf {amount}")


@tasks.loop(minutes=15)
async def owobalace():
    channel = client.get_channel(owochannel)
    await asyncio.sleep(5)
    await channel.send(f"owo cash")
    balance_message = await asyncio.wait_for(
                            client.wait_for(
                                "message",
                                check=lambda m: "cowoncy" 
                                in m.content,
                            ),
                            timeout=60,
                        )
    if "cowoncy" in balance_message.content and not "sent" in balance_message.content:
                pattern = r"\| {}\*\*, you currently have \*\*__([\d,]+)__ cowoncy!".format(
                    re.escape(globalname)
                )
                match = re.search(pattern, balance_message.content)
                if match:
                    cowoncy_amount = match.group(1).replace(",", "")
                    print(
                        f"{Fore.LIGHTYELLOW_EX}[Logger] You Have {cowoncy_amount} Cowoncy{Fore.RESET}"
                    )
                    update_entry(new_cowoncy=cowoncy_amount)
                    print(
                        f"{Fore.CYAN}[Logger] Saved cowoncy balance for autohunt usage: {cowoncy_amount}{Fore.RESET}"
                    )
                return
            


@tasks.loop(minutes=random.randrange(15, 20))
async def autosleep():
    tosleep =random.randrange(3, 8)
    print(f"{Fore.LIGHTGREEN_EX}[Sleeper] Bot Sleeping for {tosleep} Minutes{Fore.RESET}")
    all_tasks_stop.remove(autosleep)
    if config['plugins']["autohuntbot"] == "true":
        all_tasks_stop.remove(autohuntbot)
    for task in all_tasks_stop:
        try:
            task.cancel()
        except RuntimeError:
            pass
    await asyncio.sleep(tosleep*60)
    all_tasks_stop.append(autosleep)
    if config['plugins']["autohuntbot"] == "true":
        all_tasks_stop.append(autohuntbot) 
    print(f"{Fore.LIGHTGREEN_EX}[Sleeper] Bot Again Resumed{Fore.RESET}")
    for task in all_tasks:
        try:
            if task.is_running():
                task.restart()
            else:
                task.start()
        except RuntimeError:
            pass
        await asyncio.sleep(5)
    
def get_random_autohunt_amount():
    stored_cowoncy = get_entry()[0]
    print(f"{Fore.CYAN}[autohuntbot] stored cowoncy value from entry: {stored_cowoncy}{Fore.RESET}")

    try:
        cowoncy_amount = int(str(stored_cowoncy).replace(",", "").strip() or "0")
    except (TypeError, ValueError):
        print(f"{Fore.YELLOW}[autohuntbot] invalid stored cowoncy value, defaulting autohunt amount to 1{Fore.RESET}")
        return 1

    max_amount = max(1, cowoncy_amount // 2)
    amount = random.randint(1, max_amount)
    print(f"{Fore.CYAN}[autohuntbot] computed max autohunt amount from cowoncy: {max_amount}{Fore.RESET}")
    print(f"{Fore.CYAN}[autohuntbot] randomly selected autohunt amount: {amount}{Fore.RESET}")
    return amount


def truncate_log_text(value, limit=350):
    value = str(value or "")
    return value if len(value) <= limit else f"{value[:limit]}...<truncated {len(value) - limit} chars>"


def summarize_message(message):
    attachment_urls = []
    if getattr(message, 'attachments', None):
        attachment_urls = [attachment.url for attachment in message.attachments]

    return {
        "author_id": getattr(message.author, 'id', None),
        "channel_id": getattr(message.channel, 'id', None),
        "content": truncate_log_text(getattr(message, 'content', '')),
        "attachments": attachment_urls,
        "jump_url": getattr(message, 'jump_url', None),
    }
     
@tasks.loop(minutes=6)
async def autohuntbot():
    try:
        print(f"{Fore.CYAN}[autohuntbot] loop triggered at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}{Fore.RESET}")
        channel = client.get_channel(owochannel)
        if channel is None:
            print(f"{Fore.RED}[autohuntbot] current channel is None for channel id {owochannel}{Fore.RESET}")
            return

        next_huntbot_at = get_entry()[3]
        remaining = next_huntbot_at - time.time()
        print(f"{Fore.CYAN}[autohuntbot] active channel id: {owochannel}{Fore.RESET}")
        print(f"{Fore.CYAN}[autohuntbot] next_huntbot_at={next_huntbot_at}, remaining={remaining:.2f}s{Fore.RESET}")

        if not remaining <= 0:
            print(f"{Fore.YELLOW}[autohuntbot] skipping run because cooldown is still active{Fore.RESET}")
            return

        await asyncio.sleep(3)
        print(f"{Fore.CYAN}[autohuntbot] sending initial command: owo autohunt{Fore.RESET}")
        await channel.send("owo autohunt")
        await asyncio.sleep(30)
        print(f"{Fore.CYAN}[autohuntbot] sending follow-up command: owo autohunt 1d{Fore.RESET}")
        await channel.send("owo autohunt 1d")
        print(f"{Fore.CYAN}[autohuntbot] waiting for password prompt message{Fore.RESET}")

        try:
            amount_message = await asyncio.wait_for(
                client.wait_for(
                    "message",
                    check=lambda m: "password" in m.content,
                ),
                timeout=60,
            )
            print(f"{Fore.CYAN}[autohuntbot] password prompt received: {summarize_message(amount_message)}{Fore.RESET}")
        except asyncio.TimeoutError:
            print(f"{Fore.YELLOW}[autohuntbot] timed out waiting for password message{Fore.RESET}")
            return

        # Ensure there is an attachment
        if not getattr(amount_message, 'attachments', None) or len(amount_message.attachments) == 0:
            print(f"{Fore.YELLOW}[autohuntbot] no attachments found in amount_message, skipping{Fore.RESET}")
            print(f"{Fore.YELLOW}[autohuntbot] amount_message details: {summarize_message(amount_message)}{Fore.RESET}")
            await asyncio.sleep(180)
            return

        attachment_url = amount_message.attachments[0].url
        print(f"{Fore.CYAN}[autohuntbot] attachment count: {len(amount_message.attachments)}{Fore.RESET}")
        print(f"{Fore.CYAN}[autohuntbot] first attachment url: {attachment_url}{Fore.RESET}")
        print(f"{Fore.GREEN}[autohuntbot] solving password image with 2Captcha{Fore.RESET}")
        password = solve_huntbot_with_2captcha(attachment_url)
        print(f"{Fore.CYAN}[autohuntbot] raw password solver response: {password}{Fore.RESET}")
        if password:
            password = re.sub(r"\s+", "", password)
            print(f"{Fore.CYAN}[autohuntbot] normalized password: {password}{Fore.RESET}")

        if not password:
            print(f"{Fore.YELLOW}[autohuntbot] no password extracted, aborting autohunt{Fore.RESET}")
            await asyncio.sleep(180)
            return

        amount = get_random_autohunt_amount()
        print(f"{Fore.CYAN}[autohuntbot] using balance-driven autohunt amount: {amount}{Fore.RESET}")

        final_command = f"owo autohunt {amount} {password} "
        print(f"{Fore.CYAN}[autohuntbot] sending final command: {final_command}{Fore.RESET}")
        await channel.send(final_command)
        print(f"{Fore.CYAN}[autohuntbot] waiting for huntbot confirmation response{Fore.RESET}")

        try:
            huntbot_msg = await asyncio.wait_for(
                client.wait_for(
                    "message",
                    check=lambda m: "I WILL BE BACK IN" in m.content,
                ),
                timeout=60,
            )
            print(f"{Fore.CYAN}[autohuntbot] huntbot confirmation received: {summarize_message(huntbot_msg)}{Fore.RESET}")
        except asyncio.TimeoutError:
            print(f"{Fore.YELLOW}[autohuntbot] timed out waiting for huntbot confirmation{Fore.RESET}")
            return

        time_str = re.search(r"(\d+)M", huntbot_msg.content)
        if time_str:
            minutes = int(time_str.group(1)) + 2
        else:
            minutes = 2
        seconds = minutes * 60
        print(f"{Fore.CYAN}[autohuntbot] parsed cooldown minutes: {minutes}, seconds: {seconds}{Fore.RESET}")
        sendhook(hook_url=huntbot_hook_url, content="HuntBot Alert!!", description=f"Huntbot Started!!\n[Jump to Message]({huntbot_msg.jump_url})", image_url="https://images-ext-1.discordapp.net/external/r-T0CN-zkuhykmnsWyy6gRSkZyAb-mm7EDeH-lUi_w8/https/cdn.discordapp.com/emojis/459996048379609098.png?format=webp&quality=lossless&width=160&height=160")
        update_entry(new_nexthuntbot=time.time() + seconds)
        print(f"{Fore.CYAN}[autohuntbot] updated next_huntbot timestamp to {time.time() + seconds}{Fore.RESET}")
        print(f"{Fore.CYAN}[autohuntbot] sleeping for {seconds} seconds until next autohuntbot window{Fore.RESET}")
        await asyncio.sleep(seconds)
    except Exception as e:
        print(f"{Fore.RED}[autohuntbot] unhandled exception: {e}{Fore.RESET}")
        return



@tasks.loop(seconds=random.randrange(35, 120))
async def autorandomcommand():
    channel = client.get_channel(owochannel)
    await channel.typing()
    msg = random.choice(config['settings']['random_commands'])
    await channel.send(f"owo {msg}")
    await asyncio.sleep(3)

@tasks.loop(minutes=2)
async def balanace_alerts():
    hbal = fetch_hcaptcha_balance()
    txtbal = fetch_texttoimage_balance()
   
    if hbal and txtbal < 0:
        sendhook(description="Keys Ran Out Of Funds Please Refill ANd then Restart Bot", hook_url=funds_hook_url, content="@everyone Bot Stopped!!", image_url="https://media.discordapp.net/attachments/1251479335647576169/1271412600915230720/Money-Bag-Transparent-PNG.png?ex=66b73ec1&is=66b5ed41&hm=33fadea61e4229b908c3e5c0a3423bf48318f1a5e111f93245618141ae5ce607&=&format=webp&quality=lossless&width=437&height=437")
        sys.exit()
    else:
        return


@tasks.loop(minutes=random.choice(change_channel_after))
async def auto_channelchange():
    change_channel()

@client.command()
async def help(ctx):
    msg = f'''
    ```ini
    [Made By maimaidxer]
      [Help Command]
⁙ {prefix}autoowo - Starts Farming OwO Automatically
⁙ {prefix}stopautoowo - stops Farming OwO
⁙ {prefix}chhservicekey (new key) - changes hcaptcha service key
⁙ {prefix}chtexttoimagekey (new key) - changes texttoimage service key
⁙ {prefix}balance - returns each service balances
⁙ {prefix}info - returns the instance info along other details
```
        [Github.com/Neoexm]
'''
    await ctx.send(f"{msg}")


@client.command()
async def autoowo(ctx):
    wait =random.randrange(3, 8)
    await ctx.send("> Started Auto OwO - By maimaidxer")
    change_channel()
    for task in all_tasks:
        try:
            if task.is_running():
                task.restart()
            else:
                task.start()
        except RuntimeError:
            pass
        await asyncio.sleep(wait)


@client.command()
async def stopautoowo(ctx):
    await ctx.send("> Stopped Auto OwO")
    for task in all_tasks_stop:
        try:
            task.cancel()
        except RuntimeError:
            pass
    
def update_json(file_path, key_path, new_value):
    # Read the original file content
    with open(file_path, 'r') as file:
        original_content = file.read()
    
    # Parse the JSON data from the content
    data = json.loads(original_content)
    
    # Traverse the JSON object to update the specific value
    keys = key_path.split('.')
    temp_data = data
    for key in keys[:-1]:
        temp_data = temp_data[key]
    temp_data[keys[-1]] = new_value
    
    # Convert the updated JSON data to a formatted string
    updated_json_str = json.dumps(data, indent=2)
    
    # Use regex to replace the old value with the new value while keeping the original formatting intact
    def replace_value(match):
        return f'"{key_path}": "{new_value}"'
    
    # Find the value to replace in the original content
    pattern = re.compile(rf'"{key_path}":\s*".*?"')
    formatted_content = pattern.sub(replace_value, original_content)

    # Write the formatted content back to the file
    with open(file_path, 'w') as file:
        file.write(formatted_content)

@client.command()
async def chhservicekey(ctx, key=None):
    if key is None:
        await ctx.reply("`providing a hcaptcha_key key is must`")
    else:
        file_path = 'config.json'
        update_json(file_path=file_path, key_path='captcha.hcaptcha_key', new_value=key)
        await ctx.message.delete()
        await ctx.send("`Updated hcaptcha_key Key Successfully`")

@client.command()
async def chtexttoimagekey(ctx, key=None):
    if key is None:
        await ctx.reply("`providing a TextToImage_key key is must`")
    else:
        file_path = 'config.json'
        update_json(file_path=file_path, key_path='captcha.TextToImage_key', new_value=key)
        await ctx.message.delete()
        await ctx.send("`Updated TextToImage_key Key Successfully`")

@client.command()
async def balance(ctx):
    message = await ctx.send('`Fetching balance...`')
    hbal = fetch_hcaptcha_balance()
    txtbal = fetch_texttoimage_balance()
    msg = f'''
```ini
    [Balance]

  Hcaptcha Balance: "{hbal}"    
  TextToImage Balance: "{txtbal}"   
```
'''
    await message.edit(content=msg)

@client.command()
async def info(ctx):
    message = await ctx.reply("`fetching details...`")
    ping = client.latency * 1000
    r = requests.get(
        "https://raw.githubusercontent.com/Neoexm/Auto-Owo/main/Current-version.txt"
    )
    ver = r.text.rstrip()
    msg = f'''```ini
    [ Adv Auto OwO | Information ]

User: "{globalname}"
Latency: "{ping}ms"
Version: "{ver}"
Hservice: "{config['captcha']['hcaptcha_service']}"
TextToImage Service: "{config['captcha']['TextToImage_service']}"
Current OwO Channel: "{owochannel}"
OwO Dm Channel: "{owodm}"
```
'''
    await message.edit(content=msg)

client.run(token)
