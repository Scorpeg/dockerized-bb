#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile

root=Path(__file__).resolve().parents[1]
archives=root/'vendor/full-archives'
bb=root/'vendor/buildbot-recipes'
lock=json.loads((root/'full-dependencies.lock.json').read_text())
for name,digest in lock['buildbot']['recipe_sha256'].items():
    assert hashlib.sha256((bb/name).read_bytes()).hexdigest()==digest,name
for name,digest in lock['sha256'].items():
    assert hashlib.sha256((archives/name).read_bytes()).hexdigest()==digest,name
work=root/'build-full/deps-work'
prefix=root/'build-full/deps'
logs=root/'logs/full'
for path in [work,prefix/'lib',prefix/'include',logs]: path.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
env.update(CFLAGS='-O2 -fPIC -miphoneos-version-min=5.1', CXXFLAGS='-O2 -fPIC -miphoneos-version-min=5.1', CPPFLAGS='-I'+str(prefix/'include'), LDFLAGS='-L'+str(prefix/'lib'), PKG_CONFIG_LIBDIR=str(prefix/'lib/pkgconfig'), PKG_CONFIG_PATH='', CC_FOR_BUILD='/usr/bin/gcc', CXX_FOR_BUILD='/usr/bin/g++')
env['PATH']=str(prefix/'bin')+':'+env['PATH']
jobs=os.environ.get('JOBS','3')
packages=['zlib','bzip2','libjpeg-turbo','faad2','libmad','libogg','libtheora','libvorbis','flac','libmikmod','mpeg2dec','a52dec','libmpc','libvpx','openssl','curl','fribidi','libsdl2-net','fluidsynth']
for name in sys.argv[1:] or packages:
    marker=work/(name+'.done')
    if marker.exists():
        print('CACHED',name,flush=True)
        continue
    print('BUILD',name,flush=True)
    source=work/name
    with (logs/(name+'.log')).open('w') as log:
        def run(args,cwd=source,extra=None):
            print('+ '+' '.join(map(str,args)),file=log,flush=True)
            try:
                subprocess.run(list(map(str,args)),cwd=cwd,env=env if extra is None else dict(env,**extra),stdout=log,stderr=subprocess.STDOUT,check=True)
            except subprocess.CalledProcessError:
                print('FAIL dependency '+name+': '+str(logs/(name+'.log')),file=sys.stderr,flush=True)
                print('\n'.join((logs/(name+'.log')).read_text(errors='replace').splitlines()[-40:]),file=sys.stderr,flush=True)
                raise
        if not source.exists():
            if name in ('fluidsynth','libtheora','openssl','curl'):
                archive=archives/({'fluidsynth':'fluidsynth-2.6.1.tar.gz','libtheora':'theora-28fd5ec77f0ad0e07a371cef1047828116f6bd8a.tar.gz'}.get(name) or lock['extra'][name]['archive'])
                with tarfile.open(archive) as tar:
                    for m in tar.getmembers():
                        m.name='/'.join(m.name.split('/')[1:])
                        if m.name: tar.extract(m,source)
            else:
                run(['dpkg-source','--no-check','-x',archives/lock['packages'][name]['dsc'],source],cwd=work)
            if name=='openssl':
                patch=root/'packaging/dependency-patches/openssl-ios5-atomics.patch'
                assert hashlib.sha256(patch.read_bytes()).hexdigest()==lock['local_patch_sha256'][str(patch.relative_to(root))]
                run(['patch','--batch','-p1','-i',patch])
            patchname={'libmpc':'libmpcdec','curl':'curl-new'}.get(name,name)
            for base in ['common','apple-common']:
                for patch in sorted((bb/'toolchains'/base/'packages'/patchname/'patches').glob('*.patch')):
                    run(['patch','--batch','-p1','-i',patch])
        def configure(*args):
            run([source/'configure','--host=arm-apple-darwin11',*(['--build=x86_64-linux-gnu'] if name != 'libvpx' else []),'--prefix='+str(prefix),'--disable-shared','--enable-static',*args])
        def make(*args): run(['make','-j'+jobs,*args])
        def cmake(*args):
            run(['cmake','--fresh','-S',source,'-B',source/'_build','-DCMAKE_SYSTEM_NAME=Darwin','-DCMAKE_SYSTEM_PROCESSOR=armv7','-DCMAKE_OSX_ARCHITECTURES=armv7','-DCMAKE_OSX_SYSROOT='+env['IOS_SDK_ROOT'],'-DCMAKE_C_COMPILER='+env['CC'],'-DCMAKE_CXX_COMPILER='+env['CXX'],'-DCMAKE_AR='+env['AR'],'-DCMAKE_RANLIB='+env['RANLIB'],'-DCMAKE_INSTALL_PREFIX='+str(prefix),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF',*args])
            run(['cmake','--build',source/'_build','-j',jobs])
            run(['cmake','--install',source/'_build'])
        if name=='zlib':
            run([source/'configure','--prefix='+str(prefix),'--static'])
            make(); make('install')
        elif name=='openssl':
            run(['perl',source/'Configure','--config='+str(root/'scripts/openssl_full.conf'),'ios5','no-shared','no-tests','no-apps','no-dso','no-module','no-asm','no-engine','no-ui-console','no-legacy','no-quic','no-afalgeng','--with-rand-seed=devrandom','--prefix='+str(prefix),'--openssldir='+str(prefix/'ssl')])
            make(); make('install_sw')
        elif name=='bzip2':
            make('libbz2.a','CC='+env['CC'],'AR='+env['AR'],'RANLIB='+env['RANLIB'],'CFLAGS=-O2 -fPIC')
            shutil.copy2(source/'libbz2.a',prefix/'lib'); shutil.copy2(source/'bzlib.h',prefix/'include')
        elif name=='libjpeg-turbo':
            cmake('-DENABLE_SHARED=OFF','-DWITH_TURBOJPEG=OFF','-DWITH_SIMD=OFF')
        elif name=='faad2':
            cmake('-DFAAD_BUILD_CLI=OFF')
        elif name=='fluidsynth':
            cmake_source=source/'CMakeLists.txt'
            cmake_source.write_text(cmake_source.read_text().replace('set(CMAKE_CXX_STANDARD 11)', 'set(CMAKE_CXX_STANDARD 17)'))
            with zipfile.ZipFile(archives/lock['extra']['gcem']['archive']) as z:
                for item in z.infolist():
                    rel='/'.join(item.filename.split('/')[1:])
                    if rel and not item.is_dir():
                        target=source/'gcem'/rel
                        target.parent.mkdir(parents=True,exist_ok=True)
                        target.write_bytes(z.read(item))
            disabled='alsa aufile dbus jack ladspa libinstpatch libsndfile midishare opensles oboe network oss dsound wasapi waveout winmidi sdl3 pulseaudio pipewire readline threads openmp systemd coreaudio coremidi framework native-dls'.split()
            cmake('-Dosal=embedded','-DLIB_SUFFIX=','-DCMAKE_CXX_COMPILER='+str(root/'scripts/cxx_constexpr'),*['-Denable-'+x+'=OFF' for x in disabled])
        else:
            if name=='libmad':
                assert (source/'.pc/applied-patches').exists(), 'Debian libmad patches were not applied'
                for f in ['NEWS','AUTHORS','ChangeLog']: (source/f).touch()
            if name=='libvorbis':
                p=source/'configure.ac'; p.write_text(p.read_text().replace('-mno-ieee-fp',''))
            if name=='libvpx':
                env['LD']=env['CC']
                configure('--target=armv7-darwin-gcc','--disable-neon-asm','--disable-examples','--disable-tools','--disable-docs','--disable-unit-tests','--disable-install-bins','--disable-install-srcs','--size-limit=16384x16384','--disable-vp8-encoder','--disable-vp9-encoder')
                make(); make('install')
                env.pop('LD',None)
            else:
                if name=='fribidi':
                    run(['./autogen.sh'],extra={'NOCONFIGURE':'1'})
                else: run(['autoreconf','-fi'])
                args={
                    'libmad':['ac_cv_func_fork=no','--enable-fpm=arm'],
                    'libtheora':['--disable-examples','--disable-spec','--disable-doc','--disable-asm'],
                    'flac':['--disable-doxygen-docs','--disable-xmms-plugin','--disable-cpplibs','--disable-ogg','--disable-programs','--disable-examples'],
                    'libmikmod':['--disable-doc','--disable-alldrv','--disable-threads','--disable-dl'],
                    'curl':['--with-openssl='+str(prefix),'--with-ca-bundle=/Applications/ScummVM-iOS5.app/cacert.pem','--without-ca-path','--without-nghttp3','--without-ngtcp2','--without-libpsl','--without-libidn2','--without-libssh2','--without-nghttp2','--without-brotli','--without-zstd','--disable-ldap','--disable-ldaps','--disable-threaded-resolver'],
                    'libsdl2-net':['--disable-examples'],
                }.get(name,[])
                configure(*args)
                subdirs={'flac':['src/libFLAC','include'],'mpeg2dec':['libmpeg2','include'],'a52dec':['liba52','include'],'libmpc':['include','libmpcdec'],'curl':['lib','include']}.get(name)
                if subdirs:
                    for d in subdirs:
                        make('-C',d); make('-C',d,'install')
                    if name=='curl': make('install-pkgconfigDATA','install-binSCRIPTS')
                else:
                    make(); make('install')
        marker.write_text(json.dumps({'source':(lock['extra']['theora'] if name=='libtheora' else lock['extra'].get(name,lock['packages'].get(name))), 'buildbot':lock['buildbot']['revision']})+'\n')
    print('PASS',name,flush=True)
