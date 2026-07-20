import sys
import copy
from pysat.solvers import *
from pysat.formula import CNF, IDPool
from pysat.card import *
import time
from pathlib import Path

from common import common_functions as cf
from common import problem_manager as pm

debug_dir = Path("debug")
debug_dir.mkdir(exist_ok=True)
out_dir = Path("out")
out_dir.mkdir(exist_ok=True)
register_dir = Path("register")
register_dir.mkdir(exist_ok=True)


# ASK THE USER THE PARAMETERS OF THE PROBLEM AN STORE THEM

(instance, date_instance, stock_values, n, length, words_file,
        M, U, V, MGL, LGL, solver_to_use, n_diags) = pm.input_reader()
I_final = 3*n*n
I_tree = I_final + n


# DEFINE THE FUNCTIONS NEEDED TO EXPRESS THE LITERALS AND CONSTRAINTS OF THE PROBLEM

def delta(a: int, i: int, j: int):
    if -1 > a or a >= 2 or 0 > i or i >= n or 0 > j or j >= n:
        sys.exit("Invalid usage of \'delta\'")
    return (a+1)*n*n + i*n + j + 1

def final(i: int):
    if 0 > i or i >= n:
        sys.exit("Invalid usage of \'final\'")
    return I_final + i + 1

def node_index(node: cf.TernaryNode, j: int):
    return I_tree + node.ordinal*n + j + 1

def resulting_state(T: cf.TernaryTree, w: int, j: int):
    if 0 > j or j >= n:
        sys.exit("Invalid usage of \'resulting_state\'")
    return I_tree + T.get_ordinal(w)*n + j + 1

START = time.time()

# PREPARE THE VARIABLES FOR THE LOOP AND START THE ITERATIVE SEARCH OF SOLUTIONS

problem_file = open(r"./register/" + date_instance + ".reg","w")
best_guessing_rate = M - 1
for d in range(n_diags):
    for i_u in range(max(0,d-len(V)+1),min(len(U)-1, d) + 1):
        u = U[i_u]
        v = V[d - i_u]
        t0 = time.time()
        print(f"------------------------------------------------------------------------\nSolving for values (u,v)= ({u},{v}).")

        # DISCRETIZE THE WORDS OF THE LISTS ACCORDING TO THE VALUES OF u AND v AND PRINT THEM IN THE CORRESPONDIG FILE

        (A,R) = cf.discretize(MGL,LGL,u,v)
        M_A = len(A)
        M_R = len(R)
        M_T = M_A + M_R
        print("------------------------------------------------------------------------", file=problem_file)
        print(f"Problem ( u= {u} , v= {v} ):\n", file=problem_file)
        cf.print_word_set(A,True,False,problem_file)
        cf.print_word_set(R,False,False,problem_file)

        # BUILD THE TERNARY TREE OF THE PROBLEM

        T = cf.TernaryTree()
        clauses_file = open(r"./debug/clauses_file.txt","w")
        for w in A:
            T.insert_word(w)
        for w in R:
            T.insert_word(w)
        if len(U) == 1 and len(V) == 1: T.plot()

        # DEFINE EVEN MORE FUNCTIONS TO EXPRESS LITERALS AND CONSTRAINTS

        I_guessstates = I_tree + T.next_ordinal*n
        I_guesslits = I_guessstates + M_T*n
        n_vars = I_guesslits + M_T

        def A_guessing_state(k: int, i: int):
            if 0 > k or k >= M or 0 > i or i >= n:
                sys.exit("Invalid usage of \'A_guessing_state\'")
            return I_guessstates + k*n + i + 1

        def R_guessing_state(k: int, i: int):
            if 0 > k or k >= M or 0 > i or i >= n:
                sys.exit("Invalid usage of \'R_guessing_state\'")
            return I_guessstates + M_A*n + k*n + i + 1

        def correctly_accepted(k: int):
            if 0 > k or k >= M:
                sys.exit("Invalid usage of \'correctly_accepted\'")
            return I_guesslits + k + 1

        def correctly_rejected(k: int):
            if 0 > k or k >= M:
                sys.exit("Invalid usage of \'correctly_rejected\'")
            return I_guesslits + M_A + k + 1

        unguessing_lits = [ -correctly_accepted(k) for k in range(M_A) ] + [ -correctly_rejected(k) for k in range(M_R) ]

        # SHOW ALL THE VARIABLES DEFINED UNTIL NOW

        def print_tree_variables(node: cf.TernaryNode, output_file):
            first_child = node_index(node.negone,0) if node.negone else None
            second_child = node_index(node.zero,0) if node.zero else None
            third_child = node_index(node.one,0) if node.one else None
            print(f"The node {node.ordinal} has variables {[ node_index(node,i) for i in range(n) ]} and children {first_child}, {second_child} and {third_child}.", file=output_file)
            if node.negone:
                print_tree_variables(node.negone, output_file)
            if node.zero:
                print_tree_variables(node.zero, output_file)
            if node.one:
                print_tree_variables(node.one, output_file)

        print("Variables for delta:", file=clauses_file)
        for i in range(n):
            print( [ [ delta(a,i,j) for j in range(n) ] for a in range(-1,2) ], file=clauses_file)
        print("Variables for final:", file=clauses_file)
        print( [ final(i) for i in range(n) ], file=clauses_file)
        print(f"-------- # of variables used up to this point: {I_tree} --------", file= clauses_file)
        print("Variables for the tree nodes:", file=clauses_file)
        print_tree_variables(T.root,clauses_file)
        print(f"-------- # of variables used up to this point: {I_guessstates} --------", file= clauses_file)
        for k in range(M_A):
            print(f"For the guessing states of the {k}{cf.ordinal_suffix(k)} word of A:",[ A_guessing_state(k,i) for i in range(n) ], file= clauses_file)
        for k in range(M_R):
            print(f"For the guessing states of the {k}{cf.ordinal_suffix(k)} word of R:",[ R_guessing_state(k,i) for i in range(n) ], file= clauses_file)
        print(f"-------- # of variables used up to this point: {I_guesslits} --------", file= clauses_file)
        for k in range(M_A):
            print(f"To guess the {k}{cf.ordinal_suffix(k)} word of A:",[correctly_accepted(k)], file= clauses_file)
        for k in range(M_R):
            print(f"To guess the {k}{cf.ordinal_suffix(k)} word of R:",[correctly_rejected(k)], file= clauses_file)

        # DECLARE THE PROBLEM AND THE POOL OF AUXILIARY VARIABLES AND DEFINE HELPFUL FUNCTIONS

        problem = CNF()
        pool = IDPool(start_from=n_vars+1)

        def add_traversing_constraints(T: cf.TernaryTree, node: cf.TernaryNode):
            clauses = CardEnc.equals( lits=[ node_index(node,j) for j in range(n) ], vpool=pool, bound=1 ).clauses
            print(f"Clauses for EaU of the {node.ordinal}{cf.ordinal_suffix(node.ordinal)} node of T:\n",clauses, file=clauses_file)
            problem.extend( clauses )
            for a in range(-1,2):
                next_node = node.negone if a == -1 else node.zero if a == 0 else node.one
                if not next_node is None:
                    for i in range(n):
                        print(f"Clauses for the recursivity of delta from node {node.ordinal} to {next_node.ordinal}:", file=clauses_file)
                        for j in range(n):
                            print([ -node_index(node,i) , -delta(a,i,j) , node_index(next_node,j) ], file=clauses_file)
                            problem.append([ -node_index(node,i) , -delta(a,i,j) , node_index(next_node,j) ])
                    add_traversing_constraints(T,next_node)

        # ADD CONSTRAINTS THAT SIMULATE THE BEHAVIOUR OF THE AUTOMATON

        for a in range(-1,2):
            for i in range(n):
                clauses = CardEnc.equals( lits=[ delta(a,i,j) for j in range(n) ], vpool=pool, bound=1 ).clauses
                print(f"Clauses for EaU of delta({a},{i},·):\n", clauses, file=clauses_file)
                problem.extend( clauses )

        print("---------------------------------------------------------------------", file=clauses_file)
        print(f"Clause for starting at the root node ({T.root.ordinal}):\n",[ node_index(T.root,0) ], file=clauses_file)
        problem.append([ node_index(T.root,0) ])
        T.plot()
        add_traversing_constraints(T,T.root)

        for k in range(M_A):
            for i in range(n):
                clauses = [ [-resulting_state(T,A[k],i),-final(i),A_guessing_state(k,i)], [-A_guessing_state(k,i),resulting_state(T,A[k],i)], [-A_guessing_state(k,i),final(i)] ]
                print(f"Definition of A_guessing_state({k},{i}):",clauses, file=clauses_file)
                problem.extend( clauses )
            clauses = [ [-A_guessing_state(k,i),correctly_accepted(k)] for i in range(n) ] + [ [-correctly_accepted(k)] + [A_guessing_state(k,i) for i in range(n)] ]
            print(f"Definition of correctly_accepted({k}):",clauses, file=clauses_file)
            problem.extend( clauses )
        for k in range(M_R):
            for i in range(n):
                clauses = [ [-resulting_state(T,R[k],i),final(i),R_guessing_state(k,i)], [-R_guessing_state(k,i),resulting_state(T,R[k],i)], [-R_guessing_state(k,i),-final(i)] ]
                print(f"Definition of R_guessing_state({k},{i}):",clauses, file=clauses_file)
                problem.extend( clauses )
            clauses = [ [-R_guessing_state(k,i),correctly_rejected(k)] for i in range(n) ] + [ [-correctly_rejected(k)] + [R_guessing_state(k,i) for i in range(n)] ]
            print(f"Definition of correctly_rejected({k}):",clauses, file=clauses_file)
            problem.extend( clauses )

        # ADD REDUNDANT CLAUSES TO HELP THE SOLVER PROPAGATE

        for k in range(M_A):
            for l in range(k+1,M_A):
                if A[l] == A[k]:
                    clauses = [ [ -correctly_accepted(k) , correctly_accepted(l) ] , [ correctly_accepted(k) , -correctly_accepted(l) ] ]
                    print(f"Redundant equivalence between words A[{k}] and A[{l}]:",clauses, file=clauses_file)
                    problem.extend( clauses )
                    for i in range(n):
                        clauses = [ [ -A_guessing_state(k,i) , A_guessing_state(l,i) ] , [ A_guessing_state(k,i) , -A_guessing_state(l,i) ] ]
                        print(f"Redundant equivalence between A_guessing_states({k},{i}) and A_guessing_states({l},{i}):",clauses, file=clauses_file)
                        problem.extend( clauses )
        for k in range(M_R):
            for l in range(k+1,M_R):
                if R[l] == R[k]:
                    clauses = [ [ -correctly_rejected(k) , correctly_rejected(l) ] , [ correctly_rejected(k) , -correctly_rejected(l) ] ]
                    print(f"Redundant equivalence between words R[{k}] and R[{l}]:",clauses, file=clauses_file)
                    problem.extend( clauses )
                    for i in range(n):
                        clauses = [ [ -R_guessing_state(k,i) , R_guessing_state(l,i) ] , [ R_guessing_state(k,i) , -R_guessing_state(l,i) ] ]
                        print(f"Redundant equivalence between R_guessing_states({k},{i}) and R_guessing_states({l},{i}):",clauses, file=clauses_file)
                        problem.extend( clauses )

        # TRY TO SOLVE THE PROBLEM AND PRINT THE RESULTING GUESSING INDEX

        still_solvable = True
        SOL = None
        solution_found = False
        guessing_rate = best_guessing_rate + 1
        t = ITotalizer( lits=unguessing_lits, ubound=(M+M), top_id=problem.atoms()[-1] )
        problem.extend( t.cnf.clauses )
        problem.append( [-t.rhs[-guessing_rate]] )
        attempts_count= 0
        if solver_to_use != "Kissat404": s = Solver(name= "cadical300", bootstrap_with=problem.clauses)
        while still_solvable and attempts_count < M + 1:
            if solver_to_use == "Kissat404": s = Solver(name= "Kissat404", bootstrap_with=problem.clauses)
            attempts_count += 1
            print(f"\tSearching for solutions with guessing_rate >= {guessing_rate}.")
            print(f"\tSearching for solutions with guessing_rate >= {guessing_rate}.", file=problem_file)
            still_solvable = s.solve()
            print("\t\tResult:\t","SAT" if still_solvable else "UNSAT")
            print("\t\tResult:\t","SAT" if still_solvable else "UNSAT", file=problem_file)
            if still_solvable:
                solution_found = True
                SOL = s.get_model().copy()
                guessing_rate = 0
                for k in range(M_T):
                    if SOL[I_guesslits+k] > 0:
                        guessing_rate += 1
                print(f"\t\tNew guessing_rate obtainded: {guessing_rate} / {M+M}")
                if guessing_rate < (M+M):
                    guessing_rate += 1
                    s.add_clause( [-t.rhs[-guessing_rate]] ) if solver_to_use != "Kissat404" else problem.append( [-t.rhs[-guessing_rate]] )
                elif guessing_rate == (M+M):
                    break
            else:
                guessing_rate -= 1
            if solver_to_use == "Kissat404": s.delete()
        if solver_to_use != "Kissat404": s.delete()
        t.delete()
        if solution_found:
            print(f"Max guessing_rate for (u,v)= ({u},{v}):           \t{guessing_rate} / {M+M}")
            print(f"Max guessing_rate for (u,v)= ({u},{v}):           \t{guessing_rate} / {M+M}", file=problem_file)

        # SHOW THE TIME NEEDED TO SOLVE THE PROBLEM WITH THESE VALUES OF (u,v)

        tf = time.time()
        dtime = tf - t0
        print(f"Time needed to solve the problem with (u,v)= ({u},{v}):\t{dtime}")
        print(f"Time needed to solve the problem with (u,v)= ({u},{v}):\t{dtime}", file=problem_file)

        # STORE THE OPTIMAL AUTOMATON FOUND FOR THIS VALUES OF (u,v) AND SHOW IT

        if solution_found: 
            (DELTAn1, DELTA0, DELTA1, FINAL) = cf.read_solution(SOL,n,I_final,I_tree)
            print(f"Best solution found for the problem with (u,v)= ({u},{v}):", file=problem_file)
            cf.print_solution(n,DELTAn1,DELTA0,DELTA1,FINAL,problem_file)

        # COMPARE THE SOLUTION TO THE ONES FOUND PREVIOUSLY

        if guessing_rate > best_guessing_rate:
            best_guessing_rate = guessing_rate
            best_u, best_v = u, v
            best_A = copy.deepcopy(A)
            best_R = copy.deepcopy(R)
            BEST_SOL = SOL.copy()

        if best_guessing_rate >= M+M:
            break

    if best_guessing_rate >= M+M:
            break


# SHOW THE RESULTS OBTAINED THROUGH EACH OUTPUT

END = time.time()
TIME_SPENT = END - START

solution_file = open(r"./out/" + date_instance + ".sol","w")
(DELTAn1, DELTA0, DELTA1, FINAL) = cf.read_solution(BEST_SOL,n,I_final,I_tree)

pm.solution_plotter(best_A, best_R, n, DELTAn1, DELTA0, DELTA1, FINAL, best_u, best_v, best_guessing_rate,
                    M, solver_to_use, TIME_SPENT, problem_file, solution_file, instance)


# CLOSE ALL FILES

problem_file.close()
words_file.close()
solution_file.close()
clauses_file.close()


# ✓ 1. PBlib
# ✓  - Juntar palabras
# ✗  - Implementar pseudobool (with incremental interface)
#   2. Més exemples (kissat vs Cadical vs los demás)
# ✓ 3. Unificar todos los programas y modularizar el código
# ✗ 4. Implementar checker
# ✓ 5. Mostrar autómata gráficamente