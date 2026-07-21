import sys
from pathlib import Path

debug_dir = Path("debug")
debug_dir.mkdir(exist_ok=True)
out_dir = Path("out")
out_dir.mkdir(exist_ok=True)

input_file = str(input("Input file: "))
sys.stdin = open(r"./out/" + input_file + '.sol', 'r')
output_file = open(r"./debug/checker.reg",'w')

def read_word_set(is_accepting: bool):
    S = [  ]
    S_size = int(input())
    assert S_size > 0, f"Block A has an impossible size." if is_accepting else f"Block R has an impossible size."
    for k in range(0,S_size):
        line = input().split()
        assert len(line) > 0, f"Word {k} of block A has an impossible size." if is_accepting else f"Word {k} of block R has an impossible size."
        S.append( [ int(a) for a in line ] )
        for i in range(len(S[k])):
            assert S[k][i] == -1 or S[k][i] == 0 or S[k][i] == 1, f"Word {k} of block A has a non-ternary character in position {i}." if is_accepting else f"Word {k} of block R has a non-ternary character in position {i}."
    return S

def read_automaton(n: int):
    DELTA, FINAL = [ [0]*n for _ in range(-1,2) ], [0]*n
    for i in range(n):
        line = input().split()
        DELTA[0][i] = int(line[0])
        DELTA[1][i] = int(line[1])
        DELTA[2][i] = int(line[2])
        FINAL[i] = int(line[3])
        for a in range(0,3):
            assert DELTA[a][i] >= 0 and DELTA[a][i] < n, f"Delta({a},{i}) is not well defined."
        assert FINAL[i] == 0 or FINAL[i] == 1, f"Alpha({i}) is not well defined."
    return DELTA, FINAL

A = read_word_set(True)
R = read_word_set(False)
M = len(A) + len(R)

n = int(input())

(DELTA, FINAL) = read_automaton(n)

def transition(w: list):
    print(f"Transition of {w}:", file=output_file)
    state = 0
    print(f"\t0",end="", file=output_file)
    for a in w:
        state = DELTA[a+1][state]
        print(f" -> {state}",end="", file=output_file)
    print("", file=output_file)
    return state
def is_accepting(w: list):
    p = FINAL[transition(w)]
    return True if p == 1 else False if p == 0 else None

success_index = int(input())

count_guesses = 0
for k in range(0,len(A)):
    flag = is_accepting(A[k])
    count_guesses += flag
    print(f"\tWord {k} of set A has been","correctly accepted." if flag else "wrongly rejected.", file=output_file)
for k in range(0,len(R)):
    flag = not is_accepting(R[k])
    count_guesses += flag
    print(f"\tWord {k} of set R has been","correctly rejected." if flag else "wrongly accepted.", file=output_file)

print("\n----------------------------------------------------------", file=output_file)
if count_guesses == success_index:
    print("The automaton guesses EXACTLY the # of words expected.", file=output_file)
    print(f"                       {count_guesses}  =  {success_index}                      ", file=output_file)
    print(1)
elif count_guesses < success_index:
    print("The automaton guesses LESS words than expected.", file=output_file)
    print(f"                       {count_guesses}  <  {success_index}                      ", file=output_file)
    print(-0)
elif count_guesses > success_index:
    print("The automaton guesses MORE words than expected.", file=output_file)
    print(f"                       {count_guesses}  >  {success_index}                      ", file=output_file)
    print(+0)
print("----------------------------------------------------------", file=output_file)

output_file.close()