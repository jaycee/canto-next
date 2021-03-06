# -*- coding: utf-8 -*-

#Canto - RSS reader backend
#   Copyright (C) 2010 Jack Miller <jack@codezen.org>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2 as 
#   published by the Free Software Foundation.

import traceback
import logging

log = logging.getLogger("HOOKS")

hooks = {}

def on_hook(hook, func):
    if hook in hooks:
        hooks[hook].append(func)
    else:
        hooks[hook] = [func]

def remove_hook(hook, func):
    if hook in hooks and func in hooks[hook]:
        hooks[hook].remove(func)

def call_hook(hook, args):
    if hook in hooks:

        # List copy here so hooks can remove themselves
        # without effecting our iteration.

        try:
            for func in hooks[hook][:]:
                func(*args)
        except:
            log.error("Error calling hook %s (func: %s args: %s)" % (hook, func, args))
            log.error(traceback.format_exc())
