import pandas as pd
import numpy as np
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from rmllm.utils.apa import format_descriptives_summary

def test_format_descriptives_summary():
    data = {
        ('mean', 'accuracy', 'SingleTurn'): [1.0, 0.5],
        ('std', 'accuracy', 'SingleTurn'): [0.0, 0.1],
        ('mean', 'accuracy', 'TrialChain'): [1.0, 0.4],
        ('std', 'accuracy', 'TrialChain'): [0.0, 0.2],
        ('mean', 'confidence', 'SingleTurn'): [5.0, 5.5],
        ('std', 'confidence', 'SingleTurn'): [0.3, 0.7],
        ('mean', 'confidence', 'TrialChain'): [5.9, 5.8],
        ('std', 'confidence', 'TrialChain'): [0.1, 0.6],
    }
    df = pd.DataFrame(data, index=['Model1', 'Model2'])
    df.columns.names = [None, 'metric', 'memory']
    
    formatted_df = format_descriptives_summary(df)
    
    print("Formatted DataFrame:")
    print(formatted_df)
    
    assert formatted_df.shape == (2, 4)
    assert formatted_df.iloc[0, 0] == "1.00 (0.00)"
    assert formatted_df.iloc[1, 1] == "0.40 (0.20)"
    print("Test passed!")

if __name__ == "__main__":
    test_format_descriptives_summary()
