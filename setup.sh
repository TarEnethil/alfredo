#!/bin/bash

wget https://tug.org/fonts/getnonfreefonts/install-getnonfreefonts
texlua install-getnonfreefonts
getnonfreefonts --sys webomints
