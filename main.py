#IMPORTS
from cgi import test
from multiprocessing import pool
from kivymd.uix.button import *
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.core.window import Window
from kivymd.uix.navigationdrawer import NavigationLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.toast import toast

from kivy.uix.image import Image
from kivymd.uix.imagelist import SmartTileWithLabel
from kivymd.uix.list import MDIconButton
from kivymd.uix.dialog import MDDialog

from nbformat import read
from numpy import delete
import pandas as pd
from random import randint
import shutil

import filecmp

import os, sys
from kivy.resources import resource_add_path, resource_find

from sqlalchemy import null
from sympy import source

from ClothingMatrix import ClothingMatrix

#--------------------------------------------------------------------------------------------------

#GLOBAL OBJECTS
wardrobe = None
matrix = None

#--------------------------------------------------------------------------------------------------

class MyLayout(NavigationLayout):
    #navigates to specified screen with a right transition (as if going backwards)
    def backButton(self, screenname):
        global wardrobe

        self.ids.screenmanager.transition.direction = 'right'
        self.ids.screenmanager.current = screenname


    #navigates to specified screen with left transition (as if going forwards)
    def nextScreen(self, screenname):
        self.ids.screenmanager.transition.direction = 'left'
        self.ids.screenmanager.current = screenname   

#--------------------------------------------------------------------------------------------------

#KIVY CLASS EXTENSIONS
class MyClothesTile(SmartTileWithLabel):
    def get_clothing_object_from_image_address(self,address):
        #the 6 letters before the full stop form the id
	    #so split address string by '.'
	    #and take a substring of the last 6 letters

        id = address.split('.')[0][-5:]


        for type in wardrobe.clothes:
            for item in type:
                if item.get_clothing_id() == id:
                    return item
        
        return -1

    def tile_selected(self):
        if self.box_color == [0,0,0,0]:

            viewers = self.parent.parent.parent.parent.parent.children
            

            #reset color of other tiles
            #unhighlight other tiles...
            for viewer in viewers:
                for tile in viewer.ids.container_x.children:
                    tile.box_color = [0,0,0,0]
                    tile.text = ""

            #...so only current is highlighted
            self.box_color = self.theme_cls.primary_color
            self.text = "GENERATE OUTFIT"
            self.tile_text_color = [0,0,0,1]
        else:
            #change screen
            self.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.nextScreen("generateOutfitScreen")
            self.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.parent.ids.generateOutfitScreen.displayOutfit(self.get_clothing_object_from_image_address(self.source))

#--------------------------------------------------------------------------------------------------

class DeleteItemTile(SmartTileWithLabel):
    dialog = None
    def get_clothing_object_from_image_address(self,address):
        #the 6 letters before the full stop form the id
	    #so split address string by '.'
	    #and take a substring of the last 6 letters

        id = address.split('.')[0][-5:]


        for type in wardrobe.clothes:
            for item in type:
                if item.get_clothing_id() == id:
                    return item
        
        return -1


    #show confirmation box
    def show_alert_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                size_hint_x = 0.8,
                title="Are you sure you want to delete this item?",
                text = "All outfits containing this item will also be deleted!",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release = self.close_dialog
                    ),
                    MDFlatButton(
                        text="DELETE",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release = self.delete_item
                    ),
                ],
            )
        self.dialog.open()

    #to close dialog
    def close_dialog(self,obj):
        self.dialog.dismiss()

    #when confirmed, delete item
    def delete_item(self,obj):

        item = self.get_clothing_object_from_image_address(self.source)
        print("ITEM BEING DELETED: " + item.get_clothing_id())

        #delete from clothes.csv file
        
        with open("clothes.csv", "r") as f:
            lines = f.readlines()
        with open("clothes.csv", "w") as f:
            for line in lines:
                
                if line.split(",")[0] != item.get_clothing_id():
                    f.write(line)


        #delete from savedOutfits.csv
        with open("savedOutfits.csv", "r") as f:
            lines = f.readlines()
        with open("savedOutfits.csv", "w") as f:
            for line in lines:
                write = True
                for id in line.split(","):
                    if id == item.get_clothing_id():
                        write = False
                

                
                if write:
                    f.write(line)

        #delete image in subfolder
        if os.path.exists(item.get_image_address()):
            os.remove(item.get_image_address())
        else:
            print("The file does not exist")


        #delete from clothingMatrix.csv
        matrix.delete_id_from_matrix(item.get_clothing_id())

        #delete from wardrobe
        for type in wardrobe.clothes:
            for clothing in type:
                if clothing.get_clothing_id() == item.get_clothing_id():
                    type.remove(clothing)
        wardrobe.printWardrobe()

        self.dialog.dismiss()

        #refresh current screen so item no longer shown to user
        self.parent.parent.parent.parent.add_images()
        
    #show confirmation box
    #when item selected to delete
    def tile_selected(self):
        self.show_alert_dialog()
        
#--------------------------------------------------------------------------------------------------   
    
#class for canvas grid for outfit
#main code in design file - for appearance
class OutfitGrid(GridLayout):
    pass

#line to sepearate outfits
#main code in design file
class Separator(Widget):
    pass

#--------------------------------------------------------------------------------------------------

class DeleteOutfitButton(MDIconButton):
    
    #set outfit attribute for button
    #the outfit that the button is linked to
    #just holds ids of clothes in array attribute
    def set_outfitIds(self,outfit):
        self.outfitIds = []
        for item in outfit:
            self.outfitIds.append(item.get_clothing_id())
            
    
    #delete outfit procedure
    #compares own outfit attribute to each line of outfits save file
    #if same then delete the outfit
    def delete_outfit(self,saveFile):

        #print(saveFile)
        with open(saveFile, "r") as f:
            lines = f.readlines()
        with open(saveFile, "w") as f:
            for line in lines:
                
                if sorted(line.strip("\n").split(",")) != sorted(self.outfitIds):
                    f.write(line)

        #refresh page so outfit is removed from screen
        self.parent.parent.parent.parent.parent.parent.parent.parent.display_outfits()

        #confirmation message
        toast("Outfit Deleted")

        
#--------------------------------------------------------------------------------------------------
    
#SCREENS

#Screen shown when user first loads app
#main code in design file - for appearance
class StartScreen(Screen):
    pass

class MyWardrobeScreen(Screen):
    
    #to display all of the clothes
    def add_images(self):
        global wardrobe
        

        #for each clothing type in wardrobe
        for i in range (0,len(wardrobe.clothes)):
            types = ["Tops", "Bottoms", "One-Pieces", "Jackets", "Shoes", "Accessories"]
            viewer = self.ids.image_viewers.children[len(wardrobe.clothes)-i-1]
            

            viewer.ids.viewer_label.text = types[i]
            container = viewer.ids.container_x

            for child in container.children:
                #empty image_viewers
                container.clear_widgets()
                
            for item in wardrobe.clothes[i]:
                
                container.add_widget(MyClothesTile(source = item.get_image_address()))


    def get_object_id(self, id):
        #search through wardrobe
        #return correct Clothing object

        for type in wardrobe.clothes:
            for item in type:
                if item.get_clothing_id() == id:
                    return item
        
        #print("error")


    #read outfits save file
    #obtain array of outfit arrays and return
    def get_outfits(self,saveFile):
        outfits = []
        file = open(saveFile)

        outfitIds = file.readline().strip(" \n")
        
        while outfitIds!=None and outfitIds!='':
            outfitIds=outfitIds.split(",")
            

            outfit = []

            for id in outfitIds:
                outfit.append(self.get_object_id(id))

            outfits.append(outfit)
            outfitIds = file.readline().strip(" \n")


        
        file.close()
        
        return outfits

    #to display the outfits
    def display_outfits(self):
        outfits = self.get_outfits("savedOutfits.csv")
        self.ids.outfitContainer.clear_widgets()
        for outfit in outfits:
            outfit_images = ["","","",
                            "","","",
                            "","",""]
            if len(outfit) > 0:
                #if outfit exists
                #assign position in grid to each item
                outfitGrid = OutfitGrid()
                for item in outfit:

                    if item.get_clothing_type() == "accessories":
                        outfit_images[1] = item.get_image_address() #top middle
                    elif item.get_clothing_type() == "top":
                        outfit_images[3] = item.get_image_address() #middle left
                    elif item.get_clothing_type() == "onepiece":
                        outfit_images[4] = item.get_image_address() #middle middle
                    elif item.get_clothing_type() == "jackets":
                        outfit_images[5] = item.get_image_address() #middle right
                    elif item.get_clothing_type() == "bottom":
                        outfit_images[6] = item.get_image_address() #bottom left
                    elif item.get_clothing_type() == "shoes":
                        outfit_images[7] = item.get_image_address() #bottom middle
                    else:
                        print("error adding image")
                
                #display outfit grid - add images to grid
                for address in outfit_images:
                    outfitGrid.add_widget(Image(source = address))

                
                self.ids.outfitContainer.add_widget(outfitGrid)

                #add delete button associated with outfit
                #assign the outfit to the button (calls previous function)
                binButton = DeleteOutfitButton()
                binButton.set_outfitIds(outfit)
                self.ids.outfitContainer.add_widget(binButton)
                
                #separator - visual clarity
                self.ids.outfitContainer.add_widget(Separator())


#--------------------------------------------------------------------------------------------------
    
class OutfitSandboxScreen(Screen):
    pass

class MyPlannerScreen(Screen):
    pass

#--------------------------------------------------------------------------------------------------

class FileChooserScreen(Screen):
    #called when a file is selected on the file chooser screen
    image_path = ""

    def selectfile(self, *args):
        try: 
            
            #update image_path variable to chosen filepath
            self.image_path = args[1][0]

            #update source for preview image to selected file
            self.parent.parent.ids.addNewItemScreen.ids.upload_preview.source = self.image_path

        except: pass

#--------------------------------------------------------------------------------------------------

class AddNewItemScreen(Screen):
    #ADD NEW ITEM SCREEN
    #----------------------
    clothingID = ""
    image_path = ""
    clothing_type = ""

    #function called when radio buttons are selected
    def radio_selected(self,instance,value, clothingType):
        #if now selected
        if value == True:
            self.clothing_type = clothingType
        else:
            #now unselected
            self.clothing_type = ""

    #set image path of item
    def set_image_path(self, *args):
        self.image_path = args[1][0]

    #generate id for item
    #to uniquely identify item
    def generateID(self):
        existingIDs = []
        file = open(r"C:\Users\Tisya\Documents\A-Level\A-Level\Computer Science\NEA\Pocket Stylist App\clothes.csv",'r')

        #list of already-used IDs
        #to avoid repeats
        for line in file:
            existingIDs.append(line.split(",")[0])

        file.close()


        valid = False
        randomID = 0

        #repeat until unique
        while not valid:
            valid = True        
            randomID = randint(10000,99999)

            #compare to IDs in existingIDs to check it's unique
            for i in range(0,len(existingIDs)):
                if existingIDs[i]==str(randomID):
                    valid = False
                    break
        
        return str(randomID)
    
    def copy_image(self, og_filepath, filename):
        #get extension of file (.jpg? .png?)
        extension = "." + og_filepath.split(".")[-1]

        #define new location
        new_address = r"C:\Users\Tisya\Documents\A-Level\A-Level\Computer Science\NEA\Pocket Stylist App\Images\item" + filename + extension

        #copy contents of file to new location
        shutil.copyfile(og_filepath, new_address)

        return new_address

    #check this image has not already been uploaded
    #simple validation
    def check_duplicate(self,user_filepath):
        directory = r"C:\Users\Tisya\Documents\A-Level\A-Level\Computer Science\NEA\Pocket Stylist App\Images"

        for dir_file in os.scandir(directory):
            if filecmp.cmp(user_filepath,dir_file.path, shallow=False):
                return True


    def reset_form(self):
        #reset variables
        self.clothingID = ""
        self.image_path = ""
        self.clothing_type = ""

        #reset page
        self.ids.upload_preview.source = r"C:\Users\Tisya\Documents\A-Level\A-Level\Computer Science\NEA\Pocket Stylist App\Images\image placeholder.png"
        for id in self.ids:
            if self.ids[id] != "upload_preview":
                self.ids[id].active = False


    #save item to save file
    #create Clothing object
    def add_and_save_item(self):
        self.clothingID = self.generateID()
        
        #basic validation
        if self.image_path == "":
            toast("Please select an image of the clothing")
        elif self. clothing_type == "":
            toast("Please select what type of clothing you are uploading by selecting a checkbox")
        elif self.check_duplicate(self.image_path):
            toast("You have already uploaded an item with this image!")

        #all required information input
        else:
            #copy image file to local directory
            self.image_path = self.copy_image(self.image_path, self.clothingID)

            #write details to 'clothing.csv file'
            # id, image address, clothing type
            file = open(r"C:\Users\Tisya\Documents\A-Level\A-Level\Computer Science\NEA\Pocket Stylist App\clothes.csv", "a")
            file.write(self.clothingID + "," + self.image_path + "," + self.clothing_type + "\n")

            #create clothing object
            newItem = Clothing(self.clothingID, self.image_path,self.clothing_type)
            wardrobe.add_item_to_correct_type_array(newItem)
            file.close()

            matrix.addIdToMatrix(self.clothingID)

            #confirmation message
            toast("Item successfully added!")
            self.reset_form()

#display all clothes
#on delete screen
class DeleteItemScreen(Screen):
    def add_images(self):
        self.ids.clothingImagesGrid.clear_widgets()
        for type in wardrobe.clothes:
            for item in type:
                self.ids.clothingImagesGrid.add_widget(DeleteItemTile(source = item.get_image_address()))

#--------------------------------------------------------------------------------------------------        

class GenerateOutfitScreen(Screen):
    
    #resets page for new outfit
    def refresh(self):
        self.stars(0)
        self.ratedOutfit = False
        self.ids.rateButton.disabled = True
        self.ids.saveButton.disabled = True
        self.ids.nextButton.disabled = True


    #obtain user input of rating
    def stars(self,rating):
        self.rating = rating
        self.ratedOutfit = False
        self.ids.rateButton.disabled = False
        self.ids.saveButton.disabled = True
        self.ids.nextButton.disabled = True

        count = 1
        for star in range(len(self.ids.rating_stars.children)-1,-1,-1):
            if count<=rating:
                self.ids.rating_stars.children[star].icon = "star"
            else:
                self.ids.rating_stars.children[star].icon = "star-outline"

            count+=1
 

    #apply rating to outfit
    #enable save and next buttons
    def rate_button_pressed(self):
        self.ids.rateButton.disabled = True
        self.ids.saveButton.disabled = False
        self.ids.nextButton.disabled = False

        if self.ratedOutfit ==False:
            self.rateOutfit(self.outfit,self.rating)
            self.ratedOutfit = True
        

    #if next button pressed
    #display a new outfit
    def next_button_pressed(self):
        if self.disabled:
            toast("Give this outfit a rating before continuing!")

        else:
            self.refresh()
            self.displayOutfit(self.item0)

    #if save button pressed
    #write to save file
    def save_button_pressed(self,saveFile):
        if self.disabled:
            toast("Give this outfit a rating before continuing!")

        else:
            string_to_write = ""

            for item in self.outfit:

                #comma separated list of ids
                if string_to_write == "":
                    string_to_write += item.get_clothing_id()
                else:
                    string_to_write += "," + item.get_clothing_id()
            

            string_to_write += "\n"

            #check if outfit has already been outfit
            check = self.check_outfit_not_already_added(string_to_write,"savedOutfits.csv")

            #confirmation/prompt message
            if check==True:
                file = open(saveFile, "a")
                file.write(string_to_write)
                file.close()

                toast("Outfit has been saved!")
            else:
                print(string_to_write)
                toast("You have already have this outfit saved!")

    def check_outfit_not_already_added(self,csvListOfIds, saveFile):
        currentOutfit = csvListOfIds.strip(" \n").split(",")
        file = open(saveFile)
        
        match = False
	
        outfit = file.readline().strip(" \n")
        while match == False and outfit!=None and outfit!='':
            outfit = outfit.split(",")
            
            if sorted(outfit)==sorted(currentOutfit):
                print(sorted(outfit))
                print(sorted(currentOutfit))
                #same sorted lists
                #therefore same outfit
                #therefore dont add
                
                return False
                

            outfit = file.readline().strip(" \n")
        
        return True


    def displayOutfit(self,inputItem):
        self.item0 = inputItem


        if randint(0,100) < 40:
            #40% chance randomly generated (w/ heuristics) outfit
            self.outfit = self.heuristicOutfit(inputItem)
            print("heuristic")
        else:
            #60% chance ai generated (w/ heuristics) outfit
            self.create_outfit_template(inputItem)
            self.outfit = self.ai_outfit(inputItem)
            print("ai")



        #corresponds to positioning in grid layout
        outfit_images = ["","","",
                         "","","",
                         "","",""]
        if self.outfit != -1:
            self.ids.outfit_grid.clear_widgets()
            for item in self.outfit:

                if item.get_clothing_type() == "accessories":
                    outfit_images[1] = item.get_image_address() #top middle
                elif item.get_clothing_type() == "top":
                    outfit_images[3] = item.get_image_address() #middle left
                elif item.get_clothing_type() == "onepiece":
                    outfit_images[4] = item.get_image_address() #middle middle
                elif item.get_clothing_type() == "jackets":
                    outfit_images[5] = item.get_image_address() #middle right
                elif item.get_clothing_type() == "bottom":
                    outfit_images[6] = item.get_image_address() #bottom left
                elif item.get_clothing_type() == "shoes":
                    outfit_images[7] = item.get_image_address() #bottom middle
                else:
                    print("error adding image")

            for address in outfit_images:
                self.ids.outfit_grid.add_widget(Image(source = address))
                
    
    def heuristicOutfit(self,inputItem):
        currentType = inputItem.get_clothing_type()

        #array to hold outfit pieces - Clothing objects
        outfit = []

        #current item must be in outfit
        outfit.append(inputItem)


        #probabilities
        pBase = randint(0,100)
        pTop = 100
        pAccessories = randint(0,100)
        pJackets = randint(0,100)


        
        
        if currentType == "onepiece" or currentType=="bottom":
            if currentType=="onepiece":
                pTop = randint(0,100)
        else:
            #CREATE OUTFIT BASE
            if ((pBase < 20) and (len(wardrobe.onepieces) >0)):
                #onepiece
                index = randint(0,len(wardrobe.onepieces)-1)
                outfit.append(wardrobe.onepieces[index])
                pTop = randint(0,100)
            elif (len(wardrobe.bottoms) >0):
                #bottom
                index = randint(0,len(wardrobe.bottoms)-1)
                outfit.append(wardrobe.bottoms[index])
            else:
                toast("Not enough pieces to create an outfit - please add some trousers/skirts etc. to the 'Bottoms' section to continue")
                return -1
        
        if currentType != "top":
            #ADD TOP (depends on pTop - 1 for bottoms, 0 or 1 for onepieces)
            if pTop > 50 and len(wardrobe.tops) > 0:
                index = randint(0,len(wardrobe.tops)-1)
                outfit.append(wardrobe.tops[index])
            else:
                if len(wardrobe.tops) <= 0:
                    toast("Not enough pieces to create an outfit - please add some tops/shirts etc. to the 'Tops' section to continue")
                    return -1

        if currentType != "shoes":
            #ADD SHOES - always 1
            if len(wardrobe.shoes) > 0:
                index = randint(0,len(wardrobe.shoes)-1)
                outfit.append(wardrobe.shoes[index])
        
        if currentType != "jackets":
            #ADD JACKET - 0 or 1
            if pJackets > 50 and len(wardrobe.jackets) > 0:
                index = randint(0,len(wardrobe.jackets)-1)
                outfit.append(wardrobe.jackets[index])

        
        #ADD ACCESSORIES
        if currentType != "accessories":
            if pAccessories > 50 and len(wardrobe.accessories) > 0:
                index = randint(0,len(wardrobe.accessories)-1)
                outfit.append(wardrobe.accessories[index])
            
        

        #OUTFIT COMPLETE - return
        return outfit

    def ai_outfit(self,item0):
        poolFile = "OutfitPool.csv"

        self.collaborative_filtering(item0.get_clothing_id(), poolFile)

        #array holds outfit template
        outfitTemplate = self.create_outfit_template(item0)
        if outfitTemplate == -1:
            return -1

        #array to hold actual outfit
        outfit = []
        
        #item0 must be in outfit
        outfit.append(item0)

        
        with open(poolFile, 'r', encoding='utf8') as f:
            #skip first line
            f.readline()

            id = f.readline().split(',',1)[0]
            while id!=None and id!='' and (outfitTemplate):
                currentItem = Clothing("","","")
                

                counters = {"top":0,
                            "bottom":0,
                            "onepiece":0,
                            "jackets":0,
                            "shoes":0,
                            "accessories":0}
                
                wardrobeIndices =  {"top":0,
                                    "bottom":1,
                                    "onepiece":2,
                                    "jackets":3,
                                    "shoes":4,
                                    "accessories":5}

                for type in wardrobe.clothes:
                    for item in type:
                        if item.get_clothing_id() == id:
                            
                            currentItem = item
                            break
                
                #update correct counters to keep track of how many of a type have been considered
                
                counters[currentItem.get_clothing_type()] += 1

                #calculate which index of the wardrobe the item is in
                wardrobeIndex = wardrobeIndices[currentItem.get_clothing_type()]


                #add to outfit if current item is one that matches one of the types in outfit template
                for elt in outfitTemplate:
                    if currentItem.get_clothing_type() == elt:

                        if counters[currentItem.get_clothing_type()] < len(wardrobe.clothes[wardrobeIndex]):
                        #If current item is not the last of its type

                            #30% item will not be added and next item will be considered instead
                            if randint(0,100) > 40:
                                outfit.append(currentItem)
                                outfitTemplate.remove(elt)
                                print("item skipped")

                        else:
                            #last of its kind 
                            #must be added
                            outfit.append(currentItem)
                            outfitTemplate.remove(elt)



                id = f.readline().split(',',1)[0]

        return outfit


    #applies Pearson Correlation Coefficient to all clothes pairs
    #to find similar items
    #to use to generate outfit
    def collaborative_filtering(self, item0, saveFileName):
        matrix = pd.read_csv("clothingMatrix.csv",index_col = 'i')

        item_similarity_df = matrix.corr(method='pearson')
        item_similarity_df.fillna(0)

        similar_score = item_similarity_df[item0].sort_values(ascending=False)

        similar_score.to_csv(saveFileName,header=False)


    def create_outfit_template(self,item0):
        currentType = item0.get_clothing_type()

        #array to hold outfit pieces - Clothing objects
        outfitElts = []


        #probabilities
        pBase = randint(0,100)
        pTop = 100
        pAccessories = randint(0,100)
        pJackets = randint(0,100)


        #create outfit
        if currentType == "onepiece" or currentType=="bottom":
            if currentType=="onepiece":
                pTop = randint(0,100)
        else:
            #CREATE OUTFIT BASE
            if ((pBase < 20) and (len(wardrobe.onepieces) >0)):
                #onepiece
                outfitElts.append("onepiece")
                pTop = randint(0,100)
            elif (len(wardrobe.bottoms) >0):
                #bottom
                outfitElts.append("bottom")
            else:
                toast("Not enough pieces to create an outfit - please add some trousers/skirts etc. to the 'Bottoms' section to continue")
                return -1
        
        if currentType != "top":
            #ADD TOP (depends on pTop - 1 for bottoms, 0 or 1 for onepieces)
            if pTop > 50 and len(wardrobe.tops) > 0:
                outfitElts.append("top")
            else:
                if len(wardrobe.tops) <= 0:
                    toast("Not enough pieces to create an outfit - please add some tops/shirts etc. to the 'Tops' section to continue")
                    return -1

        if currentType != "shoes":
            #ADD SHOES - always 1
            if len(wardrobe.shoes) > 0:
                outfitElts.append("shoes")
        
        if currentType != "jackets":
            #ADD JACKET - 0 or 1
            if pJackets > 50 and len(wardrobe.jackets) > 0:
                outfitElts.append("jackets")

        
        #ADD ACCESSORIES
        if currentType != "accessories":
            if pAccessories > 50 and len(wardrobe.accessories) > 0:
                outfitElts.append("accessories")
            
        

        #OUTFIT COMPLETE - return
        return outfitElts

    def get_outfit_ids(self,outfit):
        ids = []

        
        for item in outfit:
            ids.append(item.get_clothing_id())
        return ids

    def rateOutfit(self,outfit,rating):
        matrix.rate(self.get_outfit_ids(outfit),rating)
        
#--------------------------------------------------------------------------------------------------

#MY CLASSES 
class Clothing():

    #initialise object with id, address, type
    def __init__(self, input_clothing_id, input_image_address, input_clothing_type):
        self.clothing_id = input_clothing_id
        self.image_address = input_image_address
        self.clothing_type = input_clothing_type


    #getter methods for each attribute
    def get_clothing_id(self):
        return self.clothing_id

    def get_image_address(self):
        return self.image_address
    
    def get_clothing_type(self):
        return self.clothing_type


#class created to store all of the clothing objects
class Wardrobe():

    def __init__(self, clothes_filename):
        #if new type added, edit add_item_to_correct_array method too
        self.tops = []
        self.bottoms = []
        self.onepieces = []
        self.jackets = []
        self.shoes = []
        self.accessories = []
        self.create_clothing_objects(clothes_filename)    
        self.clothes = [self.tops, self.bottoms, self.onepieces, self.jackets, self.shoes, self.accessories]    

    def create_clothing_objects(self, clothes_filename):
        #called when program first loads
        file = open(clothes_filename, "r")

        for line in file:
            info = line.strip( "\n").split(",")
            new_item = Clothing(info[0], info[1], info[2])
            self.add_item_to_correct_type_array(new_item)


    def add_item_to_correct_type_array(self,item):
        #when a new item is added
        #add to correct place in wardrobe
        type = item.get_clothing_type()
        if type == "top":
            self.tops.append(item)
        elif type == "bottom":
            self.bottoms.append(item)
        elif type == "onepiece":
            self.onepieces.append(item)
        elif type == "jackets":
            self.jackets.append(item)
        elif type == "shoes":
            self.shoes.append(item)
        elif type == "accessories":
            self.accessories.append(item)
        else:
            print("Error appending item to correct array")

    #prints to terminal
    #for checks
    #eg to count number of items in wardrobe
    def printWardrobe(self):
        count = 0
        total = 0
        for type in self.clothes:
            
            print("\n\nArray " + str(count))

            for item in type:
                print (item.get_clothing_id())
                total+=1

            count+=1

        print("\n\nNumber of clothing types: " + str(len(self.clothes)))
        print("Number of items total: " + str(total))
    

#--------------------------------------------------------------------------------------------------


class MainApp(MDApp):
    def __init__(self, **kwargs):
        self.title = "Pocket Stylist"

        #instantiate wardrobe object
        global wardrobe
        wardrobe = Wardrobe("clothes.csv")
        wardrobe.printWardrobe()

        #instantiate ratings matrix
        #populate with existing ids if empty (used for testing)
        global matrix
        matrix = ClothingMatrix("clothingMatrix.csv")
        if matrix.matrix.empty:
            for type in wardrobe.clothes:
                for item in type:
                    matrix.addIdToMatrix(item.get_clothing_id())

        super().__init__(**kwargs)


    def build(self):
        Window.size = (350, 600)
        
        #colour theme for app
        self.theme_cls.primary_palette = "Orange"

        return MyLayout()

if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
    MainApp().run()
