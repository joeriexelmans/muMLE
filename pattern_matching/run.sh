#!/bin/sh

rm *.svg
rm *.dot
python main.py
# dot randomGraph.dot -Tsvg > randomGraph.svg
for filename in randomGraph-*.dot; do
  dot $filename -Tsvg > $filename.svg
done

firefox *.svg
