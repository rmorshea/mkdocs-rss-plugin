#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
from email.utils import formatdate
from pathlib import Path

# 3rd party
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload.server import Server
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page
from mkdocs.utils import get_build_timestamp


# package modules
from .__about__ import __title__, __version__
from .customtypes import PageInformation
from .util import Util

# ############################################################################
# ########## Globals #############
# ################################

DEFAULT_TEMPLATE_FOLDER = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE_FILENAME = DEFAULT_TEMPLATE_FOLDER / "rss.xml.jinja2"


# ############################################################################
# ########## Classes ###############
# ##################################
class GitRssPlugin(BasePlugin):
    config_scheme = (
        ("abstract_chars_count", config_options.Type(int, default=150)),
        ("category", config_options.Type(str, default=None)),
        ("exclude_files", config_options.Type(list, default=[])),
        ("feed_ttl", config_options.Type(int, default=1440)),
        ("length", config_options.Type(int, default=20)),
        ("output_feed_filepath", config_options.Type(str, default="feed.xml")),
        ("template", config_options.Type(str, default=str(DEFAULT_TEMPLATE_FILENAME)),),
    )

    def __init__(self):
        self.pages_to_filter = []
        self.util = Util()

    def on_config(self, config: config_options.Config) -> dict:
        """

        The config event is the first event called on build and
        is run immediately after the user configuration is loaded and validated.
        Any alterations to the config should be made here.
        https://www.mkdocs.org/user-guide/plugins/#on_config

        Args:
            config (dict): global configuration object

        Returns:
            dict: global configuration object
        """
        # check template dirs
        if not Path(self.config.get("template")).is_file():
            raise FileExistsError(self.config.get("template"))
        self.tpl_file = Path(self.config.get("template"))
        self.tpl_folder = Path(self.config.get("template")).parent

        # start a feed dictionary using global config vars
        self.feed = {
            "author": config.get("site_author", None),
            "buildDate": formatdate(get_build_timestamp()),
            "copyright": config.get("copyright", None),
            "description": config.get("site_description", None),
            "generator": "{} - v{}".format(__title__, __version__),
            "html_url": config.get("site_url", None),
            "repo_url": config.get("repo_url", config.get("site_url", None)),
            "title": config.get("site_name", None),
            "ttl": self.config.get("feed_ttl", None),
        }

        # final feed url
        if config.get("site_url"):
            self.feed["rss_url"] = "{}/{}".format(
                config.get("site_url"), self.config.get("output_feed_filepath")
            )

        # ending event
        return config

    def on_page_markdown(
        self, markdown: str, page: Page, config: config_options.Config, files
    ) -> str:
        """The page_markdown event is called after the page's markdown is loaded
        from file and can be used to alter the Markdown source text.
        The meta- data has been stripped off and is available as page.meta
        at this point.

        https://www.mkdocs.org/user-guide/plugins/#on_page_markdown

        Args:
            markdown (str): Markdown source text of page as string
            page: mkdocs.nav.Page instance
            config: global configuration object
            site_navigation: global navigation object

        Returns:
            str: Markdown source text of page as string
        """
        # retrieve dates from git log
        page_dates = self.util.get_file_dates(
            path=page.file.abs_src_path, fallback_to_build_date=1,
        )

        # append to list to be filtered later
        self.pages_to_filter.append(
            PageInformation(
                abs_path=Path(page.file.abs_src_path),
                created=page_dates[0],
                updated=page_dates[1],
                title=page.title,
                description=self.util.get_description_or_abstract(
                    in_page=page, chars_count=self.config.get("abstract_chars_count")
                ),
                url_full=page.canonical_url,
            )
        )
        # print(self.util.get_description_or_abstract(page))

    def on_post_build(self, config: config_options.Config) -> dict:
        """The post_build event does not alter any variables. \
        Use this event to call post-build scripts. \
        See: <https://www.mkdocs.org/user-guide/plugins/#on_post_build>

        Args:
            config (dict): global configuration object

        Returns:
            dict: global configuration object
        """
        # load Jinja environment
        env = Environment(
            loader=FileSystemLoader(self.tpl_folder),
            autoescape=select_autoescape(["xml"]),
        )

        template = env.get_template(self.tpl_file.name)

        # items
        self.feed["entries"] = [
            {"title": "hahaha", "description": "youplouboum"},
            {"title": "OIHOHOIHO", "description": "&é('(é'"},
        ]

        # write feed to file
        with open(
            self.config.get("output_feed_filepath"), mode="w", encoding="UTF8"
        ) as fh:
            fh.write(template.render(feed=self.feed))

    def on_serve(self, server: Server, config: config_options.Config, builder):
        pass
