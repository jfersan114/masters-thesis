import copy
import heapq
import sys
from graphviz import Digraph


# FUNCTION THAT INTERPRETS AN INPUT AS A BOOLEAN CORRECTLY

def str_to_bool(w: str):
    if w == "True" or w == "true" or w == "T" or w == "t" or w == "1":
        return True
    elif w == "False" or w == "false" or w == "F" or w == "f" or w == "0" or w == "--":
        return False
    else:
        raise ValueError("Input uninterpretable as a boolean.")


# FUCTION THAT RETURNS THE SUFFIX OF AN ORDINAL NUMBER (the most important function in the whole project) (ever) (Y si no entendéis por qué, leedos el Quijote primero.)

def ordinal_suffix(k: int):
    return "-st" if k%10 == 1 and (k//10)%10 != 1 else "-nd" if k%10 == 2 and (k//10)%10 != 1 else "-rd" if k%10 == 3 and (k//10)%10 != 1 else "-th"


# CLASSES NEEDED TO MANAGE TERNARY TREES

class TernaryNode:
    def __init__(self, ordinal: int):
        self.ordinal = ordinal
        self.negone = None
        self.zero = None
        self.one = None

    def print(self, indentation: str):
        print(indentation,self.ordinal,end='')
        if not self.negone:
            print("") 
        else:
            self.negone.print("\t")
        if not self.zero:
            print("") 
        else:
            self.zero.print(indentation + "\t")
        if not self.one:
            print("") 
        else:
            self.one.print(indentation + "\t")

    def print_in_file(self, indentation: str, output_file):
        print(indentation,self.ordinal,end='', file=output_file)
        if not self.negone:
            print("", file=output_file) 
        else:
            self.negone.print_in_file("\t",output_file)
        if not self.zero:
            print("", file=output_file) 
        else:
            self.zero.print_in_file(indentation + "\t",output_file)
        if not self.one:
            print("", file=output_file) 
        else:
            self.one.print_in_file(indentation + "\t",output_file)
    
    def subtree_print(self):
        self.print("")

    def subtree_print_in_file(self, output_file):
        self.print_in_file("",output_file)

class TernaryTree:
    def __init__(self):
        self.root = TernaryNode(0)
        self.next_ordinal = 1

    def insert_word(self, w: list):
        current_node = self.root
        for a in w:
            if a == -1:
                if not current_node.negone:
                    current_node.negone = TernaryNode(self.next_ordinal)
                    self.next_ordinal += 1
                current_node = current_node.negone
            elif a == 0:
                if not current_node.zero:
                    current_node.zero = TernaryNode(self.next_ordinal)
                    self.next_ordinal += 1
                current_node = current_node.zero
            elif a == 1:
                if not current_node.one:
                    current_node.one = TernaryNode(self.next_ordinal)
                    self.next_ordinal += 1
                current_node = current_node.one
            else:
                raise ValueError("Some word is not ternary.")

    def get_ordinal(self, w: list):
        current_node = self.root

        for a in w:
            if a == -1:
                if not current_node.negone:
                    raise ValueError("No (-1)-child at position {i} in word.")
                current_node = current_node.negone
            elif a == 0:
                if not current_node.zero:
                    raise ValueError("No 0-child at position {i} in word.")
                current_node = current_node.zero
            elif a == 1:
                if not current_node.one:
                    raise ValueError("No 1-child at position {i} in word.")
                current_node = current_node.one
            else:
                raise ValueError("Some bit is not ternary: {i}")

        return current_node.ordinal

    def print(self):
        self.root.subtree_print()

    def print_in_file(self, output_file):
        self.root.subtree_print_in_file(output_file)

    def plot(self, filename="tree_graph"):
        dot = Digraph()

        dot.attr(rankdir="LR")

        def add_nodes(node):
            if node is None:
                return

            # Add current node
            dot.node(str(node.ordinal), str(node.ordinal))

            # Add edges + recurse
            if node.negone:
                dot.edge(str(node.ordinal),
                         str(node.negone.ordinal),
                         label="-1")
                add_nodes(node.negone)

            if node.zero:
                dot.edge(str(node.ordinal),
                         str(node.zero.ordinal),
                         label="0")
                add_nodes(node.zero)

            if node.one:
                dot.edge(str(node.ordinal),
                         str(node.one.ordinal),
                         label="1")
                add_nodes(node.one)

        add_nodes(self.root)

        dot.render(
            filename=r"./debug/" + filename,
            format="png",
            cleanup=True
        )


# FUNCTIONS USED TO READ AND STORE THE VALUES OF A GIVEN STOCK

def read_stock(input_file):
    stock_values = []
    for line in input_file:
        line = line.split()
        if line:
            price = float(line[-1])
            if price > 0:
                stock_values.append(price)
            else:
                raise ValueError("Prices should be strictly positive real numbers.")
    return stock_values

def subwords_lister(word: list, length: int, output_file):
    N_subwords = 0
    for i in range(0,len(word)-length+1):
        print(str(word[i:i+length]), word[i:i+length][-1]/word[i:i+length][-2], file=output_file)
        N_subwords += 1
    print(f"# of subwords of size {length}: {N_subwords}", file=output_file)
    return N_subwords


# FUNCTIONS USED TO PRINT SETS OF WORDS AND MANAGE SOLUTIONS

def print_word_set(S: list, accepting_set: bool, legacy_mode: bool, output_file=None):
    if legacy_mode:
        print(len(S), file=output_file)
        for k in range(0,len(S)):
            for i in range(0,len(S[k])):
                print(str(S[k][i]) + " ",end="", file=output_file)
            print("", file=output_file)
    else:
        print("A:" if accepting_set else "R:", file=output_file)
        for k in range(0,len(S)):
            print(S[k], file=output_file)
        print("", file=output_file)

def print_word_multiset(S: list, S_weights: list, accepting_set: bool, output_file=None):
    print("A:" if accepting_set else "R:", file=output_file)
    for k in range(0,len(S)):
        print(f"{S[k]} x {S_weights[k]}", file=output_file)
    print("", file=output_file)

def print_list_of_subwords(L: list, output_file, words_are_positive: bool):
    print("------------------------------------------------------------------------", file=output_file)
    if words_are_positive:
        print("MOST GROWING LIST:", file=output_file)
    else:
        print("LEAST GROWING LIST:", file=output_file)
    print("------------------------------------------------------------------------", file=output_file)
    for k in range(len(L)):
        print(str(L[k]) + " ", end=" ", file=output_file)
        if L[k] != 0:
            print(str(L[k][-1]/L[k][-2]), end=" ", file=output_file)
        print("", file=output_file)

def read_solution(SOL: list, n: int, I_final: int, I_tree: int):
    DELTAn1, DELTA0, DELTA1, FINAL = [0]*n, [0]*n, [0]*n, [0]*n
    for k in range(1,I_tree+1):
        lit = SOL[k]
        if 0<lit and lit<=n*n:
            i = (lit-1) // n
            j = (lit-1) % n
            DELTAn1[i] = j
        elif n*n<lit and lit<=2*n*n:
            i = (lit-n*n-1) // n
            j = (lit-n*n-1) % n
            DELTA0[i] = j
        elif 2*n*n<lit and lit<=I_final:
            i = (lit-2*n*n-1) // n
            j = (lit-2*n*n-1) % n
            DELTA1[i] = j
        elif 0<lit and I_final<lit and lit<=I_tree:
            FINAL[lit-I_final-1] = 1
    return DELTAn1, DELTA0, DELTA1, FINAL

def print_solution(n: int, DELTAn1: list, DELTA0: list, DELTA1: list, FINAL: list, output_file=None):
    for i in range(0,n):
        print(DELTAn1[i],DELTA0[i],DELTA1[i],FINAL[i], file=output_file)

def plot_automaton(n: int, DELTAn1: list, DELTA0: list, DELTA1: list, FINAL: list, output_file: str ="automaton_graph"):
    dot = Digraph("Automaton", format="png")
    dot.attr(rankdir="LR")
    dot.attr("node", shape="circle")
    dot.node("", shape="none")
    dot.edge("", str(0))
    for i in range(n):
        shape = "doublecircle" if FINAL[i] == 1 else "circle"
        dot.node(str(i), label=str(i), shape=shape)
    for i in range(n):
        dot.edge(str(i), str(DELTAn1[i]), label="-1")
        dot.edge(str(i), str(DELTA0[i]), label="0")
        dot.edge(str(i), str(DELTA1[i]), label="1")
    dot.render(r"./out/" + output_file, format="png", cleanup=True)
    return dot


# FUNCTIONS NEEDED TO CREATE THE LIST OF MEANINGFUL WORDS AND VALUES OF (u,v)

def most_meaningful_words(M: int, stock_values: list, length: int):

    heap_count = 0
    mgl_heap, lgl_heap = [], []

    for i in range(0,len(stock_values)-length+1):
        L = stock_values[i:i+length]
        ratio = L[-1]/L[-2]
        if heap_count < M:
            heapq.heappush( mgl_heap , (ratio,L[:-1]) )
            heapq.heappush( lgl_heap , (-ratio,L[:-1]) )
            heap_count += 1
        else:
            if ratio > mgl_heap[0][0]:
                heapq.heappushpop( mgl_heap , (ratio,L[:-1]) )
            if ratio < -lgl_heap[0][0]:
                heapq.heappushpop( lgl_heap , (-ratio,L[:-1]) )

    if mgl_heap[0][0] <= 1 and lgl_heap[0][0] >= 1:
        sys.exit("Could not obtain enough positive nor negative patterns")
    elif mgl_heap[0][0] <= 1 and lgl_heap[0][0] < 1:
        sys.exit("Could not obtain enough positive patterns")
    elif mgl_heap[0][0] > 1 and lgl_heap[0][0] >= 1:
        sys.exit("Could not obtain enough negative patterns")

    MGL, LGL = [], []
    for (_,L) in mgl_heap:
        MGL.append(L)
    for (_,L) in lgl_heap:
        LGL.append(L)

    coeficients = []
    for w in MGL:
        for i in range(1,length-1):
            coeficients.append( w[i]/w[i-1] )
    for w in LGL:
        for i in range(1,length-1):
            coeficients.append( w[i]/w[i-1] )

    return MGL, LGL, coeficients

def delete_duplicates(L: list):     # the list has to be previously sorted
    L_new = []
    for i in range(0,len(L)-1):
        if L[i] != L[i+1]:
            L_new.append(L[i])
        assert L[i] <= L[i+1], f"The list fed to \'delete_duplicates\' was not sorted in indexes {i}, {i+1}:\t{L[i]} >= {L[i+1]}"
    L_new.append(L[-1])
    return L_new

def middle_points(L: list):
    L_mp = []
    for i in range(0,len(L)-1):
        L_mp.append( (L[i+1]+L[i])/2 )
    return L_mp

def region_representatives(coeficients: list):
    L_u, L_v = [], []
    for c in coeficients:
        if c > 1:
            L_u.append(c-1)
        elif c < 1:
            L_v.append(1-c)
    L_u.sort()
    L_u = middle_points(delete_duplicates([0.0] + L_u + [(L_u[-1] + 0.1)]))
    L_v = middle_points(delete_duplicates([0.0] + sorted(L_v) + [1.0]))
    return L_u, L_v


# FUNCTION THAT DISCRETIZES A GIVEN LISTS OF SUBWORDS TO BALANCED TERNARY WITH THE GIVEN VALUES OF (u,v)

def discretize(L1: list, L2: list, u: float, v: float):
    A, R = [[] for _ in range(len(L1))], [[] for _ in range(len(L2))]
    for k in range(0,len(L1)):
        if len(L1[k]) < 2:
            raise ValueError("Some positive word has length too short to be discretized.")
        for i in range(0,len(L1[k])-1):
            if L1[k][i+1]/L1[k][i] > 1 + u:
                A[k].append(1)
            elif L1[k][i+1]/L1[k][i] < 1 - v:
                A[k].append(-1)
            else:
                A[k].append(0)
    for k in range(0,len(L2)):
        if len(L2[k]) < 2:
            raise ValueError("Some negative word has length too short to be discretized.")
        for i in range(0,len(L2[k])-1):
            if L2[k][i+1]/L2[k][i] > 1 + u:
                R[k].append(1)
            elif L2[k][i+1]/L2[k][i] < 1 - v:
                R[k].append(-1)
            else:
                R[k].append(0)
    return A, R

# FUNCTION THAT DELETES DUPLICATES IN A LIST

def unify_word_set(S_old: list):
    S = copy.deepcopy(S_old)
    weights = []
    k = 0
    S_size = len(S)
    while k < S_size:
        count = 1
        for l in range(S_size-1,k,-1):
            if S[l] == S[k]:
                count += 1
                del S[l]
                S_size -= 1
        weights.append(count)
        k += 1
    return S, weights

