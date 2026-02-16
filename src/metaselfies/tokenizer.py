import re
from typing import Iterator, List, Pattern

from metaselfies.grammar import Grammar, TokenInstance, TokenType

TOKEN_RE: Pattern[str] = re.compile(pattern=r"\[[^\]]*\]|[^\[\]\s]")


def tokenize(text: str, grammar: Grammar) -> Iterator[List[TokenInstance]]:
    """
    Streaming tokenizer for MetaSELFIES-style strings.

    Parameters
    ----------
    text : str
        Input string containing bracket tokens and/or single symbols.
    grammar : Grammar
        Grammar definition.

    Yields
    ------
    list[TokenInstance]
        All valid interpretations of the next token.
        (Ambiguous tokens yield multiple TokenInstances.)
    """
    edge_lookup = {e.symbol: e for e in grammar.edges}
    node_lookup = {n.symbol: n for n in grammar.nodes}
    branch_lookup = {s.symbol: s for s in grammar.branches}
    link_lookup = {s.symbol: s for s in grammar.links}
    index_lookup = {s.symbol: s for s in grammar.index}
    modifier_lookup = {m.symbol: m for m in grammar.modifiers}

    edge_symbols = sorted(edge_lookup.keys(), key=len, reverse=True)
    modifier_symbols = sorted(modifier_lookup.keys(), key=len, reverse=True)
    base_symbols = sorted(
        list(node_lookup.keys())
        + list(branch_lookup.keys())
        + list(link_lookup.keys())
        + list(index_lookup.keys()),
        key=lambda x: len(x),
        reverse=True,
    )

    for raw_token in TOKEN_RE.findall(text):
        # --- Non-bracket symbol ---
        if not raw_token.startswith("["):
            yield [
                TokenInstance(
                    type=TokenType.UNKNOWN,
                    symbol=raw_token,
                    node=None,
                    edge=None,
                    modifiers=[],
                )
            ]
            continue

        # --- Bracketed token ---
        content = raw_token[1:-1]
        edge = None

        # 1. Extract edge prefix
        for es in edge_symbols:
            if content.startswith(es):
                edge = edge_lookup[es]
                content = content[len(es) :]
                break
        else:  # get default if defined
            edge = edge_lookup.get("*", None)

        interpretations: List[TokenInstance] = []

        # 2. Try all base symbol matches
        for base in base_symbols:
            if not content.startswith(base):
                continue

            remainder = content[len(base) :]
            mods = []
            rest = remainder

            # 3. Parse modifiers
            while rest:
                matched = False
                for ms in modifier_symbols:
                    if rest.startswith(ms):
                        mods.append(modifier_lookup[ms])
                        rest = rest[len(ms) :]
                        matched = True
                        break
                if not matched:
                    break

            if rest:
                continue  # invalid interpretation

            # 4. Determine token types
            if base in node_lookup:
                interpretations.append(
                    TokenInstance(
                        type=TokenType.NODE,
                        symbol=raw_token,
                        node=node_lookup[base],
                        edge=edge,
                        modifiers=mods,
                    )
                )

            if base in branch_lookup:
                interpretations.append(
                    TokenInstance(
                        type=TokenType.BRANCH,
                        symbol=raw_token,
                        node=branch_lookup[base],
                        edge=edge,
                        modifiers=mods,
                    )
                )

            if base in link_lookup:
                interpretations.append(
                    TokenInstance(
                        type=TokenType.LINK,
                        symbol=raw_token,
                        node=link_lookup[base],
                        edge=edge,
                        modifiers=mods,
                    )
                )

            # index tokens need to include edge symbol
            if edge and (edge.symbol != "*"):
                edge_sym = edge.symbol
            else:
                edge_sym = ""
            index_base = edge_sym + base
            if index_base in index_lookup:
                interpretations.append(
                    TokenInstance(
                        type=TokenType.INDEX,
                        symbol=raw_token,
                        node=index_lookup[index_base],
                        edge=edge,
                        modifiers=mods,
                    )
                )

            break  # break to prevent duplicate matches

        # 5. Yield interpretations
        if interpretations:
            yield interpretations
        else:
            yield [
                TokenInstance(
                    type=TokenType.UNKNOWN,
                    symbol=raw_token,
                    node=None,
                    edge=edge,
                    modifiers=[],
                )
            ]
