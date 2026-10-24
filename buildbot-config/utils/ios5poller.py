from twisted.internet import defer
from buildbot.changes.gitpoller import GitPoller


class IOS5GitPoller(GitPoller):
    @defer.inlineCallbacks
    def _process_changes(self, newRev, branch):
        if self.lastRev:
            yield super()._process_changes(newRev, branch)
            return
        timestamp = yield self._get_commit_timestamp(newRev)
        author = yield self._get_commit_author(newRev)
        committer = yield self._get_commit_committer(newRev)
        files = yield self._get_commit_files(newRev)
        comments = yield self._get_commit_comments(newRev)
        yield self.master.data.updates.addChange(
            author=author, committer=committer, revision=newRev.strip(),
            files=files, comments=comments, when_timestamp=timestamp,
            branch=self._removeHeads(branch), project=self.project,
            repository=self.repourl, category=self.category, src='git',
        )
