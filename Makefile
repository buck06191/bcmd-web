# Makefile.  Generated from Makefile.in by configure.

# general build tool settings
# the following are set by the configure script
CC = gcc
CFLAGS = -g -O2
FC = gfortran
FCFLAGS = -g -O2
FCLIBS =  -L/usr/lib/gcc/x86_64-linux-gnu/6 -L/usr/lib/gcc/x86_64-linux-gnu/6/../../../x86_64-linux-gnu -L/usr/lib/gcc/x86_64-linux-gnu/6/../../../../lib -L/lib/x86_64-linux-gnu -L/lib/../lib -L/usr/lib/x86_64-linux-gnu -L/usr/lib/../lib -L/usr/lib/gcc/x86_64-linux-gnu/6/../../.. -lgfortran -lm -lquadmath

# these don't reliably get sensible values from configure
# so until I figure out why, set explicitly
# (this is the setting on all platforms tried so far anyway)
AR = ar
ARFLAGS = crs

# for the moment assume python is on the path
# (maybe use configure for this later)
PYTHON = python

# similarly for GraphViz -- which is pretty much optional anyway, but...
GV = dot

# By default we set DEBUG=FALSE. This is to allow for correct stdout output
# when using the BayesCMD bcmd_model code.
DEBUG=FALSE

# change this to TRUE -- or pass in DEBUG=TRUE on the command line
# to enable heavy logging from the RADAU wrapper library
SUPER_DEBUG=FALSE

# the system is not, in general, tied to a particular
# directory layout; however, it is convenient to have quasi-standard
# directories for shorthand building. hopefully this will not get
# out of hand and turn into the sort of monster BRAINCIRC was...
BUILD = build
MODELDEFS = examples
INPUTS = examples
PARSER = bparser
TEMPLATES = $(PARSER)/templates


# the internal tools for the system
BCMD = $(PYTHON) $(PARSER)/bcmd.py
BCMD_DEPS = $(PARSER)/bcmd.py $(PARSER)/parsetab.py \
            $(PARSER)/ast.py $(PARSER)/logger.py $(PARSER)/codegen.py \
            $(PARSER)/info.py $(TEMPLATES)/*.c_template

ifeq ($(DEBUG),TRUE)
  RADAU_WRAP_DEBUG = -DRADAU_DEBUG
  BFLAGS = -v 7 -t -p -g -G
else
  RADAU_WRAP_DEBUG =
  BFLAGS = -v 5 -t -p -G
endif

ifeq ($(SUPER_DEBUG),TRUE)
  RADAU_WRAP_SUPER_DEBUG = -DRADAU_SUPER_DEBUG
else
  RADAU_WRAP_SUPER_DEBUG =
endif


all: lib test

lib: lib/libradau.a lib/libradauwrap.a $(PARSER)/parsetab.py

test: test/radautest

doc: doc/manual.pdf


# stuff to build the RADAU stiff ODE/DAE solver library
RADAU = src/radau
RADAU_OBJ = $(RADAU)/radau.o $(RADAU)/radau5.o $(RADAU)/radauTest.o \
            $(RADAU)/dc_lapack.o $(RADAU)/lapack.o $(RADAU)/lapackc.o

$(RADAU)/%.o: $(RADAU)/%.f
	$(FC) -c $(FFLAGS) -o $@ $<

lib/libradau.a: $(RADAU_OBJ)
	$(AR) $(ARFLAGS) lib/libradau.a $(RADAU_OBJ)

# another library, for wrapper functions around RADAU
RADAU_WRAP = src/radauwrap
RADAU_WRAP_SRC = $(RADAU_WRAP)/radau5_interface.c $(RADAU)/radau.h \
                 $(RADAU_WRAP)/radau5_interface.h

lib/libradauwrap.a: $(RADAU_WRAP_SRC)
	$(CC) $(CFLAGS) -I$(RADAU) $(RADAU_WRAP_DEBUG) $(RADAU_WRAP_SUPER_DEBUG) -c $< -o $(BUILD)/radau5_interface.o
	$(AR) $(ARFLAGS) $@ $(BUILD)/radau5_interface.o

test/radautest: $(RADAU_WRAP_SRC)
	$(CC) $(CFLAGS) -I$(RADAU) $< -L./lib -lradau $(FCLIBS) -DRADAU_DEBUG_MAIN -DRADAU_DEBUG -o $@


# make manual from latex
# this is clunky and should really be in a recursive makefile, but...
doc/manual.pdf: doc/manual.tex doc/bib/papers.bib
	cd doc; pdflatex manual.tex
	cd doc; bibtex manual.aux
	cd doc; pdflatex manual.tex
	cd doc; pdflatex manual.tex


# model building
%.model: %.c lib
	$(CC) $(CFLAGS) -I$(RADAU_WRAP) -I$(RADAU) $< -L./lib -lradauwrap -lradau $(FCLIBS) $(RADAU_WRAP_DEBUG) -o $@


# it's convenient to ensure the parser tables are pre-built in the parser dir
# otherwise they may get rebuilt elsewhere
$(PARSER)/parsetab.py: $(PARSER)/bcmd_yacc.py $(PARSER)/bcmd_lex.py
	@echo '** rebuilding parse tables **'
	- cd $(PARSER); rm parsetab.*; python bcmd.py --yacc /dev/null

# these targets are locally useful, and serve as examples, but should
# not be considered the correct way to do things
$(BUILD)/%.c: $(MODELDEFS)/%.modeldef $(BCMD_DEPS)
	$(BCMD) $(BFLAGS) -i $(MODELDEFS) -d $(BUILD) $* 2> $(BUILD)/$*.log

$(BUILD)/%.detail: $(BUILD)/%.model $(INPUTS)/%.input
	$< -i $(INPUTS)/$*.input -o $(BUILD)/$*.out -d $@ > $(BUILD)/$*.stdout 2> $(BUILD)/$*.stderr

$(BUILD)/%.pdf: $(BUILD)/%.gv
	$(GV) -Tpdf -o $@ $<


# configuration and distribution
configure: configure.ac autogen.sh
	./autogen.sh

# remove all build and configuration results
distclean:
	make workclean
	make clean
	- rm Makefile

# clean up files only needed for configuring
workclean:
	- rm aclocal.m4
	- rm -Rf autom4te.cache
	- rm config.guess
	- rm config.log
	- rm config.status
	- rm config.sub
	- rm install-sh
	- rm configure

# clean up object files etc
clean:
	- rm -Rf $(BUILD)/*
	- rm lib/*
	- rm test/*
	- rm $(RADAU)/*.o
	- rm $(PARSER)/*.pyc $(PARSER)/parsetab.* $(PARSER)/parser.out
	- rm $(PARSER)/ply/*.pyc
	- rm doc/*.aux doc/*.bbl doc/*.blg doc/*.log doc/*.out

.PHONY: all clean workclean distclean doc lib test
.PRECIOUS: $(BUILD)/%.c %.model
