# -*- coding: utf-8 -*-

#Canto - RSS reader backend
#   Copyright (C) 2010 Jack Miller <jack@codezen.org>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2 as 
#   published by the Free Software Foundation.

import traceback
import logging
import inspect
import sys
import os

log = logging.getLogger("PLUGINS")

def try_plugins(topdir):
    p = topdir + "/plugins"
    pinit = p + "/__init__.py"

    if not os.path.exists(p):
        log.info("Creating plugins directory.")
        try:
            os.mkdir(p)
        except Exception as e:
            tb = traceback.format_exc()
            log.error("Exception creating plugin directory")
            log.error("\n" + "".join(tb))
            return
    elif not os.path.isdir(p):
        log.warn("Plugins file is not directory.")
        return

    if not os.path.exists(pinit):
        log.info("Creating plugin __init__.py")
        try:
            f = open(pinit, "w")
            f.close()
        except Exception as e:
            tb = traceback.format_exc()
            log.error("Exception creating plugin __init__.py")
            log.error("\n" + "".join(tb))
            return

    # Add plugin path to front of Python path.
    sys.path.insert(0, topdir)

    # Go ahead and import all .py
    for fname in os.listdir(p):
        if fname.endswith(".py") and fname != "__init__.py":
            try:
                proper = fname[:-3]
                log.info("[plugin] %s" % proper)
                __import__("plugins." + proper)
            except Exception as e:
                tb = traceback.format_exc()
                log.error("Exception importing file %s" % fname)
                log.error("\n" + "".join(tb))

arg_transforms = {}
def add_arg_transform(fn, trans):

    # If we get passed a method, get its
    # func implementation.

    if hasattr(fn, "__func__"):
        fn = fn.__func__

    arg_transforms[repr(fn)] = trans

class PluginHandler(object):
    def __init__(self):
        self.plugin_attrs = {}

    def update_plugin_lookups(self):
        # Populate a dict of overridden attributes

        self.plugin_attrs = {}

        self.plugin_class_instances =\
                [ c() for c in self.plugin_class.__subclasses__() ]

        for iclass in self.plugin_class_instances[:]:
            try:
                # Warn if we're overriding a previously defined plugin attr
                for iclass_attr in list(iclass.plugin_attrs.keys()):
                    if iclass_attr in self.plugin_attrs:
                        log.warn("Multiply defined plugin attribute!: %s" %\
                                iclass_attr)

                self.plugin_attrs.update(iclass.plugin_attrs)
            except Exception as e:
                log.error("Error initializing plugins:")
                log.error(traceback.format_exc())

                # Malformed plugins removed from instances
                self.plugin_class_instances.remove(iclass)
                continue

        # Complete the dict by preparing arg transformed functions

        for trans_obj in [ self ] + self.plugin_class_instances:
            for attr in dir(trans_obj):
                a = getattr(trans_obj, attr)

                # Skip non-functions, which make no sense
                # to have argument transforms.

                if "__func__" not in dir(a):
                    continue

                f = repr(getattr(a, "__func__"))

                # Skip functions without transforms defined

                if f not in arg_transforms:
                    continue

                # Wrap the target function with the transform.

                argt = arg_transforms[f]

                self.plugin_attrs[attr] = self.__wrap_argt(trans_obj, argt, a)

    # This has to be done in a new scope so that the newfunc doesn't bind to
    # the reference in the above loop and get majorly confused.

    def __wrap_argt(self, origin_obj, argt, realfunc):
        def newfunc(*args, **kwargs):
            r = argt(args[0], origin_obj, *args[1:], **kwargs)
            if not r:
                return False

            args, kwargs = r
            r = realfunc(*args, **kwargs)
            return r
        return newfunc

    def __getattribute__(self, name):
        if name == "plugin_attrs" or name not in self.plugin_attrs:
            return object.__getattribute__(self, name)
        return self.plugin_attrs[name]

# Plugin is the base class for all of the separate plugin classes for each Gui
# object. There are two reasons to pin plugins to an empty class:
#
# - 'object' in the hierarchy via PluginHandler means we can use
#   __subclasses__, the cornerstone of the plugins system
#
# - This allows the plugins to have a hard distinction between self (the
#   instantiated class object) and obj (the instantiated main object that's
#   being overridden). This means that plugins don't have to worry about
#   clobbering anything.
#
# As a side effect, using the separate plugin architecture, we also can
# enable/disable pluggability on a class basis. For example, if TagList
# didn't specify a plugin_class, then it could not be overridden or hooked.

class Plugin(object):
        pass
