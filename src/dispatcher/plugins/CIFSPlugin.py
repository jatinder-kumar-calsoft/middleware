#
# Copyright 2015 iXsystems, Inc.
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
import errno
import logging
import os

from datastore.config import ConfigNode
from dispatcher.rpc import RpcException, SchemaHelper as h, description, accepts, returns
from task import Task, Provider, TaskException, ValidationException

logger = logging.getLogger('CIFSPlugin')


@description('Provides info about CIFS service configuration')
class CIFSProvider(Provider):
    @accepts()
    @returns(h.ref('service-cifs'))
    def get_config(self):
        return ConfigNode('service.cifs', self.configstore)


@description('Configure CIFS service')
@accepts(h.ref('service-cifs'))
class CIFSConfigureTask(Task):
    def describe(self, share):
        return 'Configuring CIFS service'

    def verify(self, cifs):
        return ['system']

    def run(self, cifs):
        try:
            node = ConfigNode('service.cifs', self.configstore)
            node.update(cifs)
            self.dispatcher.call_sync('etcd.generation.generate_group', 'services')
            self.dispatcher.call_sync('etcd.generation.generate_group', 'samba')
            self.dispatcher.call_sync('services.reload', 'cifs')
            self.dispatcher.dispatch_event('service.cifs.changed', {
                'operation': 'updated',
                'ids': None,
            })
        except RpcException, e:
            raise TaskException(
                errno.ENXIO, 'Cannot reconfigure CIFS: {0}'.format(str(e))
            )


def _depends():
    return ['ServiceManagePlugin']


def _init(dispatcher, plugin):
    # Register schemas
    PROTOCOLS = [
        'CORE',
        'COREPLUS',
        'LANMAN1',
        'LANMAN2',
        'NT1',
        'SMB2',
        'SMB2_02',
        'SMB2_10',
        'SMB2_22',
        'SMB2_24',
        'SMB3',
        'SMB3_00',
    ]
    plugin.register_schema_definition('service-cifs', {
        'type': 'object',
        'properties': {
            'netbiosname': {'type': 'string'},
            'workgroup': {'type': 'string'},
            'description': {'type': 'string'},
            'dos_charset': {'type': 'string'},
            'unix_charset': {'type': 'string'},
            'log_level': {'type': 'string'},
            'syslog': {'type': 'boolean'},
            'local_master': {'type': 'boolean'},
            'domain_logons': {'type': 'boolean'},
            'time_server': {'type': 'boolean'},
            'guest_user': {'type': 'string'},
            'filemask': {'type': ['string', 'null']},
            'dirmask': {'type': ['string', 'null']},
            'empty_password': {'type': 'boolean'},
            'unixext': {'type': 'boolean'},
            'zeroconf': {'type': 'boolean'},
            'hostlookup': {'type': 'boolean'},
            'min_protocol': {'type': 'string', 'enum': PROTOCOLS},
            'max_protocol': {'type': 'string', 'enum': PROTOCOLS},
            'execute_always': {'type': 'boolean'},
            'obey_pam_restrictions': {'type': 'boolean'},
            'bind_addresses': {
                'type': ['array', 'null'],
                'items': {'type': 'string'},
            },
            'auxiliary': {'type': ['string', 'null']},
            'sid': {'type': ['string', 'null']},
        },
        'additionalProperties': False,
    })

    # Register providers
    plugin.register_provider("service.cifs", CIFSProvider)

    # Register tasks
    plugin.register_task_handler("service.cifs.configure", CIFSConfigureTask)
