from textbase import bot, Message
import pandas as pd

app_data = pd.read_csv("googleplaystore.csv")
# User state to keep track of the user's preferences
user_state = {}

@bot()
def on_message(message_history, state=None):
    global user_state

    # Get the user's latest message
    user_message = message_history[-1]["content"][0]["value"].lower()  # Convert to lowercase

    # Initialize the bot response
    bot_response = ""

    # Check if it's the user's first interaction
    if not user_state:
        # Send a welcome message and ask for the app category
        bot_response = "Welcome to the App Recommendation Chatbot! What category of app are you interested in?"
        user_state['step'] = 'category'  # Set the user's current step

    else:
        # Determine the user's current step
        current_step = user_state.get('step', None)

        if current_step == 'category':
            # User specified a category, ask for the type (free or paid)
            user_state['category'] = user_message
            bot_response = "Great! Do you want a free or paid app? Please type 'free' or 'paid'."
            user_state['step'] = 'type'  # Set the next step

        elif current_step == 'type':
            # User specified type (free or paid), check for valid input
            user_type = user_message
            if user_type in ['free', 'paid']:
                user_state['type'] = user_type
                if user_type == 'paid':
                    bot_response = "What is your budget for the app? Please specify the maximum price you're willing to pay."
                    user_state['step'] = 'price'  # Set the next step
                else:
                    user_state['price'] = 0  # Default to 0 if the app is free
                    bot_response = "What genre of app are you interested in?"
                    user_state['step'] = 'genre'  # Set the next step
            else:
                bot_response = "Please type 'free' or 'paid' to specify the type of app you want."

        elif current_step == 'price':
            # User specified the price, ask for genre
            try:
                user_state['price'] = float(user_message)  # Convert price to float
                bot_response = "What genre of app are you interested in?"
                user_state['step'] = 'genre'  # Set the next step
            except ValueError:
                bot_response = "Please enter a valid numeric price for the app."

        elif current_step == 'genre':
            # User specified a genre, recommend an app based on their preferences
            user_state['genre'] = user_message
            recommended_app = recommend_app(user_state)  # Function to recommend an app based on preferences

            if recommended_app is not None:
                recommended_app_name = recommended_app['App']
                content_rating = recommended_app['Content Rating']
                installs = recommended_app['Installs']
                reviews = recommended_app['Reviews']
                rating = recommended_app['Rating']
                min_size = recommended_app['Size']

                bot_response = f"I recommend '{recommended_app_name}' with Content Rating '{content_rating}', " \
                            f"Installs '{installs}', Reviews '{reviews}', Rating '{rating}', and Size '{min_size}'."
            else:
                bot_response = "I'm sorry, I couldn't find an app recommendation based on your preferences."

            # Clear the user's state for the next interaction
            user_state = {}

    response = {
        "data": {
            "messages": [{"data_type": "STRING", "value": bot_response}],
            "state": state
        },
        "errors": [
            {
                "message": ""
            }
        ]
    }

    return {
        "status_code": 200,
        "response": response
    }

# Function to recommend an app based on user preferences
def recommend_app(user_state):
    category = user_state.get('category', '').lower()
    app_type = user_state.get('type', '').lower()
    price = user_state.get('price', 0)
    genre = user_state.get('genre', '').lower()

    app_data['Price'] = pd.to_numeric(app_data['Price'], errors='coerce')
    # Filter apps based on user preferences
    if app_type == 'free':
        # User wants a free app, no need for price comparison
        filtered_apps = app_data[(app_data['Category'].str.lower() == category) &
                                (app_data['Type'].str.lower() == 'free') &
                                (app_data['Genres'].str.lower().str.contains(genre))]
    else:
        # User wants a paid app, perform price comparison
        filtered_apps = app_data[(app_data['Category'].str.lower() == category) &
                        (app_data['Type'].str.lower() == 'paid') &
                        (app_data['Price'] <= price) &
                        (app_data['Genres'].str.lower().str.contains(genre))]

    if not filtered_apps.empty:
        # Get an app with maximum content rating, installs, reviews, rating, and minimum size
        recommended_app = filtered_apps.loc[filtered_apps['Content Rating'].idxmax()]
        return recommended_app
    else:
        return None

if __name__ == "__main__":
    from textbase import run_bot

    response = run_bot()
    
    if response is not None:
        if response.get("status_code") == 200 and "response" in response:
            print("Bot response:", response["response"]["data"]["messages"])
        else:
            print("Bot returned an error response:", response)
    else:
        print("Bot returned None response.")
