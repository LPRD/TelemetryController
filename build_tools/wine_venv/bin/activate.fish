# This file must be used with ". bin/activate.fish" *from fish*
# (http://fishshell.org) you cannot run it directly
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

function deactivate  -d "Exit virtualenv and return to normal shell environment"
    # reset old environment variables
    if test -n "$_OLD_VIRTUALWINE_PATH" 
        set -gx PATH $_OLD_VIRTUALWINE_PATH
        set -e _OLD_VIRTUALWINE_PATH
    end

    if test -n "$_OLD_VIRTUALWINE_PROMPT"
        functions -e fish_prompt
        set -e _OLD_VIRTUALWINE_PROMPT
    end

    set -e WINEPREFIX
    if test "$argv[1]" != "nondestructive"
        # Self destruct!
        functions -e deactivate
    end
end

# unset irrelavent variables
deactivate nondestructive

set -gx WINEPREFIX '/media/shared/lrk/U_of_M/Research/LPRD/Telemetry-display/build_tools/wine_venv/'

set -gx _OLD_VIRTUALWINE_PATH $PATH
set -gx PATH "$WINEPREFIX/bin" $PATH


if test -z "$WINEPREFIX_DISABLE_PROMPT"
    # fish shell uses a function, instead of env vars,
    # to produce the prompt. Overriding the existing function is easy.
    # However, adding to the current prompt, instead of clobbering it,
    # is a little more work.
    set -l oldpromptfile (tempfile)
    if test $status
        # save the current fish_prompt function...
        echo "function _old_fish_prompt" >> $oldpromptfile
        echo -n \# >> $oldpromptfile
        functions fish_prompt >> $oldpromptfile
        # we've made the "_old_fish_prompt" file, source it.
        . $oldpromptfile
        rm -f $oldpromptfile
        
        if test -n ""
            # We've been given us a prompt override.
            # 
            # FIXME: Unsure how to handle this *safely*. We could just eval()
            #   whatever is given, but the risk is a bit much.
            echo "activate.fish: Alternative prompt prefix is not supported under fish-shell." 1>&2
            echo "activate.fish: Alter the fish_prompt in this file as needed." 1>&2
        end        
        
        # with the original prompt function renamed, we can override with our own.
        function fish_prompt                
            set -l _checkbase (basename "$WINEPREFIX")
            if test $_checkbase = "__"
                # special case for Aspen magic directories
                # see http://www.zetadev.com/software/aspen/
                printf "%s[%s]%s %s" (set_color -b blue white) (basename (dirname "$WINEPREFIX")) (set_color normal) (_old_fish_prompt)
            else
                printf "%s(%s)%s%s" (set_color -b blue white) (basename "$WINEPREFIX") (set_color normal) (_old_fish_prompt)
            end
        end 
        set -gx _OLD_VIRTUALWINE_PROMPT "$WINEPREFIX"
    end
end
