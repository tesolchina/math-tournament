#!/usr/bin/env python3
"""
Solve the team round-robin tournament for n=34, m=17.
Uses Google OR-Tools CP-SAT solver.
Outputs solution_34.txt on success.
"""
from ortools.sat.python import cp_model
import time
import sys

n = 34
m = 17

def solve():
    print(f"Setting up CP-SAT model for n={n}, m={m}...", flush=True)
    t0 = time.time()
    
    model = cp_model.CpModel()
    
    # y[r][i][j] = 1 if A_i plays B_j in round r
    print("  Creating y variables...", flush=True)
    y = [[[model.NewBoolVar(f'y_{r}_{i}_{j}') for j in range(n)] 
          for i in range(n)] for r in range(n)]
    print(f"  y: {n*n*n} vars ({time.time()-t0:.1f}s)", flush=True)
    
    # f[r][i] = 1 if A_i goes first in round r
    f = [[model.NewBoolVar(f'f_{r}_{i}') for i in range(n)] for r in range(n)]
    print(f"  f: {n*n} vars ({time.time()-t0:.1f}s)", flush=True)
    
    # w[r][i][j] = y[r][i][j] AND f[r][i]
    print("  Creating w variables...", flush=True)
    w = [[[model.NewBoolVar(f'w_{r}_{i}_{j}') for j in range(n)]
          for i in range(n)] for r in range(n)]
    print(f"  w: {n*n*n} vars ({time.time()-t0:.1f}s)", flush=True)
    
    # Linking w = y AND f
    print("  Adding w=y&f constraints...", flush=True)
    for r in range(n):
        for i in range(n):
            for j in range(n):
                model.Add(w[r][i][j] <= y[r][i][j])
                model.Add(w[r][i][j] <= f[r][i])
                model.Add(w[r][i][j] >= y[r][i][j] + f[r][i] - 1)
    print(f"  w linking done ({time.time()-t0:.1f}s)", flush=True)
    
    # Latin square constraints
    print("  Adding Latin square constraints...", flush=True)
    for r in range(n):
        for i in range(n):
            model.Add(sum(y[r][i][j] for j in range(n)) == 1)
    for r in range(n):
        for j in range(n):
            model.Add(sum(y[r][i][j] for i in range(n)) == 1)
    for i in range(n):
        for j in range(n):
            model.Add(sum(y[r][i][j] for r in range(n)) == 1)
    print(f"  Latin square done ({time.time()-t0:.1f}s)", flush=True)
    
    # Color balance constraints
    print("  Adding balance constraints...", flush=True)
    for r in range(n):
        model.Add(sum(f[r][i] for i in range(n)) == m)
    for i in range(n):
        model.Add(sum(f[r][i] for r in range(n)) == m)
    for j in range(n):
        model.Add(sum(w[r][i][j] for r in range(n) for i in range(n)) == m)
    print(f"  Balance done ({time.time()-t0:.1f}s)", flush=True)
    
    # Symmetry breaking
    print("  Adding symmetry breaking...", flush=True)
    for i in range(n):
        model.Add(y[0][i][i] == 1)
    for i in range(m):
        model.Add(f[0][i] == 1)
    for i in range(m, n):
        model.Add(f[0][i] == 0)
    
    setup_time = time.time() - t0
    print(f"\nModel setup complete: {setup_time:.1f}s", flush=True)
    print(f"Total variables: ~{2*n*n*n + n*n}", flush=True)
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 600
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = True
    
    print("\nSolving...", flush=True)
    status = solver.Solve(model)
    
    print(f"\nStatus: {solver.StatusName(status)}", flush=True)
    print(f"Wall time: {solver.WallTime():.1f}s", flush=True)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        L = [[0]*n for _ in range(n)]
        F = [[0]*n for _ in range(n)]
        
        for r in range(n):
            for i in range(n):
                F[r][i] = solver.Value(f[r][i])
                for j in range(n):
                    if solver.Value(y[r][i][j]) == 1:
                        L[r][i] = j
        
        return L, F, solver.WallTime()
    
    return None, None, solver.WallTime()


def verify(L, F):
    errors = []
    for r in range(n):
        if sorted(L[r]) != list(range(n)):
            errors.append(f"Round {r+1}: row not permutation")
    for i in range(n):
        col = [L[r][i] for r in range(n)]
        if sorted(col) != list(range(n)):
            errors.append(f"A{i+1}: col not permutation")
    for r in range(n):
        if sum(F[r]) != m:
            errors.append(f"Round {r+1}: row sum={sum(F[r])}")
    for i in range(n):
        s = sum(F[r][i] for r in range(n))
        if s != m:
            errors.append(f"A{i+1}: first={s}")
    for j in range(n):
        sec = sum(1 for r in range(n) for i in range(n) if L[r][i] == j and F[r][i] == 1)
        if sec != m:
            errors.append(f"B{j+1}: second={sec}")
    for r in range(n):
        bf = sum(1 for i in range(n) if F[r][i] == 0)
        if bf != m:
            errors.append(f"Round {r+1}: B-first={bf}")
    return errors


def write_solution(L, F, solve_time, filename="solution_34.txt"):
    with open(filename, 'w') as out:
        out.write(f"# Team Round-Robin Tournament Solution for n={n}, m={m}\n")
        out.write(f"# Solved by CP-SAT in {solve_time:.1f}s\n")
        out.write(f"# Format: player on LEFT of '-' goes first\n\n")
        
        for r in range(n):
            matches = []
            for i in range(n):
                j = L[r][i]
                if F[r][i] == 1:
                    matches.append(f"A{i+1}-B{j+1}")
                else:
                    matches.append(f"B{j+1}-A{i+1}")
            out.write(f"第{r+1}轮 {' '.join(matches)}\n")
        
        out.write(f"\n# Verification\n")
        errors = verify(L, F)
        if errors:
            out.write(f"# ERRORS: {len(errors)}\n")
            for e in errors:
                out.write(f"#   {e}\n")
        else:
            out.write(f"# ALL CHECKS PASSED\n")
            out.write(f"# - All {n*n} pairs appear exactly once\n")
            out.write(f"# - Each round: {m} A-first, {m} B-first\n")
            out.write(f"# - Each A-player: first={m}, second={m}\n")
            out.write(f"# - Each B-player: first={m}, second={m}\n")
    
    print(f"\nSolution written to {filename}", flush=True)


if __name__ == '__main__':
    L, F, solve_time = solve()
    if L is not None:
        errors = verify(L, F)
        if errors:
            print(f"\nVERIFICATION FAILED: {len(errors)} errors", flush=True)
            for e in errors[:10]:
                print(f"  {e}", flush=True)
        else:
            print(f"\nALL CHECKS PASSED!", flush=True)
        write_solution(L, F, solve_time)
    else:
        print("\nNo solution found!", flush=True)
        sys.exit(1)
