# Menu for Alfredo

![Alfredo Logo](alfredo.png)

# Install webomints on \*nix
(source/based on: https://tex.stackexchange.com/questions/284082/cant-install-webomints-package)

You can run [setup.sh](setup.sh) to automate this step.

```bash
wget https://tug.org/fonts/getnonfreefonts/install-getnonfreefonts
texlua install-getnonfreefonts
getnonfreefonts --sys webomints
```

Some of these commands may require sudo. Use --user instead of --sys to install the font for the current user only.

# Install webomints on Windows
Miktex does that for you. Easy.
In case it doesn't, follow the \*nix steps instead.

# TODO
* update/extend menu choices
* add Schlonz recipe
