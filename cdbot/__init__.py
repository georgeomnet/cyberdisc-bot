"""Initialise cdbot as a package for poetry."""
from git import Repo

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from .bot import bot
from .constants import BOT_TOKEN, SENTRY_URL


def main():
    """Entry point for poetry script."""
    sentry_sdk.init(
        SENTRY_URL,
        release=Repo().head.object.hexsha,
        integrations=[AioHttpIntegration()],
    )
    bot.run(BOT_TOKEN)
