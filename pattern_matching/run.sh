#!/bin/sh

python main.py
dot randomGraph.dot -Tsvg > randomGraph.svg
dot randomPattern.dot -Tsvg > randomPattern.svg

firefox randomGraph.svg
firefox randomPattern.svg