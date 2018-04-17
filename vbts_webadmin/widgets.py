"""
Copyright (c) 2015-present, Philippine-California Advanced Research Institutes-
The Village Base Station Project (PCARI-VBTS). All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""

from __future__ import unicode_literals
from django import get_version, forms
from django.forms import Widget
from django import utils
import copy
from distutils.version import StrictVersion

try:
    import simplejson as json
except ImportError:
    import json
if StrictVersion(get_version()) < StrictVersion('1.9.0'):
    from django.forms.util import flatatt
else:
    from django.forms.utils import flatatt

from django.utils.safestring import mark_safe

""" 2DArrayJSON Widget
    Returns bootstrap3 designed table
"""


class JSON2DArrayWidget(forms.Widget):
    def __init__(self, attrs=None, newline='<br/>\n', sep='__',
                 col1='col-md-3', col2='col-md-9',
                 debug=False):
        self.newline = newline
        self.separator = sep
        self.debug = debug
        self.css_column1 = col1
        self.css_column2 = col2

        Widget.__init__(self, attrs)

    def _as_tablecolumn(self, name, type, key):
        attrs = self.build_attrs(self.attrs, type='text',
                                 name="%s_%s[]" % (name, type))
        attrs['class'] = "form-control"
        attrs['value'] = utils.encoding.force_unicode(key)
        attrs['id'] = attrs.get('name', None)
        return """<td><input %s /></td>""" % (flatatt(attrs))

    def _value_as_tablecolumn(self, name, type, key):
        attrs = self.build_attrs(self.attrs, type='text',
                                 name="%s_%s[]" % (name, type))
        attrs['class'] = "form-control"
        attrs['value'] = utils.encoding.force_unicode(key)
        attrs['id'] = attrs.get('name', None)
        return """<td>
                    <input %s />
                </td>
                <td>
                    <button type="button" class="remove_item close" aria-label="Close">
                        <span aria-hidden="true">&times;</span></button>
                    <button type="button" class="add_item close" aria-label="Close">
                        <span aria-hidden="true">&plus;</span></button>
                </td>""" % (flatatt(attrs))

    def _to_build_dynamic_json_as_table(self, name, subname, json_obj):
        result = """<table class="script-properties">"""
        for key, value in json_obj.items():
            key = self._as_tablecolumn(subname, 'key', key)
            value = self._value_as_tablecolumn(subname, 'value', value)
            result += """<tr><td>%s</td><td>%s</td></tr>""" % (key, value)
        result += """<tr>
                    <td colspan="2">
                    <span><a hre="#" id="add_field_button">Add More Fields</a>
                    </span></td>
                    </tr>
                    </table>"""
        return result

    def _as_tablerow(self, name, key, value):
        attrs = self.build_attrs(self.attrs, type='text',
                                 name="%s__%s" % (name, key))
        attrs['class'] = "form-control"
        attrs['value'] = utils.encoding.force_unicode(value)
        attrs['id'] = attrs.get('name', None)
        return """
                <tr><td>
                <label>%s</label>
                </td><td><input%s/></td>
                </tr>
                """ % (key.upper(), flatatt(attrs))

    def _to_build_as_table(self, name, json_obj):
        result = "<table>"
        for key, value in json_obj.items():
            if isinstance(value, dict):
                subname = "%s%s%s" % (name, self.separator, key)
                temp = self._to_build_dynamic_json_as_table(
                    key, subname, value)
                result += """<tr>
                    <td class="title"><strong>%s</strong></td>
                    <td>%s</td></tr>""" % (key.upper(), temp)
            else:
                result += self._as_tablerow(name, key, value)
        result += "</table>"
        return result

    def _to_pack_up_2D(self, root_node, raw_data):
        copy_raw_data = copy.deepcopy(raw_data)
        result = {}

        for key in copy_raw_data.iterkeys():
            if key.find(root_node) != -1:
                subkeys = raw_data.getlist(key)
                apx, _, nk = key.rpartition(self.separator)
                if nk.find('key[]') != -1:
                    keyname = nk[:-6]
                    subvalues_list = "%s%s%s_value[]" % (
                        root_node, self.separator, keyname)
                    subvalues = raw_data.getlist(subvalues_list)
                    myresult = {}
                    for k, v in zip(subkeys, subvalues):
                        myresult[str(k)] = str(v)
                    result[str(keyname)] = myresult
                elif nk.find('value[]') != -1:
                    pass
                else:
                    result[str(nk)] = str(subkeys[0])
        return result

    def value_from_datadict(self, data, files, name):
        data_copy = copy.deepcopy(data)
        result = self._to_pack_up_2D(name, data_copy)
        return json.dumps(result)

    def render(self, name, value, attrs=None):
        result = {}
        try:
            value = json.loads(value)
            result = self._to_build_as_table(name, value or {})
        except (TypeError, KeyError):
            pass

        return result


"""
Source: https://github.com/bradleyayers/django-ace
"""


class AceWidget(forms.Textarea):
    def __init__(self, mode=None, theme=None, wordwrap=False, width="500px",
                 height="300px", minlines=None, maxlines=None,
                 showprintmargin=True, *args, **kwargs):
        self.mode = mode
        self.theme = theme
        self.wordwrap = wordwrap
        self.width = width
        self.height = height
        self.minlines = minlines
        self.maxlines = maxlines
        self.showprintmargin = showprintmargin
        super(AceWidget, self).__init__(*args, **kwargs)

    @property
    def media(self):
        js = [
            "ace/ace.js",
            "ace/django-ace-widget.js",
        ]
        if self.mode:
            js.append("ace/mode-%s.js" % self.mode)
        if self.theme:
            js.append("ace/theme-%s.js" % self.theme)
        css = {
            "screen": ["ace/django-ace-widget.css"],
        }
        return forms.Media(js=js, css=css)

    def render(self, name, value, attrs=None):
        attrs = attrs or {}

        ace_attrs = {
            "class": "django-ace-widget loading",
            "style": "width:%s; height:%s" % (self.width, self.height)
        }
        if self.mode:
            ace_attrs["data-mode"] = self.mode
        if self.theme:
            ace_attrs["data-theme"] = self.theme
        if self.wordwrap:
            ace_attrs["data-wordwrap"] = "true"
        if self.minlines:
            ace_attrs["data-minlines"] = str(self.minlines)
        if self.maxlines:
            ace_attrs["data-maxlines"] = str(self.maxlines)
        ace_attrs[
            "data-showprintmargin"] = "true" if self.showprintmargin else "false"

        textarea = super(AceWidget, self).render(name, value, attrs)

        html = '<div%s><div></div></div>%s' % (flatatt(ace_attrs), textarea)

        html = '<div class="django-ace-editor"><div style="width: %s" class="django-ace-toolbar">' \
               '<span class="django-ace-max_min"></span></div>%s</div>' % (
                   self.width, html)

        return mark_safe(html)
