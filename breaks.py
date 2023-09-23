from datetime import timedelta as td
import pickle

breaks = {
    'break1': [td(hours=8, minutes=10), td(minutes=45)],
    'break2': [td(hours=6, minutes=10), td(minutes=30)],
    'break3': [td(hours=4, minutes=10), td(minutes=15)]
}


def set_default_breaks():
    """
    Saves the default breaks to a pickle file
    """
    with open("breaks.pkl", "wb") as f:
        pickle.dump(breaks, f)


def return_breaks():
    """
    Returns the breaks dictionary from 'breaks.pkl' file

    :return: dict
    """
    with open("breaks.pkl", "rb") as f:
        dict = pickle.load(f)

    return dict


def save_new_dict(new_d):
    """
    Writes given dictionary to 'breaks.pkl' file

    :param new_d: dict
    """
    with open("breaks.pkl", "wb") as f:
        pickle.dump(new_d, f)

