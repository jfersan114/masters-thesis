from . import common_functions as cf
from datetime import datetime, timezone

def settings_reader():

    # ASK FOR THE SETTINGS FILE
    settings_file = open(r"./settings.set")

    # LIST THE AVAILABLE SOLVERS AND INITIALIZE default_mode TO False
    SOLVERS = {"Cadical300", "Glucose421", "cryptominisat5", "Kissat404", "minisat22", "minicard"}
    default_mode = False

    # LOOK FOR THE DEFAULT MODE SETTING
    for line in settings_file:
        if line.startswith("Default mode:"):
            default_mode = cf.str_to_bool( line.split()[-1] )

    # IF False, LOOK FOR THE REST OF THE SETTINGS
    if not default_mode:
        settings_file = open(r"./settings.set")
        for line in settings_file:
            if line.startswith("n:"):
                n = int(line.split()[-1])
            elif line.startswith("length:"):
                length = int( line.split()[-1] )
                if length < 4:
                    raise ValueError("Length needs to be >= 4.")
            elif line.startswith("M_type:"):
                M_type = line.split()[-1]
                if M_type == "fixed": M_type = "f"
                if M_type == "percentual": M_type = "p"
                if M_type != "f" and M_type != "p":
                    raise ValueError("Wrong format for the parameter M_type.")
            elif line.startswith("M:"):
                M = int( line.split()[-1] )
                if M < 1:
                    raise ValueError("M needs to be >= 2.")
            elif line.startswith("Are u,v fixed:"):
                are_u_v_fixed = cf.str_to_bool( line.split()[-1] )
            elif line.startswith("Solver to use:"):
                solver_to_use = line.split()[-1]
                if solver_to_use not in SOLVERS:
                    raise ValueError("Unrecognized/unsupported solver.")

    # ESTABLISH DEFAULT VALUES OTHERWISE
    else:
        n = 5
        length = 7
        M_type = "f"
        M = 20
        are_u_v_fixed = True
        p_diags = None
        u = v = 0.02
        solver_to_use = "Cadical300"

    # IF u,v ARE NOT FIXED, SET THEIR VALUES TO None AND LOOK FOR THE % OF VALUES THAT SHOULD BE TRAVERSED
    if not default_mode and not are_u_v_fixed:
        u = v = None
        settings_file = open(r"./settings.set")
        for line in settings_file:
            if line.startswith(r"% of diagonals:"):
                p_diags = float( line.split()[-1] )
                if p_diags < 0 or p_diags > 100:
                    raise ValueError("We need 0 <= p_diags <= 100.")

    
    # LOOK FOR u,v IF NEEDED.
    if not default_mode and are_u_v_fixed:
        settings_file = open(r"./settings.set")
        for line in settings_file:
            if line.startswith("u:"):
                u = float( line.split()[-1] )
                if u <= 0:
                    raise ValueError("We need 0 < u.")
            elif line.startswith("v:"):
                v = float( line.split()[-1] )
                if v <= 0 or 1 <= v:
                    raise ValueError("We need 0 < v < 1.")

    settings_file.close()
    
    return default_mode, n, length, M_type, M, are_u_v_fixed, p_diags, u, v, solver_to_use


def input_reader():

    # READ THE SETTINGS FILE SPECIFIED BY THE USER
    (default_mode, n, length, M_type, M, are_u_v_fixed, p_diags, u, v, solver_to_use) = settings_reader()

    # OPEN THE FILE CONTAINING THE VALUES OF THE STOCK AND STORE THEM
    instance = input("Input file? (from \'instances\' folder) ")
    input_file = open(r"./instances/" + instance + ".std")
    stock_values = cf.read_stock(input_file)
    input_file.close()

    # COMPUTE THE TOTAL AMOUNT OF EXISTING SUBWORDS OF THE STOCK
    words_file = open(r"./debug/words_file.txt","w")
    N_subwords = cf.subwords_lister(stock_values,length,words_file)
    print(f"Total # of subwords: {N_subwords}", file=words_file)

    # INTERPRET M AS A PERCENTAGE
    if M_type == "p":
        M = N_subwords*M//200

    # CHECK THAT M IS VALID AND RECTIFY IF IN DEBUG MODE
    if M+M > N_subwords and not default_mode:
        raise ValueError("The amount of words to analyze exceeds the total amount of subwords of the list of values of the stock.")
    elif M+M > N_subwords and default_mode:
        M = N_subwords//2

    # BUILD THE LISTS OF MOST AND LEAST GROWING WORDS AND FIND THE MEANINGFUL COEFICIENTS
    (MGL, LGL, coeficients) = cf.most_meaningful_words(M,stock_values,length)
    cf.print_list_of_subwords(MGL,words_file,True)
    cf.print_list_of_subwords(LGL,words_file,False)

    # ASK IF u,v WILL HAVE A FIXED VALUE AND BUILD U,V ACCORDINGLY
    (U,V) = cf.region_representatives(coeficients)
    if are_u_v_fixed:
        (U,V) = ([u],[v])

    # IF u,v ARE NOT FIXED, COMPUTE THE # OF DIAGONALS TO CHECK
    if not are_u_v_fixed:
        n_diags = (len(U) + len(V) - 1)*p_diags/100
    else:
        n_diags = len(U) + len(V) - 1

    # GIVE NAME TO THE REG FILE
    date_instance = instance + " " + solver_to_use + " " + str(datetime.now(timezone.utc))[:19]

    return instance, date_instance, stock_values, n, length, words_file, M, U, V, MGL, LGL, solver_to_use, n_diags


def solution_plotter(A: list, R: list, n: int, DELTAn1: list, DELTA0: list, DELTA1: list, ALPHA: list, best_u: float, best_v: float,
                     best_guessing_index: int, M: int, solver_to_use: str, TIME_SPENT: float, problem_file, solution_file, automaton_file: str ="automaton_graph"):
    
    # to solution_file
    cf.print_word_set(A,True,True,solution_file)
    cf.print_word_set(R,False,True,solution_file)
    print(n,file=solution_file)
    cf.print_solution(n,DELTAn1,DELTA0,DELTA1,ALPHA,solution_file)
    print(best_guessing_index,file=solution_file)
    print(TIME_SPENT,file=solution_file)

    # to stdout
    print( "------------------------------------------------------------------------")
    print(f"BEST SOLUTION FOUND:")
    print(f"(u,v) = ({best_u},{best_v}):")
    print(f"With best guessing rate: {best_guessing_index} / {M+M}")
    print("AUTOMATON:")
    cf.print_solution(n,DELTAn1,DELTA0,DELTA1,ALPHA,None)
    print( "------------------------------------------------------------------------")
    print( "Total time spent solving the problem:\t",TIME_SPENT)
    print( "Solver used:                         \t",solver_to_use,"w/o PBlib")

    # to problem_file
    print( "------------------------------------------------------------------------", file=problem_file)
    print(f"BEST SOLUTION FOUND:",file=problem_file)
    print(f"(u,v) = ({best_u},{best_v}):",file=problem_file)
    print(f"With best guessing rate: {best_guessing_index} / {M+M}",file=problem_file)
    print("AUTOMATON:",file=problem_file)
    cf.print_solution(n,DELTAn1,DELTA0,DELTA1,ALPHA,problem_file)
    print( "------------------------------------------------------------------------", file=problem_file)
    print( "Total time spent solving the problem:\t",TIME_SPENT,  file=problem_file)
    print( "Solver used:                         \t",solver_to_use,"w/o PBlib", file=problem_file)

    # as a graph
    cf.plot_automaton(n,DELTAn1,DELTA0,DELTA1,ALPHA,automaton_file)