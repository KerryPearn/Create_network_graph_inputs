# coding: utf-8

# # Preparing Personality Disorder data as input for Gephi (Gephi is an open source network analysis & visualisation software tool)

# ## Overview of the code
# 
# ### Code functionality
# This code takes 1 input file (the Personality Disorder dataset) and creates 3 output files (the inputs files required by Gephi to create a network graph).
# 
# The network graph is a visual representation of the order in which Personality Disorder patients access services: the nodes of the network are the individual services (the Ward Teams); the edges (links between the nodes) represents the order (chronological) in which a patient has accessed the services.
# 
# It is possible to either include all of the PD data in the network graph, or to include only a subset of the PD data in the network (for example, just those services in North Devon, or just a single patient).  When selecting a subset of the data for the network, there are options about how to represent the information that is excluded from the selection.  This will be covered later in the notebook.
# 
# Gephi requires two input files in order to create a network graph:
# 
# 1. Node file: 
# The <em>Node</em> file contains information (categorical or continuous) about each node, stored per row.  In this example the Node file will contain: a unique numerical node ID; the node name (the Ward Team); the length of stay at the Ward Team (mean and median); the setting (community, inpatient, out of area, or mixture for the instances when a node represents a combination of many WardTeams).
# 
# 2. Edge file: 
# The <em>Edge</em> file contains data about the links between two nodes, stored per row.  A link is defined by the Source Node ID and the Target Node ID (corresponding to the ID used in the Node file).  The type of each link is defined as either directed or undirected (for our case the links are all directed, because a patient accesses a service in a particular order).  The weight is the frequency that the link has been used.  A unique ID is provided for each edge.
# 
# A third output file is created by this code (but not used as an input file for Gephi):
# 
# 3. Service movement file: 
# The <em>Service movement</em> file is an interime working file that contains a matrix of the frequency of use of the links from all services to all other services (a row and column per service [Ward Team]).  The <em>Edge</em> file is created driectly from the <em>Service movement</em> file. 
# 
# ### Code Structure
# In addition to the main code, the code is divided into 14 functions (a function is defined by beginning with <em>def ______():</em> and ending with <em>return</em>. It is worth creating a function for script that is used multiple times, or to break code down into smaller chunks. 
# 
# Three of the functions create and output each of the three output files: (1) <em>output_SM_file()</em>, (2) <em>output_Edge_file()</em>, (3) <em>output_Node_file()</em>.
# 
# Function (4) <em>create_output_files()</em> runs sequentially through the three functions that create and output each of the three output files:<em>output_SM_file()</em>, <em>output_Edge_file()</em>, <em>output_Node_file()</em>.
# 
# Function (5) <em>add_columns_wardteamcatcode()</em> adds the numerical representation of the WardTeam column to the provided pandas dataframe.  The unique ID runs from 1 to n.  When this column is used as the row and colmun referrence for the matrix servMove, need to always -1 from the ID so it runs from 0 to n-1. 
# 
# Function (6) <em>create_new_ward_and_setting_columns(subgroup_info,DATA_SG,group)</em>
# 
# Function (7) <em>make_filename()</em> formats the provided string into the required filename.
# 
# Function (8) <em>set_dictionary_for_filenames()</em>: Sets the directory (file_output_info) that contains the filenames for input and output files.
# 
# Function (9) <em>clean_data(DATA)</em>: Receives a Pandas dataframe (DATA) containing the PD data. Cleans the data
# & returns the Pandas dataframe
#     
# Function (10) <em>calculate_variables(DATA)</em>: Receives a Pandas dataframe (DATA) containing the PD data. Changes the format of the date columns and calculates the length of stay (LoS). Returns the Pandas dataframe
#     
# Function (11) <em>delete_zero_LoS(DATA)</em>: Receives a Pandas dataframe (DATA) containing the PD data.  Removes any instance with a negative LoS. Returns the Pandas dataframe
#         
# Function (12) <em>sort_data(DATA)</em>: Receives a Pandas dataframe (DATA) containing the PD data.  Sorts the data by patient and orders their admissions chronologically on the date the service was accessed
#     
# Function (13) <em>create_DATA_with_one_OOA_node(DATA_OneOOA)</em>: Dupicates the PD data (DATA) and represents all of the OOA nodes as one single node. Changes all of the OOA node WardTeams to "All OOA Services".
# 
# Function (14) <em>create_network_data_for_subgroup(subgroup_info,file_output_info)</em>: Passed a dictionary, pandas dataframe and the subgroup in focus.  Adds 2 new columns: newWardTeam & Setting.  Depending on the value of subgroup_info['REPRESENT_REMOVED'] these new columns are either duplicate WardTeam & Setting (if not representing the excluded instances as a single subgroup node) but these 2 columns need to be present for consistency in the code to use these column names.  Or copy WardTeam & Setting & change the values for the subgroups not in focus (if representing the excluded instances as a single subgroup node)
# 
# The main code reads in the Personality Disorder dataset, calls the functions to clean and sort the data, and then prepares the necessary rows to be passed to function <em>create_output_files()</em> that calls the three functions in turn to create the output files.
# 
# First let's define the functions.

# ## Import the libraries

# In[39]:

import pandas as pd
import numpy as np
import igraph
import datetime

# ## Function make_filename()
# Function <em>make_filename()</em> is passed <em>filename</em> that contains the name to represent the subgroup of the data (taken from one of the categories in the PD data file) and is used to create a subgroup specific filename.  
# 
# If <em>filename</em> is a string then it is necessary to remove any charactor that is not conventionally used as a filename, and so replacing these characters (",", ".", " ") with an underscore ("_").
# 
# If <em>filename</em> is not a string, then it is necessary to represent the values as an integer.
# 
# The function returns <em>filename</em> with these replacements.
# 

# In[40]:

def make_filename(filename):
    """Formats filename, by replacing certain characters with underscore"""
    try:
        filename = filename.replace(', ', '_')
        filename = filename.replace(' ', '_')
        filename = filename.replace('.', '_')
        filename = filename.replace(',', '_')
    except:
        filename=int(filename)
    return(filename)


# ## Function add_columns_wardteamcatcode()
# Function <em>add_columns_wardteamcatcode()</em> is passed a pandas dataframe (the PD data to be represented as a network, so either the full dataset, or a subgroup), and adds two columns in order to format the WardTeam column (object) into a unique numerical ID that can be used as the nodes reference in the output file. 
# This is done in two stages: WardTeamCat (converts the object to a categorical variable) and WardTeamCatCode (converts the categorical variable to the unique numerical ID).

# In[41]:


def categorise_columns(file_output_info):
    """Converts the WardTeam column into a numerical ID field"""
    
    #To have categories represented as numbers, first need data type as categories  
    file_output_info['DATA_SG']['wardTeamCat'] = file_output_info['DATA_SG']['newWardTeam'].astype('category')
    
    #Then store the categories as the numerical codes
    file_output_info['DATA_SG']['wardTeamCatCode'] = file_output_info['DATA_SG']['wardTeamCat'].cat.codes + 1
    return file_output_info


# ## Function output_SM_file()
# 
# This is the first in a series of 3 functions that outputs a file.
# 
# This function recieves the PD data as a pandas dataframe (DATA_SG), from which to create the network.  This data is grouped by patient and ordered chronologically on the date the services they accessed (.ReferralDate).
# This function returns a NumPy array (<em>servMove</em>) with a row and column for each unique WardTeam in the passed Pandas dataframe.  The values stored are the frequency a patient chronologically used a service following another service.
# 
# <em>servMove</em> is initialised as a matrix of zeros.
# 
# Go through the <em>DATA_SG</em> records by patient.  Use the current (j) <em>wardTeamCatCode</em> to set the row, and the next (j+1) wardTeamCatCode to set the column [need to use -1 as the codes run from 1 to n, whereas row and column reference run from 0 to n-1].  Increment the respective element in the <em>servMove</em> array (row n: from service, column m: to service) by +1.
# 
# The <em>servMove</em> array is written to an output file (location and filename is passed into the function by 5 arguments) and also returned to the main code.

# In[42]:

def output_SM_file(file_output_info):#DATA_SG, FOLDER, FILESTART, FILEMIDDLE, FILEEND, FILEEX):
    """Creates the Service Movement numpy array from the Personality Disorder data
    The numpy array is used in function output_Edge_file()), and also outputted to a csv file
    Recieves the PD data as a Pandas dataframe (DATA_SG), could either be the whole network or a subgroup. 
    The data is already grouped by patient and ordered chronologically on the date the services they accessed (.ReferralDate). 
    Returns a NumPy array (servMove) with a row and column for each unique WardTeam in the passed Pandas dataframe. 
    The values stored in the array are the frequency patients chronologically used a service following another service."""
    
    #set up a matrix of zeros, with number of columns and rows = number of wardTeams 
    #Each entry will record the frequency a patient chronologically used a service following another service
    servMove = np.zeros((max(file_output_info['DATA_SG'].wardTeamCatCode), max(file_output_info['DATA_SG'].wardTeamCatCode)))

    #stores the number of patients that only have 1 service use (no edges can be recorded for that patient)
    singles = 0
    #get a vector of unique patient ID's
    clientIDUni = file_output_info['DATA_SG'].ClientID.unique()             

    # loop through each unique ClientID
    for ID in clientIDUni:                              
        #take the wardTeam column for the instances for the ClientID
        cWardTeam = file_output_info['DATA_SG'][file_output_info['DATA_SG'].ClientID == ID].wardTeamCatCode 
        l = len(cWardTeam)
        if (l > 1):                                       #if more than 1 admission, then can do source and target
            for j in range(0,(l - 1)):                    #Go through each service use
                # Record the use from Source (this service) and Target (next service)
                servMove[int(cWardTeam.iloc[j]) - 1,int(cWardTeam.iloc[j + 1]) - 1] += 1 
        else:
            #If 1 entry then record the clients accessing only one service during this time period
            singles = np.vstack((singles,ID))               

    #Create the output filename
    FileNameSM = (file_output_info['FILESTART'] + file_output_info['FILEMIDDLE'] + 
                  file_output_info['FILEENDSM'] + file_output_info['FILEEX'])

    #output service movement matrix as csv
    np.savetxt(file_output_info['FOLDER'] + FileNameSM, servMove, delimiter = ",")       
    return servMove


# ## Function output_Edge_file()
# 
# This is the second in a series of 3 functions that outputs a file.  Uses the <em>servMove</em> array created in function <em>output_servMove_file()</em> to create and output the Edge file.
# 
# This function recieves the NumPy array <em>servMove</em> with a row and column for each unique WardTeam.  The values stored are the frequency a patient chronologically used a service following another service.
# 
# A NumPy array (<em>edges</em>) is initialised with a single row with 3 columns of zero values.  The code loops through each row of <em>servMove</em> (which is a WardTeam) and for any column with a value greater than zero, a row is added to the edges NumPy array to store the row number (source WardTeam ID) the colmun number (the target WardTeam ID) and the recorded value (the frequency of patients that have used that link).
# 
# The <em>edges</em> NumPy matrix is cleaned to remove the redundant first row used to initialise the matrix.
# The NumPy array (<em>edges</em>) now contains a row per link.  Convert to a Pandas dataframe and output as a csv file
# 
# The <em>edge</em> file is written to an output file (location and filename is passed into the function by 5 arguments).

# In[43]:

def output_Edge_file(servMove, file_output_info):#FOLDER, FILESTART, FILEMIDDLE, FILEEND, FILEEX):
    """Creates the EDGE file for Gephi (outputs a csv file) from the servMove NumPy array
    Recieves the NumPy array servMove with a row and column for each unique WardTeam. 
    The values stored are the frequency a patient chronologically used a service following another service.
    For any value > 0 in servMove, a row in the EDGE file is created, with 5 columns:
    1) Source node ID [the servMove row] 
    2) Target node ID [the servMove column]
    3) Type [for this case, always DIRECTED]
    4) Edge ID [unique]
    5) Frequency of patient using the edge"""

    #initialise the numpy array (delete this redundant row later)
    edges = np.zeros((1,3))              
    lenRow = servMove.shape[0]           #number of rows (the number of wardTeams)
    for i in range (0,lenRow):           #for loop to extract the used Source-Target combinations, and their activity
        for j in range(0,lenRow):
            if (int(servMove[j, i]) > 0):
                #Record an edge for any Source-Target which has been used (activity>0)
                rowData = np.array([[j + 1,i + 1, int(servMove[j, i])]])    #Source, Target, Activity
                edges = np.vstack((edges,rowData))                    #Add the row onto the numpy array
    edges=edges.astype(int)                 
    edges = edges[1:edges.shape[0], :]          #clean up edges matrix, remove the superflous first row
    lenEdge = edges.shape[0]                    #number of rows (number of Source-Target combinations)
    edgetype = np.repeat("Directed", lenEdge)   #change depending on whether producing a directed or undirected graph
    edgeid = np.arange(0, lenEdge)              #Create a unique edgeid for the output file
    edges = np.vstack((edges[:, 0], edges[:, 1], edgetype, edgeid, edges[:, 2])) #create the output file
    edges = np.transpose(edges)                  #need to transpose the data (currently in rows, need in columns)
    edgesdf = pd.DataFrame(edges, columns = ['Source', 'Target', 'Type', 'Id', 'Weight'])
    
    #Create the output filename
    FileNameEdge = (file_output_info['FILESTART'] + file_output_info['FILEMIDDLE'] + 
                   file_output_info['FILEENDEDGE'] + file_output_info['FILEEX'])
    #output edges list as csv
    edgesdf.to_csv(file_output_info['FOLDER'] + FileNameEdge, sep = ',')           
    return


# ## Function output_Node_file()
# 
# This is the third in a series of 3 functions that outputs a file.  Outputs the <em>Node</em> file.
# 
# This function recieves the PD data as a Pandas dataframe (<em>DATA_SG</em>), from which to create the network, and creates a reference file for the nodes (WardTeams), a row per node.
# 
# Using the Pandas function "groupby" to calclate the mean and median LoS.
# 
# Creates a NumPy array (<em>nodes</em>) with a row per node storing the nodes ID, name, mean LoS, median Los, Setting.  The numpy array is converted to a Pandas dataframe.
# 
# The <em>node</em> Pandas dataframe is written to an output csv file (location and filename is passed into the function by 5 arguments).
# 

# In[44]:

def output_Node_file(file_output_info):#DATA_SG, FOLDER, FILESTART, FILEMIDDLE, FILEEND, FILEEX):
    """Creates the NODE input file for Gephi (outputs a csv file) from the PD data
    Recieves the PD data as a Pandas dataframe (DATA_SG), could either be the whole network or a subgroup. 
    Creates a NumPy array containing a reference list for the nodes (WardTeams), a row per node.
    NumPy array is outputed as a csv file"""
#    ***CREATE THE NODE FILE***

    #Calculate mean and median LoS using pandas groupby function
    daysMeans = file_output_info['DATA_SG'].groupby('wardTeamCatCode')['LoSdays'].mean()
    daysMedians = file_output_info['DATA_SG'].groupby('wardTeamCatCode')['LoSdays'].median()

    #Take a single case of occurence of WardTeamCat, Code & Setting
    df = pd.DataFrame()
    df['wardTeamCat'] = file_output_info['DATA_SG'].wardTeamCat
    df['wardTeamCatCode'] = file_output_info['DATA_SG'].wardTeamCatCode
    df['Setting'] = file_output_info['DATA_SG'].newSetting

    # keep one case for each WardTeam
    df.drop_duplicates(subset = ['wardTeamCat', 'wardTeamCatCode', 'Setting'], inplace = True)
    df.sort_values('wardTeamCatCode', inplace = True)

    #Join all output columns as numpy array, transpose, and store as pandas for easier file formatting
    nodes = np.vstack((df.wardTeamCatCode, df.wardTeamCat, daysMeans, daysMedians, df.Setting))
    nodes = np.transpose(nodes)
    nodesdf = pd.DataFrame(nodes,columns = ['ID', 'Label', 'MeanLoS', 'MedianLoS', 'Setting'])
    
    #Create the output filename from passed in variables, and output the nodedf as a csv file 
    FileNameNode = (file_output_info['FILESTART'] + file_output_info['FILEMIDDLE'] + 
                   file_output_info['FILEENDNODE'] + file_output_info['FILEEX'])

    nodesdf.to_csv(file_output_info['FOLDER'] + FileNameNode, sep = ',')
    return


# ## Function create_output_files()
# 
# The function calls the series of three functions to create the three output files.
# 
# This function is called for each subset of data going to be represented in a network.  It gets passed a Pandas dataframe of the PD data (<em>DATA_SG</em>) and the variables contining the filename and file location.

# In[45]:


def create_output_files(file_output_info):#DATA_SG, FOLDER, FILESTART, FILEMIDDLE, FILEENDSM, FILEENDEDGE, FILEENDNODE, FILEEX):
    
    """Called for each subset of data going to be represented in a network. 
    
    Function is passed a dictionary (file_output_info).
    
    Dictionary contains:
    "DATA_SG" :  Pandas dataframe of the PD data (updated for each subgroup of data)
    "FOLDER" : String containing the data folder name that sits beneath the python script
    "FILESTART" : String containing the input file name, and is used as the start of all the output file names 
    "FILEMIDDLE : String containing the subgroup specific part of the output file name (updated for each subgroup of data)
    "FILEENDSM" : String containing the end of the ServMove output file name
    "FILEENDEDGE" : String containing the end of the Edge output file name
    "FILEENDNODE" : String containing the end of the Node output file name
    "FILEEX" : String containing the file extension (both input and output)
        
    Calls series of three functions to create the three output files
    """
    
    servMove =output_SM_file(file_output_info)#DATA_SG, FOLDER, FILESTART, FILEMIDDLE, FILEENDSM, FILEEX)
    output_Edge_file(servMove, file_output_info)#FOLDER, FILESTART, FILEMIDDLE, FILEENDEDGE, FILEEX)
    output_Node_file(file_output_info)#DATA_SG, FOLDER, FILESTART, FILEMIDDLE, FILEENDNODE, FILEEX)
    return


# ## Function set_filenames()
# 
# The function sets the filenames to be used or the input and output files

# In[46]:

def set_dictionary_for_filenames():
    """Sets the directory (file_output_info) that contains the filenames for input and output files"""
    
    #Create a dictionary with these objects that will keep these values for all the codee.
    #Two additional objects will be included and changed each time look at a dfferent subgroup
    file_output_info = {"FOLDER" : 'Data/', 
                        "FILESTART" : 'ServUse15To18v6', 
                        "FILEENDSM" : '_SM_jupyter', 
                        "FILEENDEDGE" : '_edgeList_jupyter', 
                        "FILEENDNODE" : '_nodeList_jupyter', 
                        "FILEEX" : '.csv'}
    
    return file_output_info


# ### Function clean_data()  
# Replace "Nan" with "None" in 6 columns
# 
# Replace "Nan" with the date the data was acquired for column ReferralDischarge.  This is due to the admission beign ongoing at the time the data was accessed.
# 
# Remove rows with no ReferralDate
# 
# This was missed in the data cleaning stage, do it here instead.
# 
# Ward Team "Harford" has 2 different Settings, either Inpatient or OOA.  
# This means that Harford exists twice after the "no_duplicates" function.
# Rename the WardTeams as "Harford inpatient", and "Harford OOA".

# In[47]:


def clean_data(DATA):
    """Receives a Pandas dataframe (DATA) containing the PD data.  
    Cleans the data
    Returns the Pandas dataframe"""
    
    DATA.ReferralSource.replace(np.nan,"None", inplace = True)
    DATA.ReferralDate.replace(np.nan,"None", inplace = True)
    DATA.Locality_Edit.replace(np.nan,"None", inplace = True)
    DATA.Cluster.replace(np.nan,"None", inplace = True)
    DATA.AgeAtRefGroup.replace(np.nan,"None", inplace = True)
    DATA.GenSpecialty_Age.replace(np.nan,"None", inplace = True)

    DATA.ReferralDischarge.replace(np.nan,"18/02/2018", inplace = True)

    DATA = DATA[DATA.ReferralDate != "None"]

#    newWardTeam = DATA.WardTeam.copy(deep = True)
#    newWardTeam[(DATA.WardTeam == 'Harford') & (DATA.Setting == 'Inpatient')] = 'Harford Inpatient'
#    newWardTeam[(DATA.WardTeam == 'Harford') & (DATA.Setting == 'OOA')] = 'Harford OOA'
#    del DATA['WardTeam']
#    DATA['WardTeam'] = newWardTeam
    np1 = DATA.WardTeam.values
    np2 = DATA.Setting.values
    np1[(np1 == 'Harford') & (np2 == 'Inpatient')] = 'Harford Inpatient'
    np1[(np1 == 'Harford') & (np2 == 'OOA')] = 'Harford OOA'
    del DATA['WardTeam']
    DATA.loc[:,'WardTeam'] = np1
    
    return DATA


# ## Function calculate_variables()
# Calculate Length of Stay - need to convert the format of the date columns to do this calculation

# In[48]:


def calculate_LoS(DATA):
    """"Receives a Pandas dataframe (DATA) containing the PD data.
    Changes the format of the date columns and calculates the length of stay (LoS).
    Returns the Pandas dataframe"""
    
    DATA['ReferralDate'] = pd.to_datetime(DATA['ReferralDate'], format = "%d/%m/%Y")
    DATA['ReferralDischarge'] = pd.to_datetime(DATA['ReferralDischarge'], format = "%d/%m/%Y")
    DATA['LoSdays'] = (DATA.ReferralDischarge - DATA.ReferralDate).astype('timedelta64[D]')
    return DATA


# ## Function delete_zero_LoS()
# Remove rows with a negative LoS.  

# In[49]:


def delete_zero_LoS(DATA):
    """"Receives a Pandas dataframe (DATA) containing the PD data.  
    Removes any instance with a negative LoS
    Returns the Pandas dataframe"""
    
    DATA = DATA[DATA.LoSdays >= 0]
    return DATA


# ## Function sort_data()
# Sort the data into blocks for each clientID with chronological ReferralDate (needs to be in format "%d/%m/%Y", else will order by day number first)

# In[50]:


def sort_data(DATA):
    """Receives a Pandas dataframe (DATA) containing the PD data. 
    Sorts the data by patient and orders their admissions chronologically on the date the service was accessed"""
    
    DATA = DATA.sort_values(['ClientID','ReferralDate'], ascending = [True,True])
    return DATA


# ## Function create_DATA_with_one_OOA_node()
# 
# Create another Pandas dataframe that represents all of the OOA nodes as 1 single node (by changing all the OOA nodes WardTeam names to "All OOA Services").
# 

# In[51]:


def create_DATA_with_one_OOA_node(DATA_OneOOA):
    """Dupicates the PD data (DATA) and represents all of the OOA nodes as one single node.
    Changes all of the OOA node WardTeams to "All OOA Services" """
    
    np1 = DATA_OneOOA.WardTeam.values
    np2 = DATA_OneOOA.Setting.values
    np1[np2 == 'OOA'] = str('All OOA services')
    del DATA_OneOOA['WardTeam']
    DATA_OneOOA['WardTeam'] = np1
    return DATA_OneOOA


# ## Function create_new_ward_and_setting_columns()
# 
# Function is passed a dictionary (subgroup_info), a pandas dataframe (DATA_SG: the PD data to be represented as a network, so either the full dataset, or a subgroup), and the subgroup in focus (group).
# 
# Two new columns are added to the dataset DATA_SG: newWardTeam & newSetting.
# 
# Either duplicate WardTeam & Setting (if not representing the excluded instances as a single subgroup node) but these 2 columns need to be present for consistency in the code to use these column names
# 
# Or copy WardTeam & Setting & change the values for the subgroups not in focus (if representing the excluded instances as a single subgroup node)

# In[52]:


def create_new_ward_and_setting_columns(subgroup_info,file_output_info,group):
    """Passed a dictionary, pandas dataframe and the subgroup in focus.
    Adds 2 new columns: newWardTeam & Setting
    Depending on the value of subgroup_info['REPRESENT_REMOVED'] these new columns are either duplicate WardTeam & Setting
    (if not representing the excluded instances as a single subgroup node) but these 2 columns need to be present for 
    consistency in the code to use these column names
    Or copy WardTeam & Setting & change the values for the subgroups not in focus (if representing the excluded 
    instances as a single subgroup node)"""
#    DATA_SG = file_output_info['DATA_SG'].copy(deep = True)
    if subgroup_info['REPRESENT_REMOVED']:
        #Change required for the other subgroups
        #Replace WardTeam name with Subgroup name. Replace Setting with the string Mixture
        npWardTeam = file_output_info['DATA_SG'].WardTeam.values#.copy(deep = True)
        npSetting = file_output_info['DATA_SG'].Setting.values#.copy(deep = True)#[:]
        npColumn = file_output_info['DATA_SG'][subgroup_info['COLUMN']].values#.copy(deep = True)#[:]
        for notgroup in file_output_info['DATA_SG'][subgroup_info['COLUMN']].unique():
            if group != notgroup:
                npWardTeam[npColumn == notgroup] = str(subgroup_info['SUBGROUP_NODE_NAME'] + str(notgroup))
                npSetting[npColumn == notgroup] = str('Mixture')
            file_output_info['DATA_SG']['newWardTeam'] = npWardTeam
            file_output_info['DATA_SG']['newSetting'] = npSetting
    else:
        #No change required as removed the other subgroups.  Duplicate existing columns: WardTeam & Setting
        #Duplicates WardTeam and Setting columns.
        #For subgroups that do not require the contents of these columns to be changed.
        #So other functions can still use 'newWardTeam' and 'newSetting' regardless of being changed or not"""
        file_output_info['DATA_SG']['newWardTeam'] = file_output_info['DATA_SG']['WardTeam']
        file_output_info['DATA_SG']['newSetting'] = file_output_info['DATA_SG']['Setting']
#    file_output_info['DATA_SG'] = DATA_SG
    return file_output_info


# ## Function create_network_data_for_subgroup()
# 
# When creating data for a subgroup, this function loops through each of the subgroup categories and creates the input files for Gephi for each.
# 
# The function is passed two dictionaries.
# 
# Dictionary 1: subgroup_info
# 
# 'DATA_COMPLETE': the complete PD data set (either with OOA services as individual nodes, or as a single node)
# 'COLUMN': the column that contains the subgroup categories.  A set of output files will be created for each category in this column.
# 'REPRESENT_REMOVED': how to deal with the excluded data (the other subgroups).  
#     0: Do no represent the removed data
#     1: Represent the removed data by replacing the WardTeam name with the subgroup name (see 'SUBGROUP_WARDTEAM')
# 'SUBGROUP_FILENAME' : The string to state which column of data is used to divide the data into subgroups
# 'SUBGROUP_WARDTEAM' : The string to replace the WardTeam name for the excluded subgroups, the specific subgroup will to tagged onto the WARDTEAM name.
# 
# Dictionary 2: file_output_info
# 
# These 6 are constant throughout the program and unchanged here
# "FOLDER" : The subfolder where the input and output data are located
# "FILESTART" : The filename of the input data, this is used for the start of the output filenames
# "FILEENDSM" : End of the output filename for the <em>Service movement</em> data
# "FILEENDEDGE" : End of the output filename for the <em>Edge</em> data
# "FILEENDNODE" : End of the output filename for the <em>Node</em> data
# "FILEEX" : File extension for the input and output files
# 
# These 2 change for each definition of data group, and have their value defined in this function
# "FILEMIDDLE" : Middle of the output filename to specify the subgroup
# "DATA_SG" : Prepared PD dataset in terms of the subgroup, for the create_output_files function
# 
# If the dataset is not going to represent the removed subgroups then the data is filtered by the subgroup in focus.
# 
# Four new columns are added to the dataset (two in <em>create_new_ward_and_setting_columns()</em>, two in <em>add_columns_wardteamcatecode()</em>).
# 
# The updated directory <em>file_output_info</em> is passed to <em>function create_output_files()</em>.

# In[53]:


def create_network_data_for_subgroup(subgroup_info,file_output_info):
    """If looking at a subset of data for the network, loop through the categories within the column and create output file for each
    If not represent the removed data then just take the filtered rows
    """
    subgroup_info['DATA'] = subgroup_info['DATA'][subgroup_info['DATA'][subgroup_info['COLUMN']] != "None"] #Remove rows without a GenSpecialty_Age value
    for group in subgroup_info['DATA'][subgroup_info['COLUMN']].unique():
        if group != "None":
            filename = make_filename(group)
            if subgroup_info['REPRESENT_REMOVED']==0:
                file_output_info['DATA_SG'] = subgroup_info['DATA'][subgroup_info['DATA'][subgroup_info['COLUMN']] == group].copy(deep = True) #Deep copy.
            else:
                file_output_info['DATA_SG'] = subgroup_info['DATA'].copy(deep = True) #Deep copy.
            file_output_info=update_dictionary(subgroup_info,file_output_info,group,filename)
            create_output_files(file_output_info)
    return


def update_dictionary(subgroup_info,file_output_info,group,filename):
    """The data is nearly ready to be passed to the final set of functions to create the Gephi input files, just need to 
    1. Add 2 columns to the pandas dataframe
    2. Add the numerical representation of WardTeams present in the pandas dataframe
    3. Update a dictionary"""
    file_output_info = create_new_ward_and_setting_columns(subgroup_info,file_output_info,group)
    file_output_info = categorise_columns(file_output_info)
    #Update the 2 objects in the directory
    file_output_info ['FILEMIDDLE'] = str(subgroup_info['SUBGROUP_FILENAME']) + str(filename)
    #Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    return(file_output_info)
    

# In[54]:

if __name__ == '__main__':      
    
    file_output_info=set_dictionary_for_filenames()
    
    
    # ### Read in the data
    # Read in the personality disorder admission data into a pandas dataframe.  This contains dated admissions to a specific ward team.  
    # 
    # <em>Note: needed to add low_memory=False to remove the error: "DtypeWarning: Columns (11,12) have mixed types. Specify dtype option on import or set low_memory=False."</em>
    
    # In[55]:
    
    
    DATA = pd.read_csv(file_output_info['FOLDER'] + str(file_output_info['FILESTART']) + '.csv', low_memory = False)
    
    
    # ### Clean the data.  
    
    # In[56]:
    
    
    DATA = clean_data(DATA)
    
    
    # ### Calculate new variables
    
    # In[57]:
    
    
    DATA = calculate_LoS(DATA)
    DATA = delete_zero_LoS(DATA)
    
    
    # ### Sort the data
    # Sort the data into blocks for each clientID with chronological ReferralDate (needs to be in format "%d/%m/%Y", else will order by day number first)
    
    # In[58]:
    
    
    DATA = sort_data(DATA)
    
    
    # Create another Pandas dataframe that represents all of the OOA nodes as 1 single node (by changing all the OOA nodes WardTeam names to "All OOA Services").
    
    # In[59]:
    
    
    DATA_OneOOA = DATA.copy(deep = True)
    DATA_OneOOA = create_DATA_with_one_OOA_node(DATA_OneOOA)
    
    
    # ### Create the data for the networks
    # In order to create the input files for GEPHI, there are different ways to represent the data depending on the question being asked.
    # 
    # #### OOA Ward Teams.subgroup_info={"DATA_COMPLETE"
    # There are a large number of OOA Ward Teams that are not used as frequently as those in the region.  Including the individual ward teams can add noise to the network (lots of individual nodes) when the important information is that an OOA ward team was used, and not necessrily which OOA ward team.
    # 
    # ##### Choice 1. How to represent the OOA ward teams?
    # Option A. Have one node to represent all OOA wardteams ("_OneOOA" in the output filename)
    # Option B. Keep them as individual nodes.
    # 
    # #### Create networks containing data from one subgroup
    # When want to have a subgroup of the data in the network graph, if the subgroup is not on the patient level and so does not apply to all of an individual patients records (and so a subset of the patient records will be removed) then there's an additional choice.  An example when the subgroup keeps all data for a patient together and so a choice is not necessary: ClientID, or Cluster, or ICD10.
    # An example when the subgroup divides the patient records and a choice is necessary: locality or setting.  If want only WardTeams that are in North Devon then a patients records will not be a complete representation of the services they've accessed.  As each edge on the network is the sequential use of service by a patient, when only having those that are North Devon have a choice about how to represent the removed subgroups (WardTeams in South Devon, Exeter, Devon Wide or OOA). 
    # 
    # ##### Choice 2. How to represent to removed admission data?
    # Option A. Remove the other subgroups (so only keep those WardTeams that have locality North Devon) and the edges in the network represent the order of service use in the subgroup under question (eg services in North Devon) by a patient.  Important to remember that other services from other sugroups (in this case the other regions0 may be used inbetween, but this data is lost.
    # Option B. Instead of removing the other subgroups, rename the WardTeams with the subgroup name and so the edges still represent the chronological order a patient attends a WardTeam and can see true chronological order between the WardTeams accessed by patients in North Devon, and when they access a WardTeam in another locality, South Devon (say), between two North Devon WardTeams.
    # 
    # ### The networks created for the P206 project
    # For the P206 project we created 13 networks.  The code below creates the input files for these 13 networks.  Can use these as a basis to create other networks interested in.
    # 
    # Network 1. Whole Network 
    # Choice 1. Option A. 
    # Choice 2. n/a)
    # 
    # Networks 2 & 3: Each network represents the service use for an individual ClientID (1004961 & 1007835) 
    # Choice 1. Option B [small network so not confuse the visualisation].  
    # Choice 2. n/a [patient data is kept whole]
    # 
    # Networks 4 to 8. A separate network for each locality 
    # Choice 1. n/a [OOA are already grouped as a single node due to the subgrouping].  
    # Choice 2. Option B: Represent the removed subgroups by their own node)
    # 
    # Networks 9 & 10. Network for each of the Clusters 
    # Choice 1. Option A. 
    # Choice 2. n/a
    # subgroup_info={"DATA_COMPLETE"
    # Networks 11 to 12. Network for each General Specialty Age 
    # Choice 1. Option A. 
    # Choice 2. Option B
    # 
    # Network 13. Network for the patients that are <20 (Age Group 1) 
    # Choice 1. Option A. 
    # Choice 2. n/a
    
    # ### Network 1. Whole Network (using one OOA node)
    # Subgroups: NONE. This is the full network
    # Choice 1. Option A. Have one node to represent all OOA WardTeams
    # Choice 2. n/a as not removing subgroups
    
    # In[60]:
    subgroup_info={"DATA" : DATA_OneOOA.copy(deep = True), #Deep copy. Changing DATA_SG does not change DATA
                   "COLUMN" : '',
                   "REPRESENT_REMOVED" : 0,
                   "SUBGROUP_NODE_NAME" : '',
                   "SUBGROUP_FILENAME" : '_OneOOA'}
    #KP need to find a way to set this in update_data
    
    
    file_output_info["DATA_SG"] = DATA_OneOOA.copy(deep = True) #Deep copy. Changing DATA_SG does not change DATA
    
    (file_output_info)=update_dictionary(subgroup_info,file_output_info,"","")
    create_output_files(file_output_info)
     #           DATA_SG = create_new_ward_and_setting_columns(subgroup_info,DATA_SG,group)
     #           DATA_SG = add_columns_wardteamcatcode(DATA_SG)
     #           #Update the 2 objects in the directory
     #           file_output_info ['FILEMIDDLE'] = str(subgroup_info['SUBGROUP_FILENAME']) + str(filename)
     #           file_output_info['DATA_SG'] = DATA_SG                
     #           #Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    
    
    # ### Networks 2 & 3. Network for two individual ClientIDs (1004961 & 1007835)
    # Subgroups: ClientID (just for 2 examples)
    # Choice 1. Option B. Keep OOA nodes separate
    # Choice 2. n/a [Extracting the full patient data]
    # 
    # For each subgroup (ClientID), filter the DATA for just those admissions for the clientID and pass a deep copy of the filtered DATA to DATA_SG (otherwise changes to the columns remain for the rest of the program).  Using DATA and not DATA_OneOOA as having the OOA nodes separate.
    # 
    # Add the unique numberical ID for for WardTeams included in the subgroup data (running form 1 to n), to be used as the Source and Target node ID in the Edge output file.
    # 
    # Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    
    # In[61]:
    
#    quit()
    
    clientID=[1007835,1004961]
    for cID in clientID:
        subgroup_info={"DATA" : DATA[DATA.ClientID == cID].copy(deep = True), #Deep copy. Changing DATA_SG does not change DATA
                       "COLUMN" : '',
                       "REPRESENT_REMOVED" : 0,
                       "SUBGROUP_NODE_NAME" :'',
                       "SUBGROUP_FILENAME" : '_ClientID_'}
        #KP need to find a way to set this in update_data
        file_output_info["DATA_SG"] = DATA[DATA.ClientID == cID].copy(deep = True) #Deep copy. Changing DATA_SG does not change DATA
    
        file_output_info=update_dictionary(subgroup_info,file_output_info,"",cID)
        create_output_files(file_output_info)
    
    
    # ### Networks 4 to 8. Network for each locality (#having a node to represent each of the other subgroups)
    # Subgroups: Locality (North, Exeter, South, Devon, OOA)
    # Choice 1. n/a [OOA are already grouped as a single node due to the subgrouping].  
    # Choice 2. Option B: Represent the removed subgroups by their own node
    # 
    # For each subgroup (each category of Locality in turn), pass a deep copy of the DATA to DATA_SG (otherwise changes to the columns remain for the rest of the program).  Using DATA and not DATA_OneOOA as having the OOA nodes separate.
    # 
    # Edit the WardTeam column for the admissions that are not classified as the Locality category in focus by replacing their WardTeam name with their Locality category (so as to represent the subgroup data not in focus with a single node for their Locality category).
    # 
    # Add the unique numberical ID for for WardTeams included in the subgroup data (running form 1 to n), to be used as the Source and Target node ID in the Edge output file.
    # 
    # Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    
    # In[62]:
    
    
    subgroup_info={"DATA" : DATA.copy(deep = True), #Deep copy. Changing DATA_SG does not change DATA
                   "COLUMN" : 'Locality_Edit',
                   "REPRESENT_REMOVED" : 1,
                   "SUBGROUP_NODE_NAME" :'Locality ',
                   "SUBGROUP_FILENAME" : '_Locality_'}
    create_network_data_for_subgroup(subgroup_info,file_output_info)
    
    # ### Networks 9 & 10. Network for two Clusters (#using one OOA node)
    # Subgroups: Clusters (7, 8)
    # Choice 1. Option A. Have one node to represent all OOA WardTeams
    # Choice 2. n/a as keeping all patient data together
    # 
    # For each subgroup (each category of Cluster in turn), filter the DATA_OneOOA for just those admissions classified as teh Cluster in focus and pass a deep copy of the filtered DATA_OneOOA to DATA_SG (otherwise changes to the columns remain for the rest of the program).  Using DATA_OneOAA and not DATA as having one node to represent all the OOA WardTeams.
    # 
    # Add the unique numberical ID for for WardTeams included in the subgroup data (running form 1 to n), to be used as the Source and Target node ID in the Edge output file.
    # 
    # Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    
    # In[63]:
    
    
    subgroup_info={"DATA" : DATA_OneOOA.copy(deep = True), #Deep copy. Changing DATA_SG does not change DATA
                   "COLUMN" : 'Cluster',
                   "REPRESENT_REMOVED" : 0,
                   "SUBGROUP_NODE_NAME" :'',
                   "SUBGROUP_FILENAME" : '_OneOOA_Cluster_'}
    create_network_data_for_subgroup(subgroup_info,file_output_info)
    
    
    # ### Networks 11 to 12. Network for each General Specialty Age (using one OOA node, having a node to represent the other subgroup)
    # Subgroups: General Specialty (Adult, Old Age)
    # Choice 1. Option A. Have one node to represent all OOA WardTeams
    # Choice 2. Option B. Represent the other subgroups that are removed with a single node for each subgroup
    # 
    # For each subgroup (each category of General Specialty Age in turn), pass a deep copy of the DATA_OneOOA to DATA_SG (otherwise changes to the columns remain for the rest of the program).  Using DATA_OneOAA and not DATA as having one node to represent all the OOA WardTeams.
    # 
    # Edit the WardTeam column for the admissions that are not classified as the General Specialty Age category in focus by replacing their WardTeam name with their General Specialty Age category (so as to represent the subgroup data not in focus with a single node for their General Specialty Age category).
    # 
    # Add the unique numberical ID for for WardTeams included in the subgroup data (running form 1 to n), to be used as the Source and Target node ID in the Edge output file.
    # 
    # Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    
    # In[64]:
    
    
    subgroup_info={"DATA" : DATA_OneOOA.copy(deep = True), #Deep copy. Changing DATA_SG does not change DATA
                   "COLUMN" : 'GenSpecialty_Age',
                   "REPRESENT_REMOVED" : 1,
                   "SUBGROUP_NODE_NAME" :'General Specialty',
                   "SUBGROUP_FILENAME" : '_OneOOA_GenSpecialtyAge_'}
    create_network_data_for_subgroup(subgroup_info,file_output_info)
    
    
    # ### Network 13. Network for the patients that are <20 (Age Group 1) (#using one OOA node)
    # Subgroups: Age At Referral Date (1=<20, 2=20-30, 3=30-40,  4=40-50,  5=50-60,  6>60)
    # Choice 1. Option A. Have one node to represent all OOA WardTeams
    # Choice 2. n/a as keeping all data for each patient together (this subgroup applies to the patient level), or if split, then it will be chronolgical and will then go into the next subgroup age.... no too'ing and fro'ing between subgroups
    # 
    # For each subgroup (each category of Age Group in turn), filter the DATA_OneOOA for just those admissions classified as the Age Group in focus and pass a deep copy of the filtered DATA_OneOOA to DATA_SG (otherwise changes to the columns remain for the rest of the program).  Using DATA_OneOAA and not DATA as having one node to represent all the OOA WardTeams.
    # 
    # Add the unique numberical ID for for WardTeams included in the subgroup data (running form 1 to n), to be used as the Source and Target node ID in the Edge output file.
    # 
    # Call the function that calls the 3 functions in turn to output the files fo Gephi for this subgroup.
    
    # In[65]:
    
    
    subgroup_info={"DATA" : DATA_OneOOA.copy(deep = True), #Deep copy. Changing DATA_SG does not change DATA
                   "COLUMN" : 'AgeAtRefGroup',
                   "REPRESENT_REMOVED" : 0,
                   "SUBGROUP_NODE_NAME" :'',
                   "SUBGROUP_FILENAME" : '_OneOOA_AgeAtRefGroup_'}
    create_network_data_for_subgroup(subgroup_info,file_output_info)