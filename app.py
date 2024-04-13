from flask import Flask, send_file
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import io
import pandas as pd
import numpy as np
import pandas as pd
from numpy import genfromtxt
import matplotlib.pyplot as plt
from trueskill import TrueSkill, Rating



# Initialize Firebase Admin
cred = credentials.Certificate('firebase-key.json')
firebase_admin.initialize_app(cred)

app = Flask(__name__)
db = firestore.client()

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


@app.route('/plot.png')
def plot_png():
    # # Fetch data
    # docs = db.collection('gameResults').stream()
    # print(docs)
    # # Process data to count games per player
    # player_counts = {}
    # for doc in docs:
    #     game = doc.to_dict()
    #     for player in game:
    #         if player not in ['Game', 'order']:  # Exclude non-player fields
    #             player_counts[player] = player_counts.get(player, 0) + 1
    
    # # Generate plot
    # players = list(player_counts.keys())
    # counts = list(player_counts.values())
    # print(players, counts)
    # plt.figure(figsize=(10, 6))
    # plt.bar(players, counts, color='skyblue')
    # plt.xlabel('Players')
    # plt.ylabel('Number of Games Participated')
    # plt.title('Game Participation by Player')
    # plt.xticks(rotation=45)
    
    # # Save plot to a bytes buffer
    # buf = io.BytesIO()
    # plt.savefig(buf, format='png')
    # buf.seek(0)
    
    # # Send buffer as a response
    # return send_file(buf, mimetype='image/png')
    df = fetch_data_as_dataframe() #pd.read_csv('example_data/Game Data - Data.csv')
    df2 = df.astype(object).where(pd.notnull(df),None)
    boys = df2.columns[1:]

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
    do_threshold_experiment=False
    for index, row in df2.iterrows():
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
        old_ranks = ranks

        if do_threshold_experiment:
            boy_of_interest = ""
            if cnt == df2.shape[0]:
                print(dictrow)
                for boy in participating_boys:
                    if dictrow[boy] == 4.0:
                        print("updating boy")
                        boy_of_interest = boy
                        new_rating = Rating(mu=22.7, sigma=ratings_dict[boy][-1].sigma)
                        ratings_dict[boy][-1] = new_rating
                        print("before:", ratings_dict[boy][-1], boy)

        ranks, rating_groups, group_indices = fix_ties_and_teams(ranks, rating_groups)
        rating_groups = pad_rating_groups(rating_groups)
        rated_rating_groups = env.rate(rating_groups, ranks=ranks)

        for j, group in enumerate(group_indices):
            for k, i in enumerate(group):
                ratings_dict[participating_boys[i]].append(rated_rating_groups[j][k])
        if do_threshold_experiment:
            if cnt == df2.shape[0]:
                print("after:", ratings_dict[boy_of_interest][-1], boy_of_interest)


    scores_mu = {}
    scores_sigma = {}
    colors=['#913DD1', '#000000', '#CCBB44', '#EE6677', '#4477AA', '#228833', 'Grey']
    for i, boy in enumerate(ratings_dict):
        scores_mu[boy] = [float(i.mu) for i in ratings_dict[boy]]
        scores_sigma[boy] = [float(i.sigma) for i in ratings_dict[boy]]
    print(scores_mu)
    for k, i in enumerate(scores_mu):
        if k == 7:
            del scores_mu[i]
            break
    df = pd.DataFrame(scores_mu)
    df = df[-30:]
    print(df.columns)
    df.plot(color=colors)
    GREY = "#808080"
    # plt.legend(loc=(1.04, 0))

    plt.xlabel("Games played")
    plt.ylabel("Rating")
    plt.title("Ühran boys standings (TrueSkill)", loc="left", color=GREY)
    plt.tight_layout()
    ax = plt.gca()
    beautify_ax(ax, GREY)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 0.5), frameon=False)
    # # Save plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight') 
    # plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Send buffer as a response
    return send_file(buf, mimetype='image/png')
    # plt.show()


if __name__ == '__main__':
    print("hiya")
    app.run(debug=True)