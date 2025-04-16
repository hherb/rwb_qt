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

SHUTDOWNS = ["Goodbye, {user.firstname}!",
            "Nonono please don't!",
           "See you soon, {user.firstname}!",
           "See you later, {user.firstname}!",
           "Take care, {user.firstname}!",
           "Farewell, {user.firstname}!",
           "Catch you later, {user.firstname}!",
           "Until next time, {user.firstname}!",
           "Adios, {user.firstname}!",
           "Bye for now, {user.firstname}!",
           "Later, {user.firstname}!",
           "Come on, {user.firstname}, a bit longer please!"]  # Add more shutdown messages as needed


def random_greeting(user):
    """
    Returns a random greeting message for the user.
    
    Args:
        user (User): The user object containing user information.
        
    Returns:
        str: A random greeting message.
    """
    return random.choice(GREETINGS).format(user=user)

def random_shutdown(user):
    """
    Returns a random shutdown message for the user.
    
    Args:
        user (User): The user object containing user information.
        
    Returns:
        str: A random shutdown message.
    """
    return random.choice(SHUTDOWNS).format(user=user)