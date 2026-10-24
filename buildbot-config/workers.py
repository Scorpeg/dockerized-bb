from buildbot.plugins import worker

buildbot_ip = '127.0.0.1'
workers = [worker.LocalWorker('builder-1', max_builds=1), worker.LocalWorker('fetcher', max_builds=1)]
workers_by_type = {'builder': ['builder-1'], 'fetcher': ['fetcher']}
