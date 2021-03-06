#+
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


import time
import six
import gettext
import natural.date
from texttable import Texttable
from freenas.cli import config
from freenas.cli.output import ValueType, get_terminal_size, resolve_cell, get_humanized_size


t = gettext.translation('freenas-cli', fallback=True)
_ = t.gettext


class TableOutputFormatter(object):
    @staticmethod
    def format_value(value, vt):
        if vt == ValueType.BOOLEAN:
            return _("yes") if value else _("no")

        if value is None:
            return _("none")

        if vt == ValueType.SET:
            value = list(value)
            if len(value) == 0:
                return _("empty")

            return '\n'.join(value)

        if vt == ValueType.STRING:
            return value

        if vt == ValueType.NUMBER:
            return str(value)

        if vt == ValueType.HEXNUMBER:
            return hex(value)

        if vt == ValueType.SIZE:
            return get_humanized_size(value)

        if vt == ValueType.TIME:
            fmt = config.instance.variables.get('datetime_format')
            if fmt == 'natural':
                return natural.date.duration(value)

            return time.strftime(fmt, time.localtime(value))

    @staticmethod
    def output_list(data, label, vt=ValueType.STRING):
        table = Texttable(max_width=get_terminal_size()[1])
        table.set_deco(Texttable.BORDER | Texttable.VLINES | Texttable.HEADER)
        table.header([label])
        table.add_rows([[i] for i in data], False)
        six.print_(table.draw())

    @staticmethod
    def output_dict(data, key_label, value_label, value_vt=ValueType.STRING):
        table = Texttable(max_width=get_terminal_size()[1])
        table.set_deco(Texttable.BORDER | Texttable.VLINES | Texttable.HEADER)
        table.header([key_label, value_label])
        table.add_rows([[row[0], TableOutputFormatter.format_value(row[1], value_vt)] for row in list(data.items())], False)
        six.print_(table.draw())

    @staticmethod
    def output_table(data, columns):
        table = Texttable(max_width=get_terminal_size()[1])
        table.set_deco(Texttable.BORDER | Texttable.VLINES | Texttable.HEADER)
        table.header([i.label for i in columns])
        table.add_rows([[TableOutputFormatter.format_value(resolve_cell(row, i.accessor), i.vt) for i in columns] for row in data], False)
        six.print_(table.draw())

    @staticmethod
    def output_object(items):
        table = Texttable(max_width=get_terminal_size()[1])
        table.set_deco(Texttable.BORDER | Texttable.VLINES)
        for i in items:
            if len(i) == 3:
                name, _, value = i
                table.add_row([name, TableOutputFormatter.format_value(value, ValueType.STRING)])

            if len(i) == 4:
                name, _, value, vt = i
                table.add_row([name, TableOutputFormatter.format_value(value, vt)])

        six.print_(table.draw())

    @staticmethod
    def output_tree(tree, children, label, label_vt=ValueType.STRING):
        def branch(obj, indent):
            for idx, i in enumerate(obj):
                subtree = resolve_cell(i, children)
                char = '+' if subtree else ('`' if idx == len(obj) - 1 else '|')
                six.print_('{0} {1}-- {2}'.format('    ' * indent, char, resolve_cell(i, label)))
                if subtree:
                    branch(subtree, indent + 1)

        branch(tree, 0)


def _formatter():
    return TableOutputFormatter
