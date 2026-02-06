"""Deploy stub for Prediction Wager contract.

This script provides instructions and a basic template to deploy via the
GenLayer CLI / Studio. It does not perform a real deploy automatically.
"""

import subprocess
import sys


def print_instructions():
    print("Deploying a Python contract to GenLayer typically uses the GenLayer CLI.")
    print("If you have the GenLayer CLI installed, you can run:")
    print("  genlayer network  # choose network\n  genlayer deploy")
    print("This repository's contract is in prediction_wager/contract.py")


def main():
    print_instructions()


if __name__ == '__main__':
    main()
