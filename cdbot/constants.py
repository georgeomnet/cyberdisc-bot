import base64
import re
from os import environ

DEPLOY = bool(environ.get("DEPLOY"))


def getenv(name: str, fallback: str = "") -> str:
    """Return an (optionally base64-encoded) env var."""
    variable = environ.get(name)
    if DEPLOY and variable is not None:
        variable = base64.b64decode(variable).decode()
    return variable or fallback


class PostgreSQL:
    PGHOST = getenv("PGHOST")
    PGPORT = getenv("PGPORT")
    PGUSER = getenv("PGUSER")
    PGDATABASE = getenv("PGDATABASE")
    PGPASSWORD = getenv("PGPASSWORD")


class Maths:
    LATEX_RE = re.compile(r"\${1,2}(.*?)\${1,2}", re.DOTALL)
    LATEX_RESPONSE_RE = re.compile(r"^([-]?\d+)\r?\n?(\S+)\s([-]?\d+)\s(\d+)\s(\d+)\r?\n?([\s\S]*)")

    LATEX_PREAMBLE = (
        "\\usepackage{amsmath}\n"
        "\\usepackage{amssymb}\n"
        "\\usepackage{amsthm}\n"
        "\\usepackage{amsfonts}\n"
        "\\usepackage{mathtools}\n"
        "\\usepackage{stmaryrd}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage{longtable}\n"
        "\n"
        "\\usepackage{graphicx}\n"
        "\\usepackage{subcaption}\n"
        "\\usepackage{caption}\n"
        "\n"
        "\\usepackage{booktabs}\n"
        "\\usepackage[separate-uncertainty]{siunitx}\n"
        "\\usepackage[version=4]{mhchem}\n"
        "\\usepackage{mathabx}\n"
        "\n"
        "\\newtheorem{theorem}{Theorem}[section]\n"
        "\\newtheorem{corollary}{Corollary}[theorem]\n"
        "\\newtheorem{procedure}{Procedure}[section]\n"
        "\\newtheorem{lemma}[theorem]{Lemma}\n"
        "\n"
        "\\theoremstyle{remark}\n"
        "\\newtheorem*{remark}{Remark}\n"
        "\n"
        "\\theoremstyle{definition}\n"
        "\\newtheorem{definition}{Definition}[section]")

    BLOCKED_CHANNELS = [411573884597436416]

    class Challenges:
        URL = "https://cms-kcl.cloud.contensis.com/api/delivery/projects/mathsSchool/entries/search?linkDepth=1"
        CHALLENGE_RE = re.compile(r"Challenge (\d+): .*")
        TOPIC = "Nerds, the lot of you | {0}"
        TOPIC_RE = re.compile(r"Challenge (\d+)")
        TOKEN = getenv("MATHS_TOKEN")
        CHANNEL = int(environ.get("MATHS_CHANNEL", "457923834893434881"))


class Roles:
    class Elite:
        class VET2018:
            ATTENDEES = int(environ.get("2018_MEMBERS_ID", "453581429528461313"))

        class VET2019:
            ATTENDEES = int(environ.get("2019_MEMBERS_ID", "580387468336037888"))
            CYBERIST = int(environ.get("2019_CYBERIST_MEMBERS_ID", "610387199300730900"))
            FORENSICATOR = int(environ.get("2019_FORENSICATOR_MEMBERS_ID", "580387897644023811"))

        class VET2020:
            TALENTDEV = int(environ.get("TALENTDEV_MEMBERS_ID", "669927831031250954"))
            ELITEONLINE = int(environ.get("2020_ONLINE_MEMBERS_ID", "715852962664153168"))
            ELITE503 = int(environ.get("2020_503_MEMBERS_ID", "719957290039378022"))
            ELITE504 = int(environ.get("2020_504_MEMBERS_ID", "719957222657884200"))
            ELITE500 = int(environ.get("2020_500_MEMBERS_ID", "719957182308679822"))
            ELITEEHF = int(environ.get("2020_EHF_MEMBERS_ID", "722188749378683020"))

        class VET2021:
            ATTENDEES = int(environ.get("2021_MEMBERS_ID", "844211211553603654"))

    class Exchange:
        SHORTLIST = int(environ.get("EXCH_S_MEMBERS_ID", "582894164597932034"))
        CONFIRMED = int(environ.get("EXCH_C_MEMBERS_ID", "585150522336608256"))


# Cyber Constants
BOT_TOKEN = getenv("BOT_TOKEN")
SENTRY_URL = getenv("SENTRY_URL")

# Fun constants
QUOTES_DELETION_QUOTA = int(environ.get("QUOTES_DELETION_QUOTA", "10"))
QUOTES_CHANNEL_ID = int(environ.get("QUOTES_CHANNEL_ID", "463657120441696256"))
QUOTES_BOT_ID = 292953664492929025
LOGGING_CHANNEL_ID = int(environ.get("LOGGING_CHANNEL_ID", "538494690601992212"))
WELCOME_BOT_ID = 155149108183695360
CMA_LINKS = {"1": "https://cdn.discordapp.com/attachments/450107193820446722/492649412560945164/unknown.png",
             "2": "https://cdn.discordapp.com/attachments/450107193820446722/492649644623659014/unknown.png",
             "3": "https://cdn.discordapp.com/attachments/450107193820446722/492649912035573770/unknown.png",
             "3a": "https://cdn.discordapp.com/attachments/450107193820446722/492650366454857737/unknown.png",
             "3za": "https://cdn.discordapp.com/attachments/450107193820446722/492650170656489472/unknown.png",
             }
REACT_EMOTES = ["\N{ONCOMING POLICE CAR}", "\N{DUCK}", "\U0001f645 \N{NO ENTRY} \N{CROSSED SWORDS}"]
REACT_TRIGGERS = {"kali": REACT_EMOTES[0], "duck": REACT_EMOTES[1], "cybergame": "*CyberStart Game",
                  "cyberstart access": "*CyberStart Assess", "cyberessentials": "*CyberStart Essentials",
                  "cyberdiscovery game": "*CyberStart Game", "cyberdiscovery access": "*CyberStart Assess",
                  "13.1": REACT_EMOTES[2], "bill gates": "Alan Turing?", "alan turing": "Bill Gates?",
                  "sibelius": "https://i.imgur.com/PwgGWV8.png?1", "we are number one": "HEY!",
                  "I can break these cuffs": "{mention}, you can't break those cuffs!",
                  "ancestry.com": "https://i.imgur.com/DDqugBj.png"}
WORD_MATCH_RE = r"^.*\b{}\b.*$"

# General constants
WELCOME_MESSAGE = ("Welcome to the Cyber Discovery discussion discord! Before you begin, please check the "
                   "rules, roles and information in <#409853512185282561> to answer any questions.")
WELCOME_CHANNEL_ID = int(environ.get("WELCOME_CHANNEL_ID", "411573884597436416"))

# Misc roles
HUNDRED_PERCENT_ROLE_ID = 640481360766697482
TRUE_HUNDRED_PERCENT_ROLE_ID = 640481628292120576

# Lists for administration
STAFF_ROLE_ID = 450063890362138624
FAKE_ROLE_ID = 533826912712130580
STATIC_NICKNAME_ROLE_ID = 567259415393075210
CD_BOT_ROLE_ID = 543768819844251658
ADMIN_MENTOR_ROLE_ID = 502238208747110411
ROOT_ROLE_ID = int(environ.get("ROOT_MEMBERS_ID", "450113490590629888"))
SUDO_ROLE_ID = int(environ.get("SUDO_MEMBERS_ID", "450113682542952451"))
ADMIN_ROLES = ("Root", "Sudo")
BANNED_DOMAINS = ["discord.gg", "discord.com"]

HINTS_LIMIT = 8
CYBERDISC_ICON_URL = (
    "https://pbs.twimg.com/profile_images/921313066515615745/fLEl2Gfa_400x400.jpg"
)
ELITECOUNT_ENABLED = True

LOCAL_DEBUGGING = bool(environ.get("LOCAL_DEBUGGING", False))

# Readme command constants
README_SEND_ALIASES = ["create", "push", "generate", "send", "make", "build", "upload"]
README_RECV_ALIASES = ["fetch", "get", "pull", "download", "retrieve", "dm", "dl"]

# Readme auto update constants
README_CHANNEL_ID = int(environ.get("README_CHANNEL_ID", "409853512185282561"))
DEV_TESTING_CHANNEL_ID = int(environ.get("DEV_TESTING_CHANNEL_ID", "543766802174443531"))

END_README_MESSAGE = (
    "**Can't see any of the above?**\nIf you can't see any of the rich embeds above, try the"
    " following: `Settings -> Text & Images -> Link Preview (Show website preview info from"
    " links pasted into that chat)  -> ON`"
)

BASE_ALIASES = {
    "Headquarters": ["headquarters", "main", "hq", "h"],
    "Moonbase": ["moonbase", "python", "moon", "m"],
    "Forensics": ["forensics", "f"],
    "Volcano": ["volcano", "v", "volc"],
}

# Admin Constants
PLACEHOLDER_NICKNAME = "Valued server member"
NICKNAME_PATTERNS = [
    r"(discord\.gg/|discord\.com/invite/)",  # invite links
    r"(nigg|ligma|fag|nazi|hitler|\bpaki\b)",  # banned words
    r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)",  # hyperlinks
]

# Emoji Alphabet
EMOJI_LETTERS = [
    "\U0001f1e6\U0001f170\U0001F359",  # A
    "\U0001f1e7\U0001f171",  # B
    "\U0001f1e8\u262a\u00A9",  # C
    "\U0001f1e9\u21a9",  # D
    "\U0001f1ea\U0001f4e7",  # E
    "\U0001f1eb",  # F
    "\U0001f1ec\u26fd",  # G
    "\U0001f1ed\u2653",  # H
    "\U0001f1ee\u2139",  # I
    "\U0001f1ef\u2614",  # J
    "\U0001f1f0",  # K
    "\U0001f1f1\U0001f552\U0001F462",  # L
    "\U0001f1f2\u24c2\u24c2\u264f\u264d\u303d",  # M
    "\U0001f1f3\U0001f4c8\U0001F3B5",  # N
    "\U0001f1f4\U0001f17e\u2b55",  # O
    "\U0001f1f5\U0001f17f",  # P
    "\U0001f1f6",  # Q
    "\U0001f1f7",  # R
    "\U0001f1f8\U0001f4b0\u26a1\U0001F4B2",  # S
    "\U0001f1f9\u271d\U0001F334",  # T
    "\U0001f1fa\u26ce",  # U
    "\U0001f1fb\u2648",  # V
    "\U0001f1fc\u3030",  # W
    "\U0001f1fd\u274e\u274c\u2716",  # X
    "\U0001f1fe\U0001f331\u270C",  # Y
    "\U0001f1ff\U0001f4a4",  # Z
    "\u26ab\U0001f535\U0001f534\u26aa",  # Whitespace alternatives
    "\u2755\u2757\u2763",  # !
    "\u2754\u2753",  # ?
    "\U0001f4b2",  # $
    "\U000021aa",  # (
    "\U000021a9",  # )
]

CHEATING_VIDEO = "https://game.joincyberdiscovery.com/assets/videos/cheating_message.mp4?version=4.2.0"
