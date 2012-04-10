import hashlib
import json
import os
import urllib

from django.utils.translation import ugettext_lazy as _

from dojango import forms
from transmissionUI.freenas import models, utils


class TransmissionForm(forms.ModelForm):

    class Meta:
        model = models.Transmission
        widgets = {
            'rpc_port': forms.widgets.TextInput(),
            'peer_port': forms.widgets.TextInput(),
            'rpc_password': forms.widgets.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        self.mountpoints = kwargs.pop('mountpoints', [])
        self.plugin = kwargs.pop('plugin')
        self.jail = kwargs.pop('jail')
        super(TransmissionForm, self).__init__(*args, **kwargs)

        self.fields['logfile'].widget = forms.widgets.TextInput(attrs={
            'data-dojo-type': 'freeadmin.form.PathSelector',
            'root': os.path.join(
                self.jail['fields']['jail_path'],
                self.jail['fields']['jail_name'],
                #self.plugin['fields']['plugin_path'][1:],
                ),
            'dirsonly': 'false',
            })

        self.fields['conf_dir'].widget = self.fields['download_dir'].widget = self.fields['watch_dir'].widget = forms.widgets.TextInput(attrs={
            'data-dojo-type': 'freeadmin.form.PathSelector',
            'root': os.path.join(
                self.jail['fields']['jail_path'],
                self.jail['fields']['jail_name'],
                #self.plugin['fields']['plugin_path'][1:],
                ),
            'dirsonly': 'true',
            })

    def save(self, *args, **kwargs):
        obj = super(TransmissionForm, self).save(*args, **kwargs)

        advanced_settings = {}
        for field in obj._meta.local_fields:
            if field.attname not in utils.transmission_advanced_vars:
                continue
            info = utils.transmission_advanced_vars.get(field.attname)
            value = getattr(obj, field.attname)
            if info["type"] == "checkbox":
                if value:
                    if info.get("on"):
                        advanced_settings[field.attname] = info["on"]
                else:
                    if info.get("off"):
                        advanced_settings[field.attname] = info["off"]

            elif info["type"] == "textbox" and value:
                advanced_settings[field.attname] = "%s %s" % (info["opt"], value)

        rcconf = os.path.join(utils.transmission_etc_path, "rc.conf")
        with open(rcconf, "w") as f:
            if obj.enable:
                f.write('transmission_enable="YES"\n')

            if obj.watch_dir:
                f.write('transmission_watch_dir="%s"\n' % (obj.watch_dir, ))

            if obj.conf_dir:
                f.write('transmission_conf_dir="%s"\n' % (obj.conf_dir, ))

            if obj.download_dir:
                f.write('transmission_download_dir="%s"\n' % (obj.conf_dir, ))

            transmission_flags = ""
            for value in advanced_settings.values():
                transmission_flags += value + " "
            f.write('transmission_flags="%s"\n' % (transmission_flags, ))

        if obj.watch_dir:
            #os.system("/usr/sbin/chown -R transmission:transmission '%s'" % (obj.watch_dir, ))
            os.chown
            os.chmod(obj.watch_dir, 0o755)

        #os.system("/usr/sbin/chown -R transmission:transmission '%s'" % main_settings["transmission_conf_dir"])
        os.chmod(obj.conf_dir, 0o755)

        if obj.download_dir:
            #os.system("/usr/sbin/chown -R transmission:transmission '%s'" % main_settings["transmission_download_dir"])
            os.chmod(obj.download_dir, 0o755)

        if not os.path.exists(obj.conf_dir):
            try:
                os.makedirs(obj.conf_dir)
            except OSError:
                pass

        settingsfile = os.path.join(obj.conf_dir, "settings.json")
        if os.path.exists(settingsfile):
            with open(settingsfile, 'r') as f:
                settings = json.loads(f.read())
        else:
            try:
                open(settingsfile, 'w').close()
            except OSError:
                #FIXME
                pass
            settings = {}

        settings['rpc-whitelist'] = obj.rpc_whitelist
        settings['rpc-enabled'] = obj.rpc_auth
        settings['rpc-authentication-required'] = obj.rpc_auth_required
        if obj.rpc_password:
            settings['rpc-password'] = '{' + hashlib.sha1(obj.rpc_password).hexdigest()
        settings['rpc-whitelist-enabled'] = obj.rpc_whitelist_enabled
        with open(settingsfile, 'w') as f:
            f.write(json.dumps(settings, sort_keys=True, indent=4))

        os.system(os.path.join(utils.transmission_pbi_path, "tweak-rcconf"))
