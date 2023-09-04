from textbase import bot, Message
import pandas as pd

# Load the app dataset from "googleplaystore.csv"

# Load the university dataset from "Ranking.csv"
university_data = pd.read_csv("Rankings.csv")
app_data = pd.read_csv("googleplaystore.csv")

# Convert string columns to numeric (if needed)
university_data['OverAll Score'] = pd.to_numeric(university_data['OverAll Score'], errors='coerce')
university_data['Teaching Score'] = pd.to_numeric(university_data['Teaching Score'], errors='coerce')
university_data['Research Score'] = pd.to_numeric(university_data['Research Score'], errors='coerce')

from textbase import bot

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
        # Ask the user if they want university recommendations
        bot_response = "Welcome! Would you like recommendations for universities? Please type 'university'."
        user_state['step'] = 'choice'  # Set the user's current step

    else:
        # Determine the user's current step
        current_step = user_state.get('step', None)

        if current_step == 'choice':
            # User specified their choice (university)
            if user_message == 'university':
                # User wants university recommendations, ask for location
                bot_response = "Sure! In which location are you looking for universities?"
                user_state['step'] = 'location'  # Set the next step

            else:
                bot_response = "Please type 'university' for university recommendations."

        elif current_step == 'location':
            # User specified the location, ask for Overall Score
            user_state['location'] = user_message
            bot_response = "Great! Now, please provide a score out of 100 for Overall Score."
            user_state['step'] = 'overall_score'  # Set the next step

        elif current_step == 'overall_score':
            # User provided Overall Score, ask for Teaching Score
            try:
                overall_score = float(user_message)
                user_state['overall_score'] = overall_score
                bot_response = "Got it! Please provide a score out of 100 for Teaching Score."
                user_state['step'] = 'teaching_score'  # Set the next step
            except ValueError:
                bot_response = "Please enter a valid numeric score for Overall Score."

        elif current_step == 'teaching_score':
            # User provided Teaching Score, ask for Research Score
            try:
                teaching_score = float(user_message)
                user_state['teaching_score'] = teaching_score
                bot_response = "Got it! Please provide a score out of 100 for Research Score."
                user_state['step'] = 'research_score'  # Set the next step
            except ValueError:
                bot_response = "Please enter a valid numeric score for Teaching Score."

        elif current_step == 'research_score':
            # User provided Research Score, recommend a university based on their preferences
            try:
                research_score = float(user_message)
                user_state['research_score'] = research_score
                recommended_university = recommend_university(user_state)  # Function to recommend a university

                if recommended_university is not None:
                    rank = recommended_university['University Rank']
                    university_name = recommended_university['Name of University']
                    bot_response = f"The university in {user_state['location']} with the lowest rank based on your criteria is '{university_name}' with a rank of {rank}."
                else:
                    bot_response = "I'm sorry, I couldn't find a university recommendation based on your preferences."

                # Clear the user's state for the next interaction
                user_state = {}
            except ValueError:
                bot_response = "Please enter a valid numeric score for Research Score."

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

# Function to recommend a university based on user preferences
def recommend_university(user_state):
    location = user_state.get('location', '').lower()
    overall_score = user_state.get('overall_score', 0)
    teaching_score = user_state.get('teaching_score', 0)
    research_score = user_state.get('research_score', 0)

    # Filter universities based on location and scores
    filtered_universities = university_data[(university_data['Location'].str.lower() == location) &
                                            (university_data['OverAll Score'] >= overall_score) &
                                            (university_data['Teaching Score'] >= teaching_score) &
                                            (university_data['Research Score'] >= research_score)]

    if not filtered_universities.empty:
        # Get the university with the lowest rank
        recommended_university = filtered_universities.loc[filtered_universities['University Rank'].idxmin()]
        return recommended_university
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
