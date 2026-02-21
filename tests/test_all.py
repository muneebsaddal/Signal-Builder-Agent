import sys
sys.path.append('.')

from schemas.ir_schema import SignalIR
from schemas.resolver import SchemaRegistry, SchemaResolver
from graph import SignalBuilderGraph


def test_schema_registry():
    """Test schema loading and lookup"""
    print("=" * 50)
    print("TEST: Schema Registry")
    print("=" * 50)
    
    registry = SchemaRegistry()
    
    # Test loading
    assert registry.schemas is not None
    print("✓ Schemas loaded successfully")
    
    # Test node lookup
    ma_schema = registry.get_schema("indicator", "MovingAverage")
    assert ma_schema is not None
    print("✓ MovingAverage schema found")
    
    # Test listing
    nodes = registry.list_nodes("indicator")
    print(f"✓ Found {len(nodes.get('indicators', []))} indicators")
    
    print()


def test_ir_validation():
    """Test IR validation"""
    print("=" * 50)
    print("TEST: IR Validation")
    print("=" * 50)
    
    registry = SchemaRegistry()
    resolver = SchemaResolver(registry)
    
    # Valid IR
    valid_ir = SignalIR(
        signal_type="indicator",
        node="MovingAverage",
        params={"window": 20, "source": "price.close"}
    )
    
    is_valid, errors = resolver.validate_ir(valid_ir)
    assert is_valid
    print("✓ Valid IR passed validation")
    
    # Invalid IR - missing required param
    invalid_ir = SignalIR(
        signal_type="indicator",
        node="MovingAverage",
        params={}  # Missing window
    )
    
    is_valid, errors = resolver.validate_ir(invalid_ir)
    assert not is_valid
    print(f"✓ Invalid IR caught: {errors[0]}")
    
    print()


def test_ir_resolution():
    """Test IR to schema resolution"""
    print("=" * 50)
    print("TEST: IR Resolution")
    print("=" * 50)
    
    registry = SchemaRegistry()
    resolver = SchemaResolver(registry)
    
    # Create IR
    ir = SignalIR(
        signal_type="indicator",
        node="RSI",
        params={"period": 14}
    )
    
    # Resolve
    resolved = resolver.resolve(ir)
    
    assert resolved.resolved_schema["indicator"] == "rsi"
    assert resolved.resolved_schema["period"] == 14
    print("✓ IR resolved correctly")
    print(f"  Resolved schema: {resolved.resolved_schema}")
    
    print()


def test_end_to_end():
    """Test complete graph execution"""
    print("=" * 50)
    print("TEST: End-to-End Graph Execution")
    print("=" * 50)
    
    builder = SignalBuilderGraph()
    
    test_requests = [
        "20-day moving average of closing price",
        "RSI below 30",
        "14-period RSI indicator"
    ]
    
    for req in test_requests:
        print(f"\nRequest: {req}")
        result = builder.run(req)
        
        output = result["output"]
        print(f"Status: {output['status']}")
        
        if output["status"] == "success":
            print(f"✓ IR: {output['ir']['node']}")
            print(f"✓ Resolved: {list(output['resolved_schema'].keys())}")
        else:
            print(f"✗ Errors: {output.get('errors', [])}")
        
        print(f"Execution steps: {len(result['execution_log'])}")
        print(f"Retries: {result['retry_count']}")
    
    print()


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("SIGNAL BUILDER AGENT - TEST SUITE")
    print("=" * 50 + "\n")
    
    try:
        test_schema_registry()
        test_ir_validation()
        test_ir_resolution()
        test_end_to_end()
        
        print("=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
