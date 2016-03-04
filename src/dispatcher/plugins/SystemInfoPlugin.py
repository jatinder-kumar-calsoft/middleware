#+
# Copyright 2014 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
#####################################################################

import sys
import errno
import os
import psutil
import re
import netif
import bsd
import logging
import time

from threading import Event, Thread
from bsd import devinfo
from datastore import DatastoreException
from datetime import datetime
from dateutil import tz, parser
from freenas.dispatcher.rpc import (
    RpcException,
    SchemaHelper as h,
    accepts,
    description,
    returns,
    private
)
from lib.system import SubprocessException, system
from lib.freebsd import get_sysctl
from task import Provider, Task, TaskException, TaskAbortException

if '/usr/local/lib' not in sys.path:
    sys.path.append('/usr/local/lib')
from freenasOS import Configuration

KEYMAPS_INDEX = "/usr/share/syscons/keymaps/INDEX.keymaps"
ZONEINFO_DIR = "/usr/share/zoneinfo"
VERSION_FILE = "/etc/version"
logger = logging.getLogger('SystemInfoPlugin')


@description("Provides informations about the running system")
class SystemInfoProvider(Provider):
    def __init__(self):
        self.__version = None

    @accepts()
    @returns(h.array(str))
    def uname_full(self):
        return os.uname()

    @accepts()
    @returns(str)
    @description("Return the full version string, e.g. FreeNAS-8.1-r7794-amd64.")
    def version(self):
        if self.__version is None:
            # See #9113
            conf = Configuration.Configuration()
            manifest = conf.SystemManifest()
            if manifest:
                self.__version = manifest.Version()
            else:
                with open(VERSION_FILE) as fd:
                    self.__version = fd.read().strip()

        return self.__version

    @accepts()
    @returns({'type': 'array', 'items': {'type': 'number'}, 'maxItems': 3, 'minItems': 3})
    def load_avg(self):
        return list(os.getloadavg())

    @accepts()
    @returns(h.object(properties={
        'cpu_model': str,
        'cpu_cores': int,
        'cpu_clockrate': int,
        'memory_size': int,
    }))
    def hardware(self):
        return {
            'cpu_model': get_sysctl("hw.model"),
            'cpu_cores': get_sysctl("hw.ncpu"),
            'cpu_clockrate': get_sysctl("hw.clockrate"),
            'memory_size': get_sysctl("hw.physmem")
        }

    @accepts()
    @returns(h.ref('system-time'))
    def time(self):
        boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=tz.tzlocal())
        return {
            'system_time': datetime.now(tz=tz.tzlocal()).isoformat(),
            'boot_time': boot_time.isoformat(),
            'uptime': (datetime.now(tz=tz.tzlocal()) - boot_time).total_seconds(),
            'timezone': time.tzname[time.daylight],
        }


@description("Provides informations about general system settings")
class SystemGeneralProvider(Provider):

    @accepts()
    @returns(h.ref('system-general'))
    def get_config(self):
        return {
            'hostname': self.configstore.get('system.hostname'),
            'language': self.configstore.get('system.language'),
            'timezone': self.configstore.get('system.timezone'),
            'syslog_server': self.configstore.get('system.syslog_server'),
            'console_keymap': self.configstore.get('system.console.keymap')
        }

    @accepts()
    @returns(h.array(h.array(str)))
    def keymaps(self):
        if not os.path.exists(KEYMAPS_INDEX):
            return []

        rv = []
        with open(KEYMAPS_INDEX, 'r', encoding='utf-8', errors='ignore') as f:
            d = f.read()
        fnd = re.findall(r'^(?P<name>[^#\s]+?)\.kbd:en:(?P<desc>.+)$', d, re.M)
        for name, desc in fnd:
            rv.append((name, desc))
        return rv

    @accepts()
    @returns(h.array(str))
    def timezones(self):
        result = []
        for root, _, files in os.walk(ZONEINFO_DIR):
            for f in files:
                if f in ('zone.tab', 'posixrules'):
                    continue

                result.append(os.path.join(root, f).replace(ZONEINFO_DIR + '/', ''))

        return sorted(result)

    @private
    @accepts(str)
    @returns(str)
    def cowsay(self, line):
        return system('/usr/local/bin/cowsay', '-s', line)


@description("Provides informations about advanced system settings")
class SystemAdvancedProvider(Provider):

    @accepts()
    @returns(h.ref('system-advanced'))
    def get_config(self):
        cs = self.configstore
        return {
            'console_cli': cs.get('system.console.cli'),
            'console_screensaver': cs.get('system.console.screensaver'),
            'serial_console': cs.get('system.serial.console'),
            'serial_port': cs.get('system.serial.port'),
            'serial_speed': cs.get('system.serial.speed'),
            'powerd': cs.get('service.powerd.enable'),
            'swapondrive': cs.get('system.swapondrive'),
            'debugkernel': cs.get('system.debug.kernel'),
            'uploadcrash': cs.get('system.upload_crash'),
            'motd': cs.get('system.motd'),
            'boot_scrub_internal': cs.get('system.boot_scrub_internal'),
            'periodic_notify_user': cs.get('system.periodic.notify_user'),
        }

    @description('Returns array of serial port address')
    @accepts()
    @returns(h.array(str))
    def serial_ports(self):
        ports = []
        for devices in list(devinfo.DevInfo().resource_managers['I/O ports'].values()):
            for dev in devices:
                if not dev.name.startswith('uart'):
                    continue
                ports.append(hex(int(dev.start)))
        return ports


@description("Provides informations about UI system settings")
class SystemUIProvider(Provider):

    @accepts()
    @returns(h.ref('system-ui'))
    def get_config(self):

        protocol = []
        if self.configstore.get('service.nginx.http.enable'):
            protocol.append('HTTP')
        if self.configstore.get('service.nginx.https.enable'):
            protocol.append('HTTPS')

        return {
            'webui_protocol': protocol,
            'webui_listen': self.configstore.get(
                'service.nginx.listen',
            ),
            'webui_http_port': self.configstore.get(
                'service.nginx.http.port',
            ),
            'webui_http_redirect_https': self.configstore.get(
                'service.nginx.http.redirect_https',
            ),
            'webui_https_certificate': self.configstore.get(
                'service.nginx.https.certificate',
            ),
            'webui_https_port': self.configstore.get(
                'service.nginx.https.port',
            ),
        }


@description("Configures general system settings")
@accepts(h.ref('system-general'))
class SystemGeneralConfigureTask(Task):
    def describe(self, props):
        return "System General Settings Configure"

    def verify(self, props):
        return ['system']

    def run(self, props):
        if 'hostname' in props:
            netif.set_hostname(props['hostname'])

        if 'language' in props:
            self.configstore.set('system.language', props['language'])

        if 'timezone' in props:
            self.configstore.set('system.timezone', props['timezone'])
            os.putenv('TZ', props['timezone'])

        if 'console_keymap' in props:
            self.configstore.set(
                'system.console.keymap',
                props['console_keymap'],
            )

        syslog_changed = False
        if 'syslog_server' in props:
            self.configstore.set('system.syslog_server', props['syslog_server'])
            syslog_changed = True

        try:
            self.dispatcher.call_sync('etcd.generation.generate_group', 'localtime')
            if syslog_changed:
                self.dispatcher.call_sync('etcd.generation.generate_group', 'syslog')
                self.dispatcher.call_sync('service.reload', 'syslog')
        except RpcException as e:
            raise TaskException(
                errno.ENXIO,
                'Cannot reconfigure system: {0}'.format(str(e),)
            )

        self.dispatcher.dispatch_event('system.general.changed', {
            'operation': 'update',
        })


@description("Configures advanced system settings")
@accepts(h.ref('system-advanced'))
class SystemAdvancedConfigureTask(Task):

    def describe(self, props):
        return "System Advanced Settings Configure"

    def verify(self, props):
        return ['system']

    def run(self, props):
        try:
            cs = self.configstore

            console = False
            loader = False
            rc = False

            if 'console_cli' in props:
                cs.set('system.console.cli', props['console_cli'])
                console = True

            if 'console_screensaver' in props:
                cs.set('system.console.screensaver', props['console_screensaver'])
                if props['console_screensaver']:
                    try:
                        system('kldload', 'daemon_saver')
                    except SubprocessException:
                        pass
                else:
                    try:
                        system('kldunload', 'daemon_saver')
                    except SubprocessException:
                        pass
                rc = True

            if 'serial_console' in props:
                cs.set('system.serial.console', props['serial_console'])
                loader = True
                console = True
                console_en_changed = True
            else:
                console_en_changed = False

            if 'serial_port' in props:
                cs.set('system.serial.port', props['serial_port'])
                loader = True
                console = True

            if 'serial_speed' in props:
                cs.set('system.serial.speed', props['serial_speed'])
                loader = True
                console = True

            if 'powerd' in props:
                cs.set('service.powerd.enable', props['powerd'])
                self.dispatcher.call_sync('service.apply_state', 'powerd')
                rc = True

            if 'swapondrive' in props:
                cs.set('system.swapondrive', props['swapondrive'])

            if 'debugkernel' in props:
                cs.set('system.debug.kernel', props['debugkernel'])
                loader = True

            if 'uploadcrash' in props:
                cs.set('system.upload_crash', props['uploadcrash'])
                rc = True

            if 'motd' in props:
                cs.set('system.motd', props['motd'])
                self.dispatcher.call_sync('etcd.generation.generate_file', 'motd')

            if 'boot_scrub_internal' in props:
                cs.set('system.boot_scrub_internal', props['boot_scrub_internal'])

            if 'periodic_notify_user' in props:
                cs.set('system.periodic.notify_user', props['periodic_notify_user'])
                self.dispatcher.call_sync('etcd.generation.generate_group', 'periodic')

            if console:
                self.dispatcher.call_sync('etcd.generation.generate_group', 'console')
            if loader:
                self.dispatcher.call_sync('etcd.generation.generate_group', 'loader')
            if rc:
                self.dispatcher.call_sync('etcd.generation.generate_group', 'services')
            if console_en_changed:
                try:
                    system('grub-mkconfig', '-o', '/boot/grub/grub.cfg')
                except SubprocessException:
                    pass
        except DatastoreException as e:
            raise TaskException(errno.EBADMSG, 'Cannot configure system advanced: {0}'.format(str(e)))
        except RpcException as e:
            raise TaskException(errno.ENXIO, 'Cannot reconfigure system: {0}'.format(str(e)))

        self.dispatcher.dispatch_event('system.advanced.changed', {
            'operation': 'update',
        })


@description("Configures the System UI settings")
@accepts(h.ref('system-ui'))
class SystemUIConfigureTask(Task):

    def describe(self, props):
        return "System UI Settings Configure"

    def verify(self, props):
        return ['system']

    def run(self, props):
        self.configstore.set(
            'service.nginx.http.enable',
            True if 'HTTP' in props.get('webui_protocol', []) else False,
        )
        self.configstore.set(
            'service.nginx.https.enable',
            True if 'HTTPS' in props.get('webui_protocol', []) else False,
        )
        self.configstore.set('service.nginx.listen', props.get('webui_listen'))
        self.configstore.set('service.nginx.http.port', props.get('webui_http_port'))
        self.configstore.set(
            'service.nginx.http.redirect_https', props.get('webui_http_redirect_https'))
        self.configstore.set(
            'service.nginx.https.certificate', props.get('webui_https_certificate'))
        self.configstore.set('service.nginx.https.port', props.get('webui_https_port'))

        try:
            self.dispatcher.call_sync(
                'etcd.generation.generate_group', 'nginx'
            )
            self.dispatcher.call_sync('service.reload', 'nginx')
        except RpcException as e:
            raise TaskException(
                errno.ENXIO,
                'Cannot reconfigure system UI: {0}'.format(str(e),)
            )

        self.dispatcher.dispatch_event('system.ui.changed', {
            'operation': 'update',
            'ids': ['system.ui'],
        })


@accepts(h.all_of(
    h.ref('system-time'),
    h.forbidden('boot_time', 'uptime')
))
@description("Configures system time")
class SystemTimeConfigureTask(Task):
    def verify(self, props):
        return ['system']

    def run(self, props):
        if 'system_time' in props:
            timestamp = time.mktime(parser.parse(props['system_time']))
            bsd.clock_settime(bsd.ClockType.REALTIME, timestamp)

        if 'timezone' in props:
            self.configstore.set('system.timezone', props['timezone'])
            try:
                self.dispatcher.call_sync('etcd.generation.generate_group', 'localtime')
            except RpcException as e:
                raise TaskException(
                    errno.ENXIO,
                    'Cannot reconfigure system time: {0}'.format(str(e))
                )


@accepts(h.any_of(int, None))
@description("Reboots the System")
class SystemRebootTask(Task):
    def __init__(self, dispatcher, datastore):
        super(SystemRebootTask, self).__init__(dispatcher, datastore)
        self.finish_event = Event()
        self.abort_flag = False

    def describe(self, delay=None):
        return "System Reboot"

    def verify(self, delay=None):
        return ['root']

    def reboot_now(self):
        time.sleep(1)
        system('/sbin/shutdown', '-r', 'now')

    def run(self, delay=None):
        if delay:
            self.finish_event.wait(delay)

        if self.abort_flag:
            raise TaskAbortException(errno.EINTR, "User invoked task.abort")

        self.dispatcher.dispatch_event('power.changed', {
            'operation': 'REBOOT',
            })
        t = Thread(target=self.reboot_now, daemon=True)
        t.start()

    def abort(self):
        self.abort_flag = True
        self.finish_event.set()
        return True


@accepts(h.any_of(int, None))
@description("Shuts the system down")
class SystemHaltTask(Task):
    def describe(self):
        return "System Shutdown"

    def verify(self):
        return ['root']

    def shutdown_now(self):
        time.sleep(1)
        system('/sbin/shutdown', '-p', 'now')

    def run(self):
        self.dispatcher.dispatch_event('power.changed', {
            'operation': 'SHUTDOWN',
        })
        t = Thread(target=self.shutdown_now, daemon=True)
        t.start()


def _init(dispatcher, plugin):
    def on_hostname_change(args):
        if 'hostname' not in args:
            return

        if args.get('jid') != 0:
            return

        dispatcher.configstore.set('system.hostname', args['hostname'])
        dispatcher.call_sync('service.restart', 'mdns')
        dispatcher.dispatch_event('system.general.changed', {
            'operation': 'update',
        })

    # Register schemas
    plugin.register_schema_definition('system-advanced', {
        'type': 'object',
        'properties': {
            'console_cli': {'type': 'boolean'},
            'console_screensaver': {'type': 'boolean'},
            'serial_console': {'type': 'boolean'},
            'serial_port': {'type': 'string'},
            'serial_speed': {'type': 'integer'},
            'powerd': {'type': 'boolean'},
            'swapondrive': {'type': 'integer'},
            'debugkernel': {'type': 'boolean'},
            'uploadcrash': {'type': 'boolean'},
            'motd': {'type': 'string'},
            'boot_scrub_internal': {'type': 'integer'},
            'periodic_notify_user': {'type': 'integer'},
        },
        'additionalProperties': False,
    })

    plugin.register_schema_definition('system-general', {
        'type': 'object',
        'properties': {
            'hostname': {'type': 'string'},
            'language': {'type': 'string'},
            'timezone': {'type': 'string'},
            'console_keymap': {'type': 'string'},
            'syslog_server': {'type': ['string', 'null']},
        },
        'additionalProperties': False,
    })

    plugin.register_schema_definition('system-ui', {
        'type': 'object',
        'properties': {
            'webui_protocol': {
                'type': ['array'],
                'items': {
                    'type': 'string',
                    'enum': ['HTTP', 'HTTPS'],
                },
            },
            'webui_listen': {
                'type': ['array'],
                'items': {'type': 'string'},
            },
            'webui_http_redirect_https': {'type': 'boolean'},
            'webui_http_port': {'type': 'integer'},
            'webui_https_certificate': {'type': ['string', 'null']},
            'webui_https_port': {'type': 'integer'},
        },
        'additionalProperties': False,
    })

    plugin.register_schema_definition('system-time', {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'system_time': {'type': 'string'},
            'boot_time': {'type': 'string'},
            'uptime': {'type': 'string'},
            'timezone': {'type': 'string'}
        }
    })

    plugin.register_schema_definition('power_changed', {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'operation': {'type': 'string', 'enum': ['SHUTDOWN', 'REBOOT']},
        }
    })

    # Register event handler
    plugin.register_event_handler('system.hostname.change', on_hostname_change)

    # Register Event Types
    plugin.register_event_type('power.changed', schema=h.ref('power_changed'))

    # Register providers
    plugin.register_provider("system.advanced", SystemAdvancedProvider)
    plugin.register_provider("system.general", SystemGeneralProvider)
    plugin.register_provider("system.info", SystemInfoProvider)
    plugin.register_provider("system.ui", SystemUIProvider)

    # Register task handlers
    plugin.register_task_handler("system.advanced.update", SystemAdvancedConfigureTask)
    plugin.register_task_handler("system.general.update", SystemGeneralConfigureTask)
    plugin.register_task_handler("system.ui.update", SystemUIConfigureTask)
    plugin.register_task_handler("system.time.update", SystemTimeConfigureTask)
    plugin.register_task_handler("system.shutdown", SystemHaltTask)
    plugin.register_task_handler("system.reboot", SystemRebootTask)

    # Set initial hostname
    netif.set_hostname(dispatcher.configstore.get('system.hostname'))
