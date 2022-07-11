from numpy import matrix
import pandas as pd

class ClothingMatrix():
    def __init__(self,filename):
        self.filename = filename
        self.matrix = pd.read_csv(filename,index_col='i')

    def addIdToMatrix(self,id):
        #adds column to matrix at end
        #title is id, fills with 0s
        added = False

        try:
            self.matrix.insert(len(self.matrix.columns),id,0,False)
            self.matrix.fillna(0)
            added=True
        except ValueError:
            print("repeated id")

        if added:
            #adds row of 0 to bottom
            self.matrix.loc[len(self.matrix.index)] = 0

            #changes the value in the 'ids' col
            #to the input id
            self.matrix.loc[len(self.matrix.index)-1,"ids"] = "'"+id+"'"

        #save
        self.save()

    def delete_id_from_matrix(self,id):
        index = None
        for row in self.matrix.index:
            if self.matrix.loc[row,"ids"] == "'"+id+"'":
                self.matrix.drop(row,inplace=True)
                print('done')

        self.matrix.drop(labels=id,axis=1,inplace=True)

        #reset index

        self.matrix.index = pd.RangeIndex(len(self.matrix.index))
        self.matrix.rename_axis('i', inplace=True)

        self.save()


    def rate(self,outfitIds,rating):
        for row in self.matrix.index:
            for item in outfitIds:
                if self.matrix.loc[row,'ids']=="'"+str(item)+"'":
                    #For each row corresponding to an item in the outfit
                    for icol in range(0,len(self.matrix.columns)):
                        col = self.matrix.columns[icol]
                        for item in outfitIds:
                            if col==str(item):
                                #For each col corresponding to an item in the outfit 

                                #compute average of existing value in cell and new rating
                                self.matrix.loc[row,col] = (self.matrix.loc[row,col] + rating)/2
        

        self.save()

    def save(self):
        self.matrix.to_csv(self.filename)