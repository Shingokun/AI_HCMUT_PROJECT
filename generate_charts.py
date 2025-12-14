import matplotlib.pyplot as plt
import json
import os

def generate_charts():
    # Data from the evaluation
    files = ["test_1", "test_2", "test_3", "test_4", "test_5", "test_6", "test_7", "test_8", "test_9", "test_10"]
    accuracies = [0.75, 0.50, 1.00, 0.75, 1.00, 1.00, 0.75, 1.00, 1.00, 1.00]
    
    # 1. Accuracy Chart
    plt.figure(figsize=(10, 6))
    plt.bar(files, accuracies, color='skyblue')
    plt.xlabel('Document ID')
    plt.ylabel('Accuracy')
    plt.title('Accuracy per Document')
    plt.ylim(0, 1.1)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    for i, v in enumerate(accuracies):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center')
        
    plt.tight_layout()
    plt.savefig('accuracy_chart.png')
    print("Generated accuracy_chart.png")
    
    # 2. Error Distribution
    fields = ['Signer', 'Issuer', 'Date', 'Decision No']
    errors = [4, 0, 0, 1] # Based on analysis
    
    plt.figure(figsize=(8, 6))
    plt.barh(fields, errors, color='salmon')
    plt.xlabel('Number of Errors')
    plt.title('Error Distribution by Field')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    for i, v in enumerate(errors):
        plt.text(v + 0.1, i, str(v), va='center')
        
    plt.tight_layout()
    plt.savefig('error_distribution.png')
    print("Generated error_distribution.png")

if __name__ == "__main__":
    try:
        generate_charts()
    except ImportError:
        print("Matplotlib is not installed. Please install it to generate charts.")
        print("pip install matplotlib")
