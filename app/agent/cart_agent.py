import logging

from app.schemas import AddToCartRequest
from app.services.cart_service import cart_service
from app.services.vector_store import VectorStoreError
from app.tools.cart_tools import validate_cart_addition
from app.config import settings
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


class CartAgent:
    """Cart Agent that handles cart operations with validation"""
    
    def get_cart(self, state: AgentState) -> AgentState:
        """
        Get the current cart state.
        
        This is a LangGraph node function.
        """
        user_id = state.get("user_id")
        store_id = state.get("store_id", settings.default_store_id)
        
        try:
            cart = cart_service.get_cart(user_id, store_id)
            state["cart"] = cart
        except Exception:
            logger.exception("Cart retrieval failed for user=%s store=%s", user_id, store_id)
            state["error"] = "Cart retrieval error: the cart service is unavailable."
            state["cart"] = None
        
        return state
    
    def validate_cart_operation(self, state: AgentState) -> AgentState:
        """
        Validate cart operation before execution.
        
        This is a LangGraph node function.
        """
        cart = state.get("cart")
        selected_product = state.get("selected_product")
        intent = state.get("intent")
        
        if not cart or not selected_product:
            state["validation_result"] = None
            return state
        
        quantity = intent.quantity if intent else 1
        
        # Validate using deterministic Python function
        validation = validate_cart_addition(
            cart,
            selected_product.id,
            quantity
        )
        
        state["validation_result"] = validation
        if not validation.valid:
            state["error"] = f"Cannot add {selected_product.name}: {validation.reason}"
        return state
    
    def add_to_cart(self, state: AgentState) -> AgentState:
        """
        Add product to cart after validation.
        
        This is a LangGraph node function.
        """
        cart = state.get("cart")
        selected_product = state.get("selected_product")
        validation = state.get("validation_result")
        intent = state.get("intent")
        
        # Check if validation passed
        if not validation or not validation.valid:
            state["action_result"] = {
                "success": False,
                "message": validation.reason if validation else "Validation failed"
            }
            return state
        
        if not cart or not selected_product:
            state["error"] = "Missing cart or product for add operation"
            return state
        
        quantity = intent.quantity if intent else 1
        
        try:
            # Create add to cart request
            add_request = AddToCartRequest(
                cart_id=cart.cart_id,
                product_id=selected_product.id,
                quantity=quantity
            )
            
            # Add to cart using service
            response = cart_service.add_to_cart(add_request)
            
            state["action_result"] = {
                "success": response.success,
                "message": response.message,
                "quantity": quantity
            }
            
            # Refresh cart to verify state
            if response.success:
                refreshed_cart = cart_service.get_cart(state["user_id"], state["store_id"])
                state["cart"] = refreshed_cart
            else:
                state["error"] = f"Add to cart failed: {response.message}"
            
        except VectorStoreError as error:
            logger.error("Add to cart failed, product index unavailable: %s", error)
            state["error"] = "Add to cart failed: the product catalog is unavailable."
            state["action_result"] = {"success": False, "message": state["error"]}
        except Exception:
            logger.exception("Add to cart failed for product=%s", selected_product.id)
            state["error"] = "Add to cart failed: the cart could not be updated."
            state["action_result"] = {"success": False, "message": state["error"]}
        
        return state
    
    def verify_cart_state(self, state: AgentState) -> AgentState:
        """
        Verify cart state after mutation.
        
        This is a LangGraph node function.
        """
        user_id = state.get("user_id")
        store_id = state.get("store_id", settings.default_store_id)
        
        try:
            # Refresh cart to get actual state
            cart = cart_service.get_cart(user_id, store_id)
            state["cart"] = cart
        except Exception:
            logger.exception("Cart verification failed for user=%s store=%s", user_id, store_id)
            state["error"] = "Cart verification error: the cart service is unavailable."
        
        return state


# Global instance
cart_agent = CartAgent()
