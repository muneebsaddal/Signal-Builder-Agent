#!/usr/bin/env python3
"""
Example execution script for Signal Builder Agent
Demonstrates various trading signal requests
"""

import sys
sys.path.append('.')

from graph import SignalBuilderGraph
import json


def save_execution_trace(result: dict, filename: str):
    """Save execution trace to file"""
    with open(f"examples/execution_traces/{filename}", 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"✓ Saved trace to examples/execution_traces/{filename}")


def run_example(builder: SignalBuilderGraph, request: str, description: str):
    """Run a single example request"""
    print("\n" + "=" * 70)
    print(f"EXAMPLE: {description}")
    print("=" * 70)
    print(f"Request: \"{request}\"")
    print()
    
    result = builder.run(request)
    output = result["output"]
    
    # Print results
    print(f"Status: {output['status']}")
    print(f"Retries: {result['retry_count']}")
    
    if output["status"] == "success":
        print("\nIntermediate Representation (IR):")
        print(f"  Type: {output['ir']['signal_type']}")
        print(f"  Node: {output['ir']['node']}")
        print(f"  Params: {output['ir']['params']}")
        
        print("\nResolved Schema:")
        print(json.dumps(output['resolved_schema'], indent=2))
        
        print("\nMetadata:")
        print(f"  Version: {output['metadata']['version']}")
        print(f"  Timestamp: {output['metadata']['timestamp']}")
    else:
        print("\n✗ FAILED")
        print(f"Errors: {output.get('errors', [])}")
    
    print(f"\nExecution Steps:")
    for i, log in enumerate(result['execution_log'], 1):
        print(f"  {i}. {log['step']}")
    
    # Save trace
    filename = request.replace(" ", "_").replace("-", "")[:30] + ".json"
    save_execution_trace(result, filename)
    
    return result


def main():
    """Run example requests"""
    print("\n" + "=" * 70)
    print("SIGNAL BUILDER AGENT - EXAMPLE EXECUTIONS")
    print("=" * 70)
    
    builder = SignalBuilderGraph()
    
    examples = [
        (
            "20-day moving average of closing price",
            "Simple Moving Average Indicator"
        ),
        (
            "14-period RSI indicator",
            "RSI Technical Indicator"
        ),
        (
            "RSI below 30",
            "RSI Threshold Condition"
        ),
        (
            "MACD with fast 12, slow 26, signal 9",
            "MACD Indicator with Custom Parameters"
        ),
        (
            "Volume spike above 2x average",
            "Volume Condition"
        ),
        (
            "Bollinger Bands with 20 period",
            "Bollinger Bands Indicator"
        ),
        (
            "Moving average crossover strategy with 10 and 20 periods",
            "MA Crossover Strategy"
        ),
        (
            "Price above 50-day moving average",
            "Price Condition with Indicator Reference"
        )
    ]
    
    successful = 0
    failed = 0
    
    for request, description in examples:
        result = run_example(builder, request, description)
        
        if result["output"]["status"] == "success":
            successful += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total Examples: {len(examples)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(examples)*100):.1f}%")
    print()


if __name__ == "__main__":
    main()
