from pathlib import Path

from twisted.application.internet import TimerService
from twisted.internet import defer
from twisted.python import log
from buildbot.schedulers.base import ReconfigurableBaseScheduler


class IOS5Manual(ReconfigurableBaseScheduler):
    def checkConfig(self, builderNames, request_dir, repository, branch, **kwargs):
        super().checkConfig(builderNames=builderNames, **kwargs)

    @defer.inlineCallbacks
    def reconfigService(self, builderNames, request_dir, repository, branch, **kwargs):
        yield super().reconfigService(builderNames=builderNames, **kwargs)
        self.request_dir = Path(request_dir)
        self.request_dir.mkdir(parents=True, exist_ok=True)
        self.repository = repository
        self.branch = branch
        if not hasattr(self, 'poller'):
            self.poller = TimerService(5, self.poll)
            yield self.poller.setServiceParent(self)

    @defer.inlineCallbacks
    def poll(self):
        if not self.active:
            return
        for request in sorted(self.request_dir.glob('*.request')):
            try:
                yield self.addBuildsetForSourceStampsWithDefaults(
                    'Manual server request ' + request.stem,
                    [{'repository': self.repository, 'branch': self.branch, 'project': 'master', 'codebase': ''}],
                    False)
                request.unlink()
            except Exception:
                log.err()
                return
