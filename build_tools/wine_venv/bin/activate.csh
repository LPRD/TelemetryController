# This file must be used with "source bin/activate.csh" *from csh*.
# You cannot run it directly.
#
# This file is part of `vwine`.
#
# Copyright 2011-2012 by Hartmut Goebel <h.goebel@goebel-consult.de>
# Licence: GNU General Public License version 3 (GPL v3)
# Version: 0.1
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Based on work
#  Copyright (c) 2007 Ian Bicking and Contributors
#  Copyright (c) 2009 Ian Bicking, The Open Planning Project
#  Copyright (c) 2011 The virtualenv developers
# licensed under an MIT-style permissive license, see 
# https://raw.github.com/pypa/virtualenv/master/LICENSE.txt
#

alias deactivate 'test $?_OLD_VIRTUALWINE_PATH != 0 && setenv PATH "$_OLD_VIRTUALWINE_PATH" && unset _OLD_VIRTUALWINE_PATH; rehash; test $?_OLD_VIRTUALWINE_PROMPT != 0 && set prompt="$_OLD_VIRTUALWINE_PROMPT" && unset _OLD_VIRTUALWINE_PROMPT; unsetenv WINEPREFIX; test "\!:*" != "nondestructive" && unalias deactivate'

# Unset irrelavent variables.
deactivate nondestructive

setenv WINEPREFIX '/media/shared/lrk/U_of_M/Research/LPRD/Telemetry-display/build_tools/wine_venv/'

set _OLD_VIRTUALWINE_PATH="$PATH"
setenv PATH "$WINEPREFIX/bin:$PATH"

set _OLD_VIRTUALWINE_PROMPT="$prompt"

if ("" != "") then
    set env_name = ""
else
    if (`basename "$WINEPREFIX"` == "__") then
        # special case for Aspen magic directories
        # see http://www.zetadev.com/software/aspen/
        set env_name = `basename \`dirname "$WINEPREFIX"\``
    else
        set env_name = `basename "$WINEPREFIX"`
    endif
endif
set prompt = "[$env_name] $prompt"
unset env_name

rehash

