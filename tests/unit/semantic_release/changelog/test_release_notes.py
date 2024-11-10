from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# NOTE: use backport with newer API to support 3.7
from importlib_resources import files

import semantic_release
from semantic_release.cli.changelog_writer import generate_release_notes
from semantic_release.commit_parser.token import ParsedCommit
from semantic_release.hvcs import Bitbucket, Gitea, Github, Gitlab

from tests.const import TODAY_DATE_STR

if TYPE_CHECKING:
    from semantic_release.changelog.release_history import ReleaseHistory


@pytest.fixture(scope="module")
def release_notes_template() -> str:
    """Retrieve the semantic-release default release notes template."""
    version_notes_template = files(semantic_release.__name__).joinpath(
        Path("data", "templates", "angular", "md", ".release_notes.md.j2")
    )
    return version_notes_template.read_text(encoding="utf-8")


@pytest.mark.parametrize("hvcs_client", [Github, Gitlab, Gitea, Bitbucket])
def test_default_release_notes_template(
    example_git_https_url: str,
    hvcs_client: type[Github | Gitlab | Gitea | Bitbucket],
    artificial_release_history: ReleaseHistory,
):
    """
    Unit test goal: just make sure it renders the release notes template without error.

    Scenarios are better suited for all the variations (commit types).
    """
    version = next(iter(artificial_release_history.released.keys()))
    hvcs = hvcs_client(example_git_https_url)
    release = artificial_release_history.released[version]

    feat_commit_obj = release["elements"]["feature"][0]
    fix_commit_obj = release["elements"]["fix"][0]
    assert isinstance(feat_commit_obj, ParsedCommit)
    assert isinstance(fix_commit_obj, ParsedCommit)

    feat_commit_url = hvcs.commit_hash_url(feat_commit_obj.commit.hexsha)
    feat_description = str.join("\n", feat_commit_obj.descriptions)

    fix_commit_url = hvcs.commit_hash_url(fix_commit_obj.commit.hexsha)
    fix_description = str.join("\n", fix_commit_obj.descriptions)

    expected_content = str.join(
        os.linesep,
        [
            f"## v{version} ({TODAY_DATE_STR})",
            "",
            "### Feature",
            "",
            "- {commit_scope}{commit_desc} ([`{short_hash}`]({url}))".format(
                commit_scope=(
                    f"**{feat_commit_obj.scope}**: " if feat_commit_obj.scope else ""
                ),
                commit_desc=feat_description.capitalize(),
                short_hash=feat_commit_obj.commit.hexsha[:7],
                url=feat_commit_url,
            ),
            "",
            "### Fix",
            "",
            "- {commit_scope}{commit_desc} ([`{short_hash}`]({url}))".format(
                commit_scope=(
                    f"**{fix_commit_obj.scope}**: " if fix_commit_obj.scope else ""
                ),
                commit_desc=fix_description.capitalize(),
                short_hash=fix_commit_obj.commit.hexsha[:7],
                url=fix_commit_url,
            ),
            "",
        ],
    )

    actual_content = generate_release_notes(
        hvcs_client=hvcs_client(remote_url=example_git_https_url),
        release=release,
        template_dir=Path(""),
        history=artificial_release_history,
        style="angular",
    )

    assert expected_content == actual_content


@pytest.mark.parametrize("hvcs_client", [Github, Gitlab, Gitea, Bitbucket])
def test_default_release_notes_template_first_release(
    example_git_https_url: str,
    hvcs_client: type[Bitbucket | Gitea | Github | Gitlab],
    single_release_history: ReleaseHistory,
):
    """
    Unit test goal: just make sure it renders the release notes template without error.

    Scenarios are better suited for all the variations (commit types).
    """
    hvcs = hvcs_client(example_git_https_url)
    version = list(single_release_history.released.keys())[-1]
    release = single_release_history.released[version]

    expected_content = str.join(
        os.linesep,
        [
            f"## v{version} ({TODAY_DATE_STR})",
            "",
            "- Initial Release",
            "",
        ],
    )

    actual_content = generate_release_notes(
        hvcs_client=hvcs,
        release=release,
        template_dir=Path(""),
        history=single_release_history,
        style="angular",
    )

    assert expected_content == actual_content
