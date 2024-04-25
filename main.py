import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from trueskill import TrueSkill, Rating
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS, cross_origin



# Initialize Firebase Admin
cred = credentials.Certificate('firebase-key.json')
firebase_admin.initialize_app(cred)

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app, resources={r"/plot_data/*": {"origins": "*"}})
app.url_map.strict_slashes = False
app.config['CORS_HEADERS'] = 'Content-Type'

db = firestore.client()


@app.route("/plot_data/", methods=['POST', 'OPTIONS'])
@cross_origin()
def plot_data():
    log_request_info()
    if request.method == "OPTIONS":
        # Create a response for the OPTIONS request
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Accept, X-Custom-Header'

        response.status_code = 200
        print(response)
        return response
    # elif request.method == 'POST':
    else:
        df = fetch_data_as_dataframe() #pd.read_csv('example_data/Game Data - Data.csv')
        df2 = df.astype(object).where(pd.notnull(df),None)

        env = TrueSkill(tau=1.5)  
        ratings_dict = {'Auðun'  : [Rating()], 
                        'Árni'   : [Rating()], 
                        'Hlynur' : [Rating()], 
                        'Kári'   : [Rating()], 
                        'Skossi' : [Rating()],
                        'Sævar' : [Rating()], 
                        'Örn'   : [Rating()],
                        'Tóta' : [Rating()]}
        cnt=0
        for _, row in df2.iterrows():
            cnt+=1

            dictrow = dict(row)
            rating_groups = []
            ranks = []
            participating_boys = []
            for boy_name in ratings_dict:
                if dictrow[str(boy_name)] not in [None, '']:
                    participating_boys.append(boy_name)
                    rating_groups.append([ratings_dict[boy_name][-1]])
                    ranks.append(float(dictrow[str(boy_name)]))
                else:
                    ratings_dict[boy_name].append(ratings_dict[boy_name][-1])

            ranks, rating_groups, group_indices = fix_ties_and_teams(ranks, rating_groups)
            rating_groups = pad_rating_groups(rating_groups)
            rated_rating_groups = env.rate(rating_groups, ranks=ranks)

            for j, group in enumerate(group_indices):
                for k, i in enumerate(group):
                    ratings_dict[participating_boys[i]].append(rated_rating_groups[j][k])

        scores_mu = {}
        scores_sigma = {}
        colors=['#913DD1', '#000000', '#CCBB44', '#EE6677', '#4477AA', '#228833', 'Grey']
        for i, boy in enumerate(ratings_dict):
            scores_mu[boy] = [float(i.mu) for i in ratings_dict[boy]]
            scores_sigma[boy] = [float(i.sigma) for i in ratings_dict[boy]]
        for k, i in enumerate(scores_mu):
            if k == 7:
                del scores_mu[i]
                break
        data_for_chart = {
            "labels": list(range(len(next(iter(scores_mu.values()))))),  # Assuming each player has the same number of ratings
            "datasets": [
                {"label": boy, "data": scores, "borderColor": color, "fill": False}
                for boy, scores, color in zip(scores_mu.keys(), scores_mu.values(), colors)
            ]
        }

        return jsonify(data_for_chart)


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/app.js')
def serve_js():
    return app.send_static_file('app.js')

@app.after_request
def set_response_headers(response):
    # Setting Cache-Control
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    # Remove unneeded headers
    response.headers.pop('X-XSS-Protection', None)
    # Set x-content-type-options header
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Avoid using 'Expires' header for cache management
    response.headers.pop('Expires', None)
    # Set Content-Security-Policy
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
    return response

def fetch_data_as_dataframe():
    # Fetch documents from Firestore
    docs = db.collection('gameResults').stream()
    
    # Convert documents to a list of dictionaries
    data = [doc.to_dict() for doc in docs]
    
    # Sort the list of dictionaries by the "order" field
    sorted_data = sorted(data, key=lambda x: x['order'])
    
    # Convert the sorted list of dictionaries to a Pandas DataFrame
    df = pd.DataFrame(sorted_data)
    
    return df

def get_index_dict(lst):
    """
    Returns a dictionary with the numbers in the given list as keys and
    their indices in the list as values.

    
    Args:
        lst (list): A list of numbers.

    Returns:
        dict: A dictionary with the numbers as keys and their indices as values.
    """
    index_dict = {}
    for i, num in enumerate(lst):
        if num not in index_dict:
            index_dict[num] = [i]
        else:
            index_dict[num].append(i)
    return index_dict

def get_ordinality(lst):
    """
    Returns a list of ordinality for the given list of numbers.

    Args:
        lst (list): A list of numbers.

    Returns:
        list: A list of ordinality for the given list of numbers.
    """
    sorted_lst = sorted(list(set(lst)))
    ordinality = [sorted_lst.index(num) for num in lst]
    return ordinality

def fix_ties_and_teams(ranks, rating_groups):
    """
    Processes ranking and rating groups to handle ties and group them accordingly.

    This function uses an index dictionary to manage the ranks and groups teams based on these ranks.
    It generates lists of unfixed ranks, fixed rating groups (each containing the first member from the
    rating groups indexed), and the indices of these groups in the original input.

    Parameters:
        ranks (list): A list of ranks, where each rank can appear multiple times indicating ties.
        rating_groups (list of list): A list of lists, where each inner list represents a group of ratings.

    Returns:
        tuple:
            - list: Ordinal ranks converted from unfixed ranks.
            - list of list: Newly created list where each sublist contains the first member of each
                            corresponding rating group, grouped according to their rank.
            - list of list: List of indices representing the original positions of the groups in the
                            rating_groups list, grouped by their ranks.

    Note:
        This function involves several steps:
        1. Converting the ranks into an index dictionary.
        2. Extracting and grouping the first member of each rating group based on their rank.
        3. Returning the ordinality of ranks along with the grouped rating members and their indices.
    """
    index_dict = get_index_dict(ranks)
    unfixed_ranks = []
    fixed_rating_groups = []
    group_indices = []
    for i in index_dict:
        unfixed_ranks.append(i)
        lst=[]
        lst_indices = []
        for j in index_dict[i]:
           lst.append(rating_groups[j][0]) 
           lst_indices.append(j)
        fixed_rating_groups.append(lst)
        group_indices.append(lst_indices)
    return get_ordinality(unfixed_ranks), fixed_rating_groups, group_indices
import copy
def pad_rating_groups(rating_groups):
    """
    Adjust the groups of ratings so that all groups have the same number of 
    elements by padding shorter groups with new instances of the Rating class.

    The function deep-copies the input list to avoid modifying the original data,
    calculates the maximum length of any group within the list, and then pads
    each group to match this maximum length by appending
    new instances of Rating until all groups are of equal size.

    Parameters:
        rating_groups (list of list of Rating): A list where each element is a 
        list of Rating objects representing a group of ratings.

    Returns:
        list of list of Rating: A new list of rating groups where each group has 
        been padded to ensure that all groups have the same number of Rating instances.

    Examples:
        >>> pad_rating_groups([[Rating(5), Rating(4)], [Rating(3)]])
        [[Rating(5), Rating(4)], [Rating(3), Rating()]]
    """
    rgroups = copy.deepcopy(rating_groups)
    max_groupsize = -1
    for i in rgroups:
        if len(i) > max_groupsize:
            max_groupsize = len(i)
    for i in rgroups:
        while len(i) < max_groupsize:
            i.append(Rating())
    return rgroups

def beautify_ax(ax, color):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(color)
    ax.spines["left"].set_color(color)
    # Set x and y axis labels
    plt.xlabel("Rating", color=color)
    plt.ylabel("# Game", color=color)
    # Set legend font color and remove border
    legend = ax.legend(frameon=False)
    for text in legend.get_texts():
        text.set_color(color)
    # Set tick color
    ax.tick_params(axis="x", colors=color)
    ax.tick_params(axis="y", colors=color)
import logging
logging.basicConfig(level=logging.DEBUG)

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

if __name__ == '__main__':
    print("hiya")
    app.run(debug=True)