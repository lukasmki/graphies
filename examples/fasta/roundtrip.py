from pathlib import Path
import graphies as gf

grammar = gf.Grammar.from_file(path=Path(__file__).parent.resolve()/"fasta.json")


def encode_fasta(string: str):
    return "".join([f"[{c}]" for c in string])

def decode_fasta(string: str):
    tokens = list(grammar.tokenize(string))
    ntokens = len(tokens)
    
    result, i = "", 0
    token = tokens[i][0]
    while token:
        # filter out link/index structure tokens
        if token.type == "LINK":
            i += token.node.value
        else:
            result += token.serialize().strip("[]")
        i += 1
        token = tokens[i][0] if i < ntokens else None
    return result

fasta = "TVKIGGQLKEALLDTGADDTVLEDINLPGKWKPKMIGGIGGFIKVKQYDQILIEICGKKAIGTVLVGPTPVNIIGRNMLTQIGCTLNFPISPIETVPVKLKPGMDGPKVKQWPLTEEKIKALTEICIXMEKEGKISKIGPENPYNTPIFAIKKKDSTKWRKLVDFRELNKRTQDFWEVQLGIPHPAGLKKKXSVTVLDVGDAYFSVPLDEDFRKYTAFTIPSTNNETPGIRYQYNVLPQGWKGSPAIFQSSMTKILEPFRSKNPEIIIYQYMDDLYVGSDLXIGQHRXKXEELRGHLLSWGFTTPDKKHQKEPPFLWMG"

print("FASTA", fasta)
fasta_tokens = encode_fasta(fasta)

graph = gf.decode(graphies=fasta_tokens, grammar=grammar)
print("GRAPH", graph)

# add a hydrogen bond contact between residue 0 and 100
graph.add_edge(0, 100, **{"symbol": "--", "weight": 0})

graphies = gf.encode(graph=graph, grammar=grammar)
print("GRAPHIES", graphies)

new_fasta = decode_fasta(graphies)
print("FASTA", new_fasta, fasta == new_fasta)