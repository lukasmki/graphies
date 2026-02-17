# metaselfies

> [!WARNING]
> Documentation in progress...

## Token Types

There are three types of tokens: Node tokens, Structure (Branch/Link) tokens, and Index tokens.

Both node and structure tokens can be augmented with a prefixed edge modifier, indicating the type or weight of the edge.
Node tokens can be further augmented with a set of modifiers.

1. Nodes - `{edge}{node}{modifiers}`
2. Rings - `{edge?}{structure}`
3. Branches - `{edge?}{structure}`
4. Index - `{index}`