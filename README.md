# Menu for Alfredo

![Alfredo Logo](alfredo.png)

# Install webomints on *nix
(source/based on: https://tex.stackexchange.com/questions/284082/cant-install-webomints-package)

```bash
wget https://tug.org/fonts/getnonfreefonts/install-getnonfreefonts
texlua install-getnonfreefonts
getnonfreefonts --sys webomints
```

Some of these commands may require sudo. Use --usr instead of --sys to install the font for the current user only.

# Install webomints on Windows
Miktex does that for you. Easy.

# TODO
* create Makefile for menu
* update/extend menu choices
* add Schlonz recipe
