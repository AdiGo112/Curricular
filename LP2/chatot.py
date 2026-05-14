# =========================================================
# ELEMENTARY CHATBOT
# Customer Interaction Application
# =========================================================

# This chatbot is designed for a simple
# online shopping customer support system.
#
# The chatbot can answer basic customer queries
# related to:
# 1. Orders
# 2. Payments
# 3. Returns
# 4. Delivery
# 5. Contact Support
#
# =========================================================
# HOW TO USE
# =========================================================
#
# 1. Run the program.
#
# 2. Type your message/query.
#
# Example Inputs:
# - hi
# - order status
# - payment methods
# - return policy
# - delivery details
# - contact support
#
# 3. The chatbot will reply automatically.
#
# 4. Type 'exit' to end the chatbot.
#
# =========================================================


print("===================================")
print(" Welcome to SmartShop Chatbot ")
print("===================================")

print("\nType 'exit' to end the chat.\n")


# Infinite loop for continuous chatting
while True:

    # Take input from user
    user = input("You: ").lower()

    # =====================================================
    # EXIT CONDITION
    # =====================================================

    # End chatbot if user types 'exit'
    if user == "exit":

        print("Bot: Thank you for visiting SmartShop!")
        print("Bot: Have a great day!")

        break


    # =====================================================
    # GREETING QUERIES
    # =====================================================

    elif user in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you", "what's up"]:

        print("Bot: Hello! How can I help you today?")


    # =====================================================
    # ORDER RELATED QUERIES
    # =====================================================

    elif user in ["order status", "track order", "where is my order", "order"]:

        print(
            "Bot: Your order will be delivered "
            "within 3-5 working days."
        )


    # =====================================================
    # PAYMENT RELATED QUERIES
    # =====================================================

    elif user in ["payment methods", "payment options", "how to pay", "payment"]:

        print(
            "Bot: We support UPI, Debit Card, "
            "Credit Card, and Net Banking."
        )


    # =====================================================
    # RETURN POLICY QUERIES
    # =====================================================

    elif user in ["return policy", "return items", "exchange items", "refund", "return"]:

        print(
            "Bot: Products can be returned "
            "within 7 days of delivery."
        )


    # =====================================================
    # CONTACT SUPPORT QUERIES
    # =====================================================

    elif user in ["contact support", "need help", "support", "help"]:

        print(
            "Bot: You can contact us at "
            "support@smartshop.com"
        )


    # =====================================================
    # PRODUCT RELATED QUERIES
    # =====================================================

    elif user in ["product information", "product details", "product"]:

        print(
            "Bot: Please enter the product name "
            "on our website search bar."
        )


    # =====================================================
    # DELIVERY RELATED QUERIES
    # =====================================================

    elif user in ["delivery details", "delivery", "how long will it take"]:

        print(
            "Bot: Standard delivery usually "
            "takes 3-5 days."
        )


    # =====================================================
    # THANK YOU RESPONSE
    # =====================================================

    elif user in ["thank you", "thanks", "thx"]:

        print("Bot: You're welcome!")


    # =====================================================
    # DEFAULT RESPONSE
    # =====================================================

    # If chatbot cannot understand query
    else:

        print(
            "Bot: Sorry, I did not understand "
            "your query."
        )