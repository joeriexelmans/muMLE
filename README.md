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

## Dependencies

 * Python 3.?
 * Python libraries:
    - Lark (for textual parsing)
    - Jinja2 (not a hard requirement, only for model-to-text transformation)


## Development

The following branches exist:

 * `mde2425` - the branch containing a snapshot of the repo used for the MDE assignments 24-25. No breaking changes will be pushed here. After the re-exams (Sep 2025), this branch will be frozen.
 * `master` - currently equivalent to `mde2425` (this is the branch that was cloned by the students). This branch will be deleted after Sep 2025, because the name is too vague.
 * `development` - in this branch, new development will occur, primarily cleaning up the code to prepare for next year's MDE classes.

