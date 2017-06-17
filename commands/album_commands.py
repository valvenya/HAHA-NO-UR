from os import remove
from discord.ext import commands
from bot import HahaNoUR
import math
from time import clock
from random import randint
from get_names import get_idol_names
from argument_parser import parse_arguments
from image_generator import create_image
from discord import User

PAGE_SIZE = 12
IDOL_NAMES = get_idol_names()
SORTS = ["id", "name", "attribute", "rarity"]
RARITIES = ["UR", "SSR", "SR", "R", "N"]
ATRIBUTES = ["Smile", "Pure", "Cool"]

# Dictionary mapping user ids to last used album arguments
_last_user_args = {}


class AlbumCommands:
    """
    A class to hold all album commands.
    """

    def __init__(self, bot: HahaNoUR):
        self.bot = bot

    async def __send_error_msg(self, ctx):
        await self.bot.send_message(
            ctx.message.channel,
            '<@' + ctx.message.author.id + '> A transmission error occured.')

    async def __handle_result(self, ctx, album_size, image_path, delete=True):
        if not image_path:
            await self.__send_error_msg(ctx)
        else:
            page = _last_user_args[ctx.message.author.id]["page"]
            max_page = int(math.ceil(album_size / PAGE_SIZE))
            msg = '<@' + ctx.message.author.id + '> '
            msg += "Page " + str(page + 1) + " of " + str(max_page)
            msg += "\nALBUMS WILL BE RESET ON 18-JUN-2017 AT 9PM EDT"
            msg += " WHEN THE FEATURE GOES LIVE."
            await self.bot.upload(
                image_path, content=msg)

            if delete:
                remove(image_path)

    @commands.command(pass_context=True)
    @commands.cooldown(rate=3, per=2.5, type=commands.BucketType.user)
    async def album(self, ctx, *args: str):
        user = ctx.message.author
        album = self.bot.db.get_user_album(user)
        _parse_album_arguments(args, user)
        album = _apply_filter(album, user)
        album = _apply_sort(album, user)
        album_size = len(album)
        album = _splice_page(album, user)

        urls = []
        for card in album:
            if card["round_card_image"] is None:
                urls.append("http:" + card["round_card_idolized_image"])
            else:
                urls.append("http:" + card["round_card_image"])

        # TODO change this to call newer version of function that makes labels.
        if len(urls) > 0:
            image_path = await create_image(
                    urls, 2, str(clock()) + str(randint(0, 100)) + ".png")
        else:
            image_path = None

        await self.__handle_result(ctx, album_size, image_path)

def _apply_filter(album: list, user: User):
    """
    Applys a user's filters to a card album, removing anything not matching
        the filter.

    :param album: Album being filtered.
    :param user: User who requested the album.

    :return: Filtered album.
    """
    filters = _last_user_args[user.id]["filters"]

    for filt in filters:
        filter_type = filt[0]
        filter_values = filt[1]

        # Looping backwards since we are removing elements
        for i in range(len(album) - 1, -1, -1):
            for filter_value in filter_values:
                if album[i][filter_type] != filter_value:
                    album.pop(i)

    return album


def _apply_sort(album: list, user: User) -> list:
    """
    Applys a user's sort to a card album.

    :param album: Album being sorted.
    :param user: User who requested the album.

    :return: Sorted album.
    """
    sort = _last_user_args[user.id]["sort"]

    if sort == "rarity":
        album.sort(key=lambda x: RARITIES.index(x["rarity"]))
    elif sort == "attribute":
        album.sort(key=lambda x: ATRIBUTES.index(x["attribute"]))
    elif sort == "name":
        album.sort(key=lambda x: k["name"])

    return album


def _splice_page(album: list, user: User) -> list:
    """
    Splices a user's last requested page out of their album.

    :param album: Album being spliced
    :param user: User who requested the album.

    :return: Spliced album.
    """
    page = _last_user_args[user.id]["page"]
    max_page = int(math.ceil(len(album) / PAGE_SIZE)) - 1

    if page > max_page:
        page = max_page
    if page < 0:
        page = 0
    _last_user_args[user.id]["page"] = page

    start = PAGE_SIZE * page
    end = (PAGE_SIZE * page) + PAGE_SIZE
    return album[start:end]


def _parse_album_arguments(args: tuple, user: User):
    """
    Parse arguments to get how an album will be sorted and filtered. The parsed
        arguments are stored in the user's last used arguments dictionary.

    :param args: Tuple of arguments.
    :param user: User who requested the album.
    """
    # Add user to last used argument dictionary if they don't already exist.
    if not user.id in _last_user_args:
        _last_user_args[user.id] = {
            "page": 0,
            "filters": [], # Filter "all" if []
            "sort": None # Sort by ID if None
        }

    # Get values of user's last album preview.
    page = _last_user_args[user.id]["page"]
    filters = _last_user_args[user.id]["filters"]
    sort = _last_user_args[user.id]["sort"]

    # Parse other arguments
    for arg in args:
        arg = arg.lower()

        # Reset filter if "all" is given
        if arg == "all":
            filters = []

        # Parse sort
        if arg in SORTS:
            _last_user_args[user.id]["sort"] = arg

        _last_user_args[user.id]["page"] = page
        _last_user_args[user.id]["filters"] = filters
        _last_user_args[user.id]["sort"] = sort


def _is_number(string: str) -> bool:
    """
    Checks if a string is a valid number.

    :param string: String being tested.

    :return: True if valid number, otherwise false.
    """
    try:
        int(string)
        return True
    except ValueError:
        return False
