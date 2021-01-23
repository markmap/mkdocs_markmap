import os
import sys
from pathlib import Path
from pprint import pprint
from typing import Dict, List

from github.GitRelease import GitRelease
from github.GitReleaseAsset import GitReleaseAsset

from .common import AssetCollector, ChangelogLoader, GithubHandler, PROJECT_PATH


GITHUB_TOKEN: str = os.environ['GITHUB_TOKEN']

MASTER_BRANCH = 'master'



class ReleaseHandler(GithubHandler):
    def __init__(self, tag: str) -> None:
        super(ReleaseHandler, self).__init__(tag)
        self._changelog = ChangelogLoader()
        self._collector = AssetCollector()

    def create(self, commit: str = None,dry_run: bool = True):
        assets: List[str] = self._collector.get_assets()

        if commit is None:
            commit = self.repository.get_branch(MASTER_BRANCH).commit.sha

        parameters: Dict[str, str] = {
            'object': commit,
            'release_name': self.tag,
            'release_message': self._changelog.get(self.tag),
            'tag': self.tag,
            'tag_message': f'Release version {self.tag}',
            'tagger': self.repository.owner,
            'type': 'commit',
        }

        try:
            assert self.tag not in (tag.name for tag in self.repository.get_tags()), \
                f'tag "{self.tag}" already exists'
            assert self.tag not in (release.tag_name for release in self.repository.get_releases()), \
                f'release "{self.tag}" already exists'

        except AssertionError as e:
            print(e)
            sys.exit(1)

        if dry_run:
            print('This is a dry run!')
            pprint(parameters, width=120)
        
        else:
            release: GitRelease = self.repository.create_git_tag_and_release(**parameters)
            print(f'Release "{self.tag}" created: {release.html_url}')
            for asset in assets:
                release_asset: GitReleaseAsset = release.upload_asset(asset)
                print(f'Release asset "{release_asset.name}" uploaded: {release_asset.url}')

    def delete(self):
        try:
            next(t for t in self.repository.get_tags() if t.name == self.tag)

        except StopIteration:
            print(f'Tag "{self.tag}" does not exist')

        else:
            print(list(self.repository.get_git_refs()))
            self.repository.get_git_ref(f'tags/{self.tag}').delete()
            print(f'Tag "{self.tag}" deleted')

        try:
            release: GitRelease = next(r for r in self.repository.get_releases() if r.tag_name == self.tag)

        except StopIteration:
            print(f'Release "{self.tag}" does not exist')

        else:
            release.delete_release()
            print(f'Release "{self.tag}" deleted')
