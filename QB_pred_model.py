import pandas as pd
import numpy as np
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt
sns.set()

from sklearn.model_selection import train_test_split, KFold
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LassoCV, RidgeCV
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
import statsmodels.api as sm

# This is the DF created from PFR_scrape.py.
path = './Pickles/'
car_avg_df = pd.read_pickle(path + 'car_avg_stats_df.pkl')

def calc_passer_rating(row):
    '''
    Calculates passer rating for each row in a dataframe
    arg:
        row of a pandas df with Cmp, Att, Pass_Yds, TD and Int data
    return:
        QB's rating as float
    '''
    comp_p = (row['Cmp'] / row['Att'] - .3) * 5
    pyd_p = (row['Pass_Yds'] / row['Att'] - 3) * .25
    td_p = (row['TD'] / row['Att']) * 20
    int_p = 2.375 - (row['Int'] / row['Att']) * 25
    return sum([comp_p, pyd_p, td_p, int_p]) / 6

# Prepping table with additional stats/features

def add_features(car_avg_df):
    '''
    Add TD%, Int%, and place QBs in different bins
    arg:
        DF created from PFR_scrape.py
    return:
        Two DF: 1) DF with added stats; 2) DF of 2018 QBs who did not play full 2018 season
    '''
    # Add TD%, Int%, and apply passer rating function
    car_avg_df['YTD_Rating'] = car_avg_df.apply(calc_passer_rating, axis=1)
    car_avg_df['TD%'] = car_avg_df.apply(lambda x: x['TD'] / x['Att'], axis=1)
    car_avg_df['Int%'] = car_avg_df.apply(lambda x: x['Int'] / x['Att'], axis=1)
    career_ratings = car_avg_df.groupby('name', as_index=False)['YTD_Rating'].mean().reset_index()
    # binning QBs into tiers by ratings
    career_ratings['tier'] = pd.qcut(career_ratings['YTD_Rating'], 3, labels=[3, 2, 1])
    career_ratings['tier'] = career_ratings['tier'].astype(int)
    data_stats = career_ratings.merge(car_avg_df, on='name')
    data_stats.rename({'YTD_Rating_x': 'Car Rating', 'YTD_Rating_y': 'YTD_Rating'}, axis=1, inplace=True)

    # saving 2018 injured/benched players for inclusion in model
    benched_injured_df = data_stats[(data_stats['FY_TD'].isna()) &
                                    (data_stats['Year'] == 2018)]
    data_stats.dropna(inplace=True)
    return data_stats, benched_injured_df

def tr_val_test_split(data_stats):
    '''
    1) Reserve 2018 stats in a dataframe as test set;
    2) Extract only numerical stats as features for train_val set
    arg:
        Raw df with added stats
    :return:
        1) df for train_val;
        2) df for testing
    '''
    car_avg_stats = ['Year','FY_TD','G','Career W %','Cmp/gm',
                     'Att/gm','TD/gm','TD%','Int%','Pass_Yds/gm','Int/gm',
                     'Sk/gm', 'Yrs Xp', 'tier']
    car_avg_graph_df = data_stats[car_avg_stats]
    test_df_2018 = data_stats[data_stats['Year'] == 2018]
    train_val_df = car_avg_graph_df[car_avg_graph_df['Year'] < 2018].copy()
    return train_val_df, test_df_2018

def add_deviation_feature(X, feature, category):
    '''
    Scales a feature based on stand deviation in categorical groups. Adds
    calculation as a series in the dataframe.
    arg:
        X: dataframe
        feature: feature to be scaled among categories
        category: categorical used to group data for scaling
    '''
    category_gb = X.groupby(category)[feature]
    # create columns of category means and standard deviations
    category_mean = category_gb.transform(lambda x: x.mean())
    category_std = category_gb.transform(lambda x: x.std())
    deviation_feature = (X[feature] - category_mean) / category_std
    X[feature + '_Dev_' + category] = deviation_feature

def train_val_add_dev(df):
    '''
    Apply deviation feature to train_val set
    arg:
        df with TD/gm and FY_TD stats
    return:
        df with features, np array with target
    '''
    # run add deviation on train_val_df set
    add_deviation_feature(df, 'TD/gm', 'tier')
    X_train_val = df.drop(['FY_TD'], axis=1)
    # transform target variable
    y_train_val = np.log(df['FY_TD'])
    return X_train_val, y_train_val

def prep_test_inputs(test_df_2018, benched_injured_df):
    '''
    Join test df to be included in test set and add deviation variable.
    Filter inputs applicable for regression model
    arg:
        1) df for active 2018 players
        2) df for inactive/partially active 2018 players
    return:
        df to be inputted in model
    '''
    qb_set_2018 = test_df_2018.append(benched_injured_df)
    add_deviation_feature(qb_set_2018, 'TD/gm', 'tier')
    sel_features = ['name','Year', 'FY_TD', 'G', 'Career W %', 'Cmp/gm',
                    'Att/gm', 'TD/gm', 'TD%', 'Int%', 'Pass_Yds/gm',
                    'Int/gm', 'Sk/gm', 'Yrs Xp', 'tier', 'TD/gm_Dev_tier']
    qb_set_2018 = qb_set_2018[sel_features]
    return qb_set_2018

def final_model(X_train, y, X_test, alpha=0.01):
    '''
    Creates a polynomial + LASSO model to predict future touchdown passes
    arg:
        1) X_train are variables from the training set
        2) y are actuals to fit training
        3) X_test are inputs for prediction
        4) alpha default at 0.01 based on cross validation phase
    return:
        Numpy array containing predicted passing TD (in natural log)
    '''
    X_train['PY/G^3'] = X_train['Pass_Yds/gm'] ** 3 + X_train['Pass_Yds/gm'] ** 2
    X_train['Cmp/G^3'] = X_train['Cmp/gm'] ** 3 + X_train['Cmp/gm'] ** 2
    X_train['TD/gm^3'] = X_train['TD/gm'] ** 3 + X_train['TD/gm'] ** 2
    X_train['TD%_/_Int%'] = X_train['TD%'] / X_train['Int%']

    X_test['PY/G^3'] = X_test['Pass_Yds/gm'] ** 3 + X_test['Pass_Yds/gm'] ** 2
    X_test['Cmp/G^3'] = X_test['Cmp/gm'] ** 3 + X_test['Cmp/gm'] ** 2
    X_test['TD/gm^3'] = X_test['TD/gm'] ** 3 + X_test['TD/gm'] ** 2
    X_test['TD%_/_Int%'] = X_test['TD%'] / X_test['Int%']

    scaler = StandardScaler()
    X_tr_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # LASSO model
    lasso_model = Lasso(alpha=alpha)
    lasso_model.fit(X_tr_scaled, y)
    ln_predictions = lasso_model.predict(X_test_scaled)
    return ln_predictions

def result_df(test_input, predictions):
    # return df with results and analysis
    results_df = test_input[['name', 'FY_TD']]
    results_df['Pred'] = np.round_(np.exp(predictions), 0)
    results_df['Residual'] = results_df['Pred'] - results_df['FY_TD']
    # Calculate MSE
    results_df['Residual'].apply(lambda x: x**2).sum() / len(results_df['Residual'])
    print(results_df.sort_values(by='FY_TD', ascending=False))

if __name__ == '__main__':
    data_stats, benched_injured_df = add_features(car_avg_df)
    train_val_df, test_df_2018 = tr_val_test_split(data_stats)
    #pre-engineering features
    X_tr, y_tr = train_val_add_dev(train_val_df)
    test_input = prep_test_inputs(test_df_2018, benched_injured_df)
    X_test = test_input.drop(['name','FY_TD'], axis=1)
    # Run model; trains on train/val, output predict on X_test
    predictions = final_model(X_tr, y_tr, X_test, alpha=0.01)
    result_df(test_input, predictions)
