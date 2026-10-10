
def transition(a: float, q: int, DELTAn1: list, DELTA0: list, DELTA1: list, u: float, v: float):

    if a < 1 - v:
        return DELTAn1[q]
    elif 1 - v <= a and a <= 1 + u:
        return DELTA0[q]
    elif a > 1 + u:
        return DELTA1[q]
    else:
        raise ValueError("Transition invalid.")

def run_atomata_on_stock(DELTAn1: list, DELTA0: list, DELTA1: list, FINAL: list, stock_values: list, u: float, v: float, length: int):

    positives_guessed = 0
    negatives_tanked = 0
    real_length = length - 2

    for k in range(1,len(stock_values)-real_length):
        if k + 365 + real_length >= len(stock_values):
            q = 0
            for i in range(real_length):
                a = stock_values[k+i]/stock_values[k+i-1]
                q = transition(a, q, DELTAn1, DELTA0, DELTA1, u, v)
            if FINAL[q] == 1:
                print("Bet taken.\n\tResult:", end="")
                if a > 1:
                    positives_guessed += 1
                elif a <= 1:
                    negatives_tanked += 1

    return positives_guessed, negatives_tanked