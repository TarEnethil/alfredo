.PHONY: menu recipes all clean

LATEXMK = latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode" -use-make

all: menu recipes

menu:
	$(LATEXMK) menu.tex

recipes:
	$(LATEXMK) recipes.tex

clean:
	latexmk -CA
	rm -f *.aux *.log *.pdf *.synctex.gz *.toc
