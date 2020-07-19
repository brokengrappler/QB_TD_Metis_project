# QB TD projection (Metis - Linear Regression project)

#### Description 
Create a linear regression model that will project TD passes to be thrown for starting QBs in a subsequent year. The regression was
calculated using QB stats from 1998-2019. Feature engineering included:
- Polynomial regression
- Category deviance
- Interaction terms

Arrived at final model using LASSO regression.

Test set (2019 TD projects on 2018 YTD stats input) had a R<sup>2</sup> of 0.351.

#### Assignment requirements
This project was selected to fulfill the requirements of building a linear regression model to demonstrate and implement knowledge of:
- web scraping
- numpy and pandas
- statsmodels and scikit-learn

#### Data Sources
- [pro-football-reference.com](https://www.pro-football-reference.com/)

#### File Contents
- `Scrape_qb_list.py` Compile list of active quarterbacks between a specified number of years. Data frame returned is used in PFR_scrape.py.
- `PFR_scrape.py` Acquire data from pro-football-reference for QBs in the Scrape_qb_list and creates a pandas data frame. Data frame returned is used in QB_pred_model.py.
- `QB_pred_model.py` Creates model and prints results of actual vs. predicted for 2019 (test set)
`jpnb folder` Jupyter notebook folders containing charts and statistical summaries from EDA.

#### Dependencies
- Python 3.6 (and above)
- pandas
- numpy
- statsmodels
- scikit-learn
- bs4
- matplotlib
- seaborn
- collections
