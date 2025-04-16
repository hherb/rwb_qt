import random

GREETINGS = ["Hi, {user.firstname}! What took you so long?",
             "Hello, {user.firstname}!",
            "Hey, {user.firstname}! Missed you!",
            "Greetings, {user.firstname}!",
            "Salutations, {user.firstname}!",
            "Howdy, {user.first_name}!",
            "Welcome back, {user.firstname}!",
            "Good to see you, {user.firstname}!",
            "What's up, {user.firstname}?",
            "Yo, {user.firstname}! Long time no see!"]  # Add more greetings as needed


def random_greeting(user):
    """
    Returns a random greeting message for the user.
    
    Args:
        user (User): The user object containing user information.
        
    Returns:
        str: A random greeting message.
    """
    import random
    return random.choice(GREETINGS).format(user=user)