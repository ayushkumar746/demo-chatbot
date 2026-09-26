from app.tools.product_tools import format_price
from app.tools.cart_tools import format_cart_summary
from app.agent.state import AgentState


class ResponseAgent:
    """
    Response Agent that turns workflow results into a user-facing message.

    Responses are built deterministically from verified state (search results,
    cart after refresh) so the reply can never contradict what actually happened.
    """

    def generate_response(self, state: AgentState) -> AgentState:
        """
        Generate a natural language response based on workflow results.

        This is a LangGraph node function.
        """
        intent = state.get("intent")
        selected_product = state.get("selected_product")
        cart = state.get("cart")
        action_result = state.get("action_result")
        error = state.get("error")
        requires_confirmation = state.get("requires_confirmation", False)
        confirmation_options = state.get("confirmation_options")

        # Handle confirmation required case
        if requires_confirmation and confirmation_options:
            state["final_response"] = self._generate_confirmation_response(confirmation_options)
            return state

        # Handle error case
        if error:
            state["final_response"] = self._generate_error_response(error)
            return state

        # Handle successful cart operation
        if action_result and action_result.get("success"):
            state["final_response"] = self._generate_success_response(
                selected_product,
                cart,
                action_result
            )
            return state

        # Handle product search only (no cart operation)
        if selected_product and not action_result:
            state["final_response"] = (
                f"I found {selected_product.name} priced at {format_price(selected_product.price)}. "
                "Would you like me to add it to your cart?"
            )
            return state

        # Handle cart view
        if intent and intent.action == "VIEW_CART" and cart:
            state["final_response"] = format_cart_summary(cart)
            return state

        # Handle no products found
        if not selected_product:
            state["final_response"] = self._generate_no_products_response(intent)
            return state

        # Default response
        state["final_response"] = "I'm sorry, I couldn't process your request. Please try again."
        return state

    def _generate_confirmation_response(self, options: list) -> str:
        """Generate response when user needs to choose from multiple products"""
        lines = ["I found several products matching your request:"]
        for i, option in enumerate(options, 1):
            lines.append(f"{i}. {option['name']} — {format_price(option['price'])}")
        lines.append("\nWhich one would you like me to add?")
        return "\n".join(lines)

    def _generate_error_response(self, error: str) -> str:
        """Generate response for error cases; errors in state are already client-safe."""
        if "already in cart" in error.lower():
            return "This item is already in your cart. Would you like me to update the quantity instead?"
        return f"Sorry, I couldn't complete your request. {error}"

    def _generate_success_response(self, product, cart, action_result) -> str:
        """Generate response for successful operations"""
        if product:
            cart_item = next((item for item in cart.items if item.product_id == product.id), None) if cart else None
            added_quantity = action_result.get("quantity", 1)
            if cart_item and cart_item.quantity > added_quantity:
                message = f"{product.name} quantity updated to {cart_item.quantity} in your cart."
            else:
                message = f"{product.name} priced at {format_price(product.price)} has been added to your cart."

            # Add cart summary
            if cart:
                message += f"\n\n{format_cart_summary(cart)}"

            return message

        return action_result.get("message", "Operation completed successfully.")

    def _generate_no_products_response(self, intent) -> str:
        """Generate response when no products are found"""
        if intent and intent.category:
            return f"I couldn't find any {intent.category} matching your criteria. Would you like to try a different category or adjust your price range?"
        return "I couldn't find any products matching your request. Would you like to try a different search term?"


# Global instance
response_agent = ResponseAgent()
