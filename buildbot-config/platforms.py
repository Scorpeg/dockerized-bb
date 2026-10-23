import copy

from buildbot.plugins import util

import config
import builds
import workers

def _getFromBuild(data, build):
    if not isinstance(data, dict):
        return data
    if len(data) == 0:
        return None
    if build.name in data:
        return data[build.name]
    for cls in type(build).mro():
        if cls in data:
            return data[cls]
    if None in data:
        return data[None]

def _buildInData(data, build):
    if data is None:
        return True
    if len(data) == 0:
        return False
    if build.name in data:
        return True
    for cls in type(build).mro():
        if cls in data:
            return True
    return False

class Platform:
    __slots__ = ['name',
            'compatibleBuilds', 'incompatibleBuilds',
            'env', 'buildenv',
            'configureargs', 'buildconfigureargs',
            'packageable', 'built_files', 'data_files',
            'packaging_cmd', 'strip_cmd', 'archiveext',
            'run_tests', 'build_devtools',
            'workerimage', 'lock_access',
            'icon', 'description_']

    def __init__(self, name):
        self.name = name
        self.compatibleBuilds = None
        # To blacklist stable ScummVM for example
        self.incompatibleBuilds = []
        self.env = copy.deepcopy(config.common_env)
        self.buildenv = {}
        self.configureargs = []
        self.buildconfigureargs = {}
        self.packageable = True
        self.built_files = []
        self.data_files = []
        self.packaging_cmd = None
        self.strip_cmd = None
        self.archiveext = "tar.xz"
        # Can run tests
        self.run_tests = False

        self.build_devtools = False

        self.workerimage = name
        # A callable taking the build object as argument and
        # which returns a LockAccess to be used when building platform
        self.lock_access = None

        # For daily builds list
        self.icon = None
        self.description_ = None

    @property
    def description(self):
        return self.description_ or self.name

    @description.setter
    def description(self, value):
        self.description_ = value

    def canBuild(self, build):
        return (_buildInData(self.compatibleBuilds, build) and
                not _buildInData(self.incompatibleBuilds, build))
    def getEnv(self, build):
        ret = dict(self.env)
        add = _getFromBuild(self.buildenv, build)
        if add is not None:
            ret.update(add)
        return ret
    def getConfigureArgs(self, build):
        ret = list(self.configureargs)
        add = _getFromBuild(self.buildconfigureargs, build)
        if add is not None:
            ret.extend(add)
        return ret
    def canPackage(self, build):
        return _getFromBuild(self.packageable, build)
    def getBuiltFiles(self, build):
        return _getFromBuild(self.built_files, build)
    def getDataFiles(self, build):
        return _getFromBuild(self.data_files, build)
    def getPackagingCmd(self, build):
        return _getFromBuild(self.packaging_cmd, build)
    def getStripCmd(self, build):
        return _getFromBuild(self.strip_cmd, build)
    def canRunTests(self, build):
        return _getFromBuild(self.run_tests, build)
    def getWorkerImage(self, build):
        return _getFromBuild(self.workerimage, build)

platforms = []
def register_platform(platform):
    if (config.platforms_whitelist and
            platform.name not in config.platforms_whitelist):
        return
    if (config.platforms_blacklist and
            platform.name in config.platforms_blacklist):
        return
    platforms.append(platform)

platform = Platform("ios5")
platform.compatibleBuilds = (builds.ScummVMBuild,)
platform.incompatibleBuilds = (builds.ScummVMStableBuild,)
platform.configureargs = [
    "--host=ios5", "--enable-all-engines", "--enable-detection-full", "--enable-static",
    "--with-staticlib-prefix=/opt/ios5/build-full/deps",
    "--enable-mt32emu", "--enable-fluidsynth", "--enable-png", "--enable-gif", "--enable-freetype2",
    "--disable-opengl-game-classic", "--disable-discord", "--disable-retrowave", "--disable-tts",
    "--disable-debug", "--disable-Werror", "--enable-release", "--enable-test-c++11"
]
platform.env.update({"FLUIDSYNTH_LIBS": "-lc++", "IOS5_REQUIRE_FULL": "1"})
platform.packaging_cmd = "ios5deb"
platform.built_files = ["scummvm-*-ios5*.deb"]
platform.archiveext = "zip"
platform.description = "iOS 5.1 / ARMv7"
platform.icon = "iphone"
register_platform(platform)
