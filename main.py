import os
import sys
from dotenv import load_dotenv

# Ensure the root directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent.agent import ReActAgent
from src.tools.tools import check_stock, get_discount, calc_shipping, get_product_price, calculate_tax

def print_banner():
    print("=" * 65)
    print("🤖  WELCOME TO THE REACT AGENT INTERACTIVE SHELL  🤖")
    print("=" * 65)
    print("Available Tools:")
    print("  1. check_stock(item_name)  -> Checks item quantity in database")
    print("  2. get_discount(coupon_code) -> Verifies and retrieves discount rate")
    print("  3. calc_shipping(weight, destination) -> Computes shipping fees")
    print("  4. get_product_price(item_name) -> Retrieves product base price")
    print("  5. calculate_tax(subtotal, destination) -> Computes VAT/sales tax")
    print("=" * 65)

def main():
    load_dotenv()
    
    provider_type = os.getenv("DEFAULT_PROVIDER", "mimo").lower()
    model_name = os.getenv("DEFAULT_MODEL", "mimo-v2.5-pro")
    
    print(f"Loading LLM Provider: {provider_type.upper()} ({model_name})...")
    
    try:
        if provider_type == "google" or provider_type == "gemini":
            from src.core.gemini_provider import GeminiProvider
            provider = GeminiProvider(model_name=model_name, api_key=os.getenv("GEMINI_API_KEY"))
        elif provider_type == "openai":
            from src.core.openai_provider import OpenAIProvider
            provider = OpenAIProvider(model_name=model_name, api_key=os.getenv("OPENAI_API_KEY"))
        elif provider_type == "local":
            from src.core.local_provider import LocalProvider
            provider = LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH"))
        else:
            # Fallback to the new custom LLMProvider pointing to MIMO
            from src.core.llm_provider import LLMProvider
            provider = LLMProvider(model_name=model_name, api_key=os.getenv("MIMO_API_KEY"), base_url=os.getenv("LLM_ENDPOINT"))
            
        print("✅ LLM Provider loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load LLM Provider: {e}")
        print("Falling back to local simulation mode...")
        return

    # Define tools specifications for the agent
    tools_spec = [
        {
            "name": "check_stock",
            "description": "Check the current stock of an item in the warehouse. Args: item_name (str).",
            "func": check_stock
        },
        {
            "name": "get_discount",
            "description": "Retrieve discount percentage for a coupon code. Args: coupon_code (str).",
            "func": get_discount
        },
        {
            "name": "calc_shipping",
            "description": "Calculate shipping cost based on weight and destination. Args: weight (float), destination (str).",
            "func": calc_shipping
        },
        {
            "name": "get_product_price",
            "description": "Retrieve the base price of a product. Args: item_name (str).",
            "func": get_product_price
        },
        {
            "name": "calculate_tax",
            "description": "Calculate the sales tax (VAT) based on subtotal and destination. Args: subtotal (float), destination (str).",
            "func": calculate_tax
        }
    ]

    # Initialize ReAct Agent
    agent = ReActAgent(llm=provider, tools=tools_spec, max_steps=5)
    
    print_banner()
    
    print("\nAsk your e-commerce agent a question! (type 'exit' to quit)")
    print("Example: 'I want to buy 2 iPhones using code student and ship to Hanoi. Total cost?'")
    
    while True:
        try:
            user_query = input("\n👤 User: ").strip()
            if not user_query:
                continue
            if user_query.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
                
            print("\n⚙️  Agent is thinking and reasoning...\n")
            
            # Run the Agent
            response = agent.run(user_query)
            
            print("\n🤖 Final Answer:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error during execution: {e}")

if __name__ == "__main__":
    main()
