import base64
import dataclasses
import io
import os
import sys
import typing as t
import warnings

import docspec
import requests
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer
from pydoc_markdown.interfaces import Context, Renderer

README_FRONTMATTER = """---
title: {title}
excerpt: {excerpt}
category: {category}
slug: {slug}
order: {order}
hidden: false
---

"""


@dataclasses.dataclass
class ReadmeRenderer(Renderer):
    """
    This custom Renderer is heavily based on the `MarkdownRenderer`,
    it just prepends a front matter so that the output can be published
    directly to readme.io.
    """

    # These settings will be used in the front matter output
    title: str
    category_slug: str
    excerpt: str
    slug: str
    order: int
    # Docs categories fetched from Readme.io
    categories: t.Dict[str, str] = dataclasses.field(init=False)
    # This exposes a special `markdown` settings value that can be used to pass
    # parameters to the underlying `MarkdownRenderer`
    markdown: MarkdownRenderer = dataclasses.field(default_factory=MarkdownRenderer)

    def init(self, context: Context) -> None:
        self.markdown.init(context)
        version = self._doc_version()
        self.categories = self._readme_categories(version)

    def _doc_version(self) -> str:
        """
        Returns the docs version.
        """
        # full_version = about.__version__
        # major, minor = full_version.split(".")[:2]
        # return f"v{major}.{minor}"

        # The readme.io version is hardcoded for now to manually maintain the guides
        # within the same documentation page as the deepset Cloud Docs.
        return "v1.0"

    def _readme_categories(self, version: str) -> t.Dict[str, str]:
        """
        Fetch the categories of the given version from Readme.io.
        README_API_KEY env var must be set to correctly get the categories.
        Returns dictionary containing all the categories slugs and their ids.
        """
        README_API_KEY = os.getenv("README_API_KEY")
        if not README_API_KEY:
            warnings.warn("README_API_KEY env var is not set, using a placeholder category ID")
            return {"open-source-sdk-methods": "ID"}

        token = base64.b64encode(f"{README_API_KEY}:".encode()).decode()
        headers = {"authorization": f"Basic {token}", "x-readme-version": version}

        page = 1
        results = {}

        while True:
            res = requests.get(
                "https://dash.readme.com/api/v1/categories", params={"page": page}, headers=headers, timeout=60
            )
            if not res.ok:
                sys.exit("Error requesting categories")

            data = res.json()
            if not data:
                break

            results.update({c["slug"]: c["id"] for c in data})
            page += 1

        return results

    def render(self, modules: t.List[docspec.Module]) -> None:
        if self.markdown.filename is None:
            sys.stdout.write(self._frontmatter())
            self.markdown.render_single_page(sys.stdout, modules)
        else:
            with io.open(self.markdown.filename, "w", encoding=self.markdown.encoding) as fp:
                fp.write(self._frontmatter())
                self.markdown.render_single_page(t.cast(t.TextIO, fp), modules)

    def _frontmatter(self) -> str:
        return README_FRONTMATTER.format(
            title=self.title,
            category=self.categories[self.category_slug],
            excerpt=self.excerpt,
            slug=self.slug,
            order=self.order,
        )
