import pandas as pd

def collaborative_filtering(item0, saveFileName):
    matrix = pd.read_csv("clothingMatrix.csv",index_col = 'i')

    item_similarity_df = matrix.corr(method='pearson')
    print(item_similarity_df)
    item_similarity_df.fillna(0)

    similar_score = item_similarity_df[item0].sort_values(ascending=False)

    similar_score.to_csv("OutfitPool.csv",header=False)

#collaborative_filtering('16080',"OutfitPool.csv")