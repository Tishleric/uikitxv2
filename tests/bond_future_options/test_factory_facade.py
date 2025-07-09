"""
Test the Factory/Facade implementation for bond future options.
"""

from lib.trading.bond_future_options import (
    GreekCalculatorAPI,
    ModelFactory,
    BachelierV1
)
from lib.monitoring.decorators import monitor


@monitor()
def test_model_factory():
    """Test the model factory functionality."""
    print("\n=== Testing Model Factory ===")
    
    # Test creating default model
    model = ModelFactory.create_model()
    assert model.get_version() == "bachelier_v1.0"
    print(f"✓ Default model created: {model.get_version()}")
    
    # Test creating with explicit name
    model = ModelFactory.create_model('bachelier_v1')
    assert model.get_version() == "bachelier_v1.0"
    print(f"✓ Explicit model created: {model.get_version()}")
    
    # Test with custom parameters
    model = ModelFactory.create_model(
        'bachelier_v1',
        future_dv01=0.07,
        future_convexity=0.003
    )
    params = model.get_parameters()
    assert params['future_dv01'] == 0.07
    assert params['future_convexity'] == 0.003
    print(f"✓ Model with custom parameters: DV01={params['future_dv01']}")
    
    # Test listing models
    available = ModelFactory.list_models()
    assert 'bachelier_v1' in available
    print(f"✓ Available models: {list(available.keys())}")


@monitor()
def test_greek_calculator_api():
    """Test the Greek Calculator API facade."""
    print("\n=== Testing Greek Calculator API ===")
    
    # Create API instance
    api = GreekCalculatorAPI()
    
    # Test single option analysis
    option = {
        'F': 110.75,
        'K': 110.5,
        'T': 0.05,
        'market_price': 0.359375,
        'option_type': 'put'
    }
    
    result = api.analyze(option)
    
    # Verify results
    assert result['success'] == True
    assert 'volatility' in result
    assert 'greeks' in result
    assert result['model_version'] == 'bachelier_v1.0'
    
    print(f"✓ Single option analysis:")
    print(f"  Volatility: {result['volatility']:.2f}")
    print(f"  Delta: {result['greeks']['delta_y']:.2f}")
    print(f"  Model: {result['model_version']}")
    
    # Test batch processing
    options = [
        {'F': 110.75, 'K': 110.5, 'T': 0.05, 'market_price': 0.359375},
        {'F': 110.75, 'K': 111.0, 'T': 0.05, 'market_price': 0.453125},
    ]
    
    results = api.analyze(options)
    
    assert len(results) == 2
    assert all(r['success'] for r in results)
    
    print(f"\n✓ Batch analysis:")
    for i, r in enumerate(results):
        print(f"  Option {i+1}: K={r['K']}, Vol={r['volatility']:.2f}")
    
    # Test with explicit model selection
    result = api.analyze(option, model='bachelier_v1.0')
    assert result['success'] == True
    print(f"\n✓ Explicit model selection works")
    
    # Test with custom model parameters
    result = api.analyze(
        option, 
        model_params={'future_dv01': 0.08}
    )
    assert result['success'] == True
    print(f"✓ Custom model parameters accepted")


@monitor()
def test_model_interface_compliance():
    """Test that BachelierV1 properly implements the interface."""
    print("\n=== Testing Interface Compliance ===")
    
    model = BachelierV1()
    
    # Test all required methods exist
    assert hasattr(model, 'calculate_price')
    assert hasattr(model, 'calculate_implied_vol')
    assert hasattr(model, 'calculate_greeks')
    assert hasattr(model, 'get_version')
    assert hasattr(model, 'get_parameters')
    
    print("✓ All interface methods present")
    
    # Test method signatures work
    price = model.calculate_price(110.75, 110.5, 0.05, 5.0)
    assert isinstance(price, float)
    print(f"✓ calculate_price returns float: {price:.6f}")
    
    vol = model.calculate_implied_vol(110.75, 110.5, 0.05, 0.359375)
    assert isinstance(vol, float)
    print(f"✓ calculate_implied_vol returns float: {vol:.2f}")
    
    greeks = model.calculate_greeks(110.75, 110.5, 0.05, vol)
    assert isinstance(greeks, dict)
    assert 'delta_y' in greeks
    print(f"✓ calculate_greeks returns dict with {len(greeks)} Greeks")


if __name__ == "__main__":
    print("Testing Factory/Facade Implementation...")
    
    test_model_factory()
    test_greek_calculator_api()
    test_model_interface_compliance()
    
    print("\n✅ All factory/facade tests passed!") 