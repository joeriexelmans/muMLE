# muMLE

Tiny (meta-)modeling framework.

Features:

 * mostly textual concrete syntax
 * meta-modeling & constraint writing
 * conformance checking
 * model transformation primitives (match and rewrite)
 * rule-based model transformation
 * examples included:
    - Class Diagrams (self-conforming)
    - Causal Block Diagrams language
    - Petri Net language
    - [Repotting the Geraniums](https://ris.utwente.nl/ws/portalfiles/portal/5312315/gtvmt2009.pdf)

## Dependencies

 * Python 3.?
 * Python libraries:
    - Lark (for textual parsing)
    - Jinja2 (not a hard requirement, only for model-to-text transformation)


## Development

The following branches exist:

 * `development` - in this branch, new development will occur, primarily cleaning up the code to prepare for next year's MDE classes.
 * `mde2425` - contains a snapshot of the repo used for the MDE assignments 24-25. This branch should remain frozen.


## Tutorial

A good place to learn how to use muMLE is the `tutorial` directory. Each file is an executable Python script that explains muMLE step-by-step (read the comments).
