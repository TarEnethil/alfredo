.PHONY: menu recipes all clean cleanall

LATEXMK = latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode" -use-make

all: menu recipes

menu:
	$(LATEXMK) menu.tex

recipes:
	$(LATEXMK) recipes.tex

clean:
	latexmk -CA
	rm -f *.aux *.log *.synctex.gz *.toc

cleanall: clean
	rm -f *.pdf
