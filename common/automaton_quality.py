
def transition(a: float, q: int, DELTAn1: list, DELTA0: list, DELTA1: list, u: float, v: float):

    if a < 1 - v:
        return DELTAn1[q]
    elif 1 - v <= a and a <= 1 + u:
        return DELTA0[q]
    elif a > 1 + u:
        return DELTA1[q]
    else:
        raise ValueError("Transition invalid.")

def run_atomata_on_stock(DELTAn1: list, DELTA0: list, DELTA1: list, FINAL: list, stock_values: list, u: float, v: float):

    q = 0
    positives_guessed = 0
    negatives_tanked = 0

    for k in range(1,len(stock_values)):
        
        a = stock_values[k]/stock_values[k-1]
        q = transition(a, q, DELTAn1, DELTA0, DELTA1, u, v)

        if k + 365 >= len(stock_values):
            if FINAL[q] == 1:
                print("Bet taken.\n\tResult:", end="")
                if a > 1:
                    positives_guessed += 1
                    print("✓")
                elif a < 1:
                    negatives_tanked += 1
                    print("✗")
                else:
                    print("-")

    return positives_guessed, negatives_tanked