# -*- coding: utf-8 -*-
"""
Created on Sun Oct  2 13:51:22 2016

@author: Olga Acosta
"""

import json
import re, nltk
from nltk.tag import StanfordNERTagger
import subprocess
import os, glob, sys


#Argument: file with format .docx or .PDF
arg1 = sys.argv[1]
arg2 = sys.argv[2]

def get_checker_digit(rut):
    """function that gets the checker digit
    """
    try:
        value = 11 - sum([ int(a)*int(b)  for a,b in zip(str(rut).zfill(8), '32765432')])%11
        return {10: 'K', 11: '0'}.get(value, str(value))
    except ValueError:
        print("Invalid input")

    

def validate_rut(rut):
    """Function validating complete rut
    """
    update_rut = []
    try:
        if rut != []:
            for r in rut:
                r = r.strip()
                if len(r)<=10:
                    checker = get_checker_digit(r[:8])
                    if checker.lower() == r[-1].lower():
                        update_rut.append(r)
                        break
                elif r.find(".")!=-1:
                    update_rut.append(r)
                    break
        if update_rut!=[]:
            return update_rut
    except ValueError:
        print("There is no a valid rut")


def find_role(fragm, roles):
    try:
        pos_rol = 0
        for r in roles:
            if r in fragm:
                pos_rol = fragm.index(r)
        return pos_rol
    except ValueError:
        print("Problems for finding rol position in text fragment!")


def search_current_word(fragm):
    """Function searching word indicative of present date, for example: dic. 1999 a la fecha. 
    """
    current = ["actual", "ahora", "presente", "actualidad", "fecha", "hoy"]
    position = -1           
    try:
        for c in current:
            if c in fragm:
                position = fragm.index(c)
                break
        return position
    except ValueError:
        print("There is no input fragment to search current word!")



def correct_order_year(list_year):
    """Function correcting period order.
    """
    try:
        update_result = []
        if len(list_year)==2:
            segment_year_one = list_year[0].split("/")
            segment_year_two = list_year[1].split("/")
            if segment_year_one[1]==segment_year_two[1] and int(segment_year_two[0])<int(segment_year_one[0]):
                update_result.append(list_year[1])
                update_result.append(list_year[0])
                return update_result
            else:
                return list_year
        else:
            return list_year
    except ValueError:
        print("Incorrect period")



def convert_original_date(list_year, fragm):
    """Function converting a date format: dic 1999 - ene 2006 to 12/1999 - 01/2006.
    """
    months = [("enero","01"),("febrero","02"),("marzo","03"),("abril","04"),("mayo","05"),("junio","06"),\
            ("julio","07"), ("agosto","08"),("septiembre","09"), ("octubre","10"),("noviembre","11"),("diciembre","12")]
    month_suffix = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
    month_suffix_num = ["01","02","03","04","05","06","07","08","09","10","11","12"]
    result = []

    #Default no information about month in date.
    isThereMonth = 0
       
    #list_year contains years and its positions in fragments    
    try:
        #There is information about month in both years: dic. 1999 - ene. 2001 or 12/1999 - 01/2001
        if len(list_year)==2:
            pos_year_one = list_year[0][1]
            pos_year_two = list_year[1][1]
            year1 = list_year[0][0]
            year2 = list_year[1][0]
            
            if ((fragm[pos_year_one-1].lower()[:3] in month_suffix and fragm[pos_year_two-1].lower()[:3] in month_suffix) \
                or ((fragm[pos_year_one-1][:2] in month_suffix_num) and fragm[pos_year_two[1][1]-1][:2] in month_suffix_num)):
                    for year in list_year:
                        for m in months:
                            if (m[0].startswith(fragm[year[1]-1].lower()) or m[1]==fragm[year[1]-1]) and (m[1]+"/"+year[0]) not in result:  
                                isThereMonth = 1
                                result.append((m[1]+"/"+year[0]))
                                break
            #There is no information about month in both years: 1999-2001
            elif ((fragm[pos_year_one-1].lower()[:3] not in month_suffix and fragm[pos_year_two-1].lower()[:3] not in month_suffix) \
                 or (fragm[pos_year_one-1][:2] not in month_suffix_num) and fragm[pos_year_two-1][:2] not in month_suffix_num):                         
                    result.append(("01/"+str(year1)+"-"+"01/"+str(year2)))
        #There is only a year.
        elif len(list_year)==1:
            pos_year = list_year[0][1]
            year = list_year[0][0]
            for m in months:
                #Year has month and superior limit as actualidad: dic. 1999 a la fecha.
                if (fragm[pos_year-1].lower()[:3] in month_suffix or fragm[pos_year-1][:2] in month_suffix_num  \
                    or m[0].startswith(fragm[pos_year-1].lower())) and  m[0].startswith(fragm[pos_year-1].lower()) and (m[1]+"/"+ year, "now") not in result:     
                        isThereMonth = 1
                        result.append((m[1]+"/"+year, "now"))
                        break
                #Year without information about month: 1999 a la fecha.
                elif fragm[pos_year-1].lower()[:3] not in month_suffix and search_current_word(fragm)!=-1 \
                    and ("01/"+ year, "now") not in result:
                        result.append(("01/"+ year, "now"))
                #Year without information about month and actualidad: 1999.
                elif fragm[pos_year-1].lower()[:3] not in month_suffix and search_current_word(fragm)==-1 \
                    and (year) not in result:
                        result.append((year))
                
        #Correct inverted order [10/2005, 08/2005]
        result = correct_order_year(result)
        
        return result, isThereMonth
    except ValueError:
            print("List of years or sentence is empty!")


def search_position(seq, word):
    """Function calculates index of years in text. For cases like: ene. 2008 - dic. 2008
    """
    start_at = -1
    positions = []
    while True:
        try:
            pos = seq.index(word,start_at+1)
        except ValueError:
            break
        else:
            positions.append(pos)
            start_at = pos
    return positions 
    
        

def delimit_resume(text, resume_data):        
    """Function reading and delimitating resume in plain text format after conversion.
    """
    positions = []
    info_cv = {}
    generic_categories = []
    
    try:
        #Searchable list
        lower_fragments = [f.lower().strip() for f in text.lower().split("\n") if f!=""]
        original_fragments = [f.strip() for f in text.split("\n") if f!=""]    
        for category in resume_data:
            for fragm in lower_fragments:
                segment_fragm = nltk.word_tokenize(fragm)
                segment_category = category[1].split()      #How many words the real category has.
                num_match = 0
                for sc in segment_category:
                    if sc in segment_fragm and segment_fragm.index(sc)<=7:      #Number 7 is arbitrary
                        num_match = num_match + 1
                        
                if num_match == len(segment_category):
                    index_fragm = lower_fragments.index(fragm)
                    if (category[0],index_fragm) not in positions and category[0] not in generic_categories:
                        positions.append((category[0],index_fragm))
                        generic_categories.append(category[0])
                    else:
                        pass
        sorted_by_pos = sorted(positions, key=lambda tup: tup[1])
        update_positions = define_info_ranks(sorted_by_pos, len(original_fragments))
        isLabInfo = 0
        for pos in update_positions:
            info_cv[pos[0]] = [f for f in original_fragments[pos[1]:pos[2]+1] if f!=""]       
            if pos[0]=="experiencia_profesional":
                isLabInfo = 1
        if isLabInfo==1:
            return info_cv, update_positions 
        else:
            print("There is no information about laboral experience")
            return
    except ValueError:
        print("There is no information about resume or resume categories")
    

def define_info_ranks(sort_positions, number_fragments):
    """Function establishing positions of relevant information
    """
    result = []
    try:
        for r in range(len(sort_positions)):
            if r<len(sort_positions)-1:
                result.append((sort_positions[r][0],sort_positions[r][1]+1,sort_positions[r+1][1]-1))
            else:
                result.append((sort_positions[r][0], sort_positions[r][1]+1, number_fragments))
        result = sort_tuple_list(result)
        return result
    except ValueError:
        print("There is a problem with positions of resume categories!")


        
def sort_tuple_list(positions):
    """Function rearranging position index.
    """
    result = []
    try:
        for p in positions:
            if len(p) == 3 and p[1] < p[2]:
                result.append(p)
            elif len(p) == 3 and p[1] == p[2]:
                result.append((p[0], p[1], p[2]+1))
            else:
                result.append((p[0], p[2], p[1]))
        return(result)
    except ValueError:
        print("There is a problem with positions!")


def get_dates_year(list_fragm_years):
    """Function generating tuple with relevant information
    """
    result = []
    try:
        for tup in list_fragm_years:
            #Only century XX and XXI
            years = re.findall("19\d{2}|20\d{2}", "\n".join(tup[1]))
            pos_year = []

            #two years equal can exist (ene 2014 - dic 2014)
            for year in years:
                list_pos = search_position(tup[1], year)
                if len(list_pos)==2:
                    for e in list_pos:
                        if (year,e) not in pos_year:
                            pos_year.append((year,e))
                        else:
                            pass
                elif len(list_pos)==1:
                    pos_year.append((year,list_pos[0]))
            #Removing duplicates
            pos_year = list(set(pos_year))
            
            #Sorting tuples (year, index_fragm)
            pos_year = sorted(pos_year, key=lambda tup: tup[0])
            
            update_pos_year = []
            if len(pos_year)==2 and pos_year[0][0]==pos_year[1][0] and pos_year[0][1]>pos_year[1][1]:
                update_pos_year.append(pos_year[1])
                update_pos_year.append(pos_year[0])
                pos_year = update_pos_year
            #Cases where there is a potential error: ene 2016 - feb 2015.
            elif len(pos_year)==2  and pos_year[1][1]<pos_year[0][1]:
                update_pos_year.append((pos_year[0][0], pos_year[1][1]))
                update_pos_year.append((pos_year[1][0], pos_year[0][1]))
                pos_year = update_pos_year
            else:
                pass            

            #Converting to date format
            period, isThereMonth = convert_original_date(pos_year, tup[1])
            result.append((period, tup[0], tup[1], pos_year, isThereMonth))             
        
        return result
    except ValueError:
        print("Problems with list of fragments with at least a year!")



def get_dates_year_rol(list_fragm_years):
    """Function generating tuple with relevant information for fragments with rol and year.
       In this version, this function is not used. Probably collapses with other function.
    """
    result = []
    try:
        for tup in list_fragm_years:
        
            #Only century XX and XXI
            years = set(re.findall("19\d{2}|20\d{2}", "\n".join(tup[1])))
    
            pos_year = []
        
            #two years equal can exist (ene 2014 - dic 2014)
            for year in years:
                list_pos = search_position(tup[1], year)
                if len(list_pos)==2:
                    for e in list_pos:
                        pos_year.append((year,e))
                elif len(list_pos)==1:
                    pos_year.append((year,list_pos[0]))

            #Removing duplicates
            pos_year = list(set(pos_year))
        
            #Sorting tuples (year, index_fragm)
            pos_year = sorted(pos_year, key=lambda tup: tup[0])
            update_pos_year = []
            if len(pos_year)==2 and pos_year[0][0]==pos_year[1][0] and pos_year[0][1]>pos_year[1][1]:
                update_pos_year.append(pos_year[1])
                update_pos_year.append(pos_year[0])
                pos_year = update_pos_year
            else:
                pass            
            #Converting to date format
            period, isThereMonth = convert_original_date(pos_year, tup[1])

            #A value has been added to fragments with year and rol. For example: Asistente       ene 1999 - dic 2003.
            result.append((period, tup[0], tup[1], tup[3], pos_year, isThereMonth))               
        return result
    except ValueError:
        print("Problems with list of fragments with at least a year!")



def extract_laboral_experience(category):       #category (type list) is professional experience o education
    """Function extracting laboral experience.
    """
    laboral_experience = {}
    result = {}
    fragm_all = []
    fragm_year = []
    fragm_rol = []
    list_fragm_rol = []
    try:
        fragm_cat = [(category.index(f), f) for f in category] 
        years = set(re.findall("19\d{2}|20\d{2}", "\n".join(category)))
        roles = re.findall("(\w+ente|\w+ista|\w+dora|\w+dor|\w+ico|\w+tor|\w+iero|\w+sor|\w+ivo|\w+ero|\w+anza|\+og[o|a])", "\n".join(category).lower())
        roles = set([r for r in roles if r[-5:]!="mente"])            #Removing adverbs finished in "mente"
        generic_roles = {"lider","jefe","encargado","responsable","encargada","manager","maestro"}
        roles = roles | generic_roles
        
        for y in years:
            for r in roles:
                for f in fragm_cat:
                    fragm = re.sub("/"," / ",f[1])
                    fragm = re.sub("-"," - ",fragm)
                    fragm = re.sub(r"\."," . ",fragm)     #Some cases, example, Nov. correctly don't tokenize 
                    segment_fragm = nltk.word_tokenize(fragm.lower())
                    
                    #Fragment has year and potential role
                    if y in segment_fragm and r in segment_fragm and (f[0], segment_fragm, segment_fragm.index(y), \
                        segment_fragm.index(r)) not in fragm_all:
                            fragm_all.append((f[0],segment_fragm, segment_fragm.index(y), segment_fragm.index(r)))
                    #Fragment has year and no role. So, if it has more information, it can be Company.
                    elif y in segment_fragm and r not in segment_fragm and (f[0], segment_fragm, segment_fragm.index(y)) \
                        not in fragm_year:
                            fragm_year.append((f[0],segment_fragm, segment_fragm.index(y)))
                    #Fragment has role and not year, So it it has more information, it can be Company.
                    elif y not in segment_fragm and r in segment_fragm and (f[0], segment_fragm, segment_fragm.index(r)) \
                        not in list_fragm_rol:
                            fragm_rol.append((f[0], segment_fragm, segment_fragm.index(r)))
                    else:
                        pass

        #Until here, we have a tuple with (period, pos_fragm, fragm, index(rol), pos_year, isThereMonth)
        fragms_all =  get_dates_year_rol(fragm_all)
        fragms_year = get_dates_year(fragm_year)
        
        if type(extract_remain_year_rol(fragms_all, fragm_cat))!=None and type(extract_remain_year(fragms_year, fragm_cat, roles))!=None:
            if len(extract_remain_year_rol(fragms_all, fragm_cat)) > len(extract_remain_year(fragms_year, fragm_cat, roles)):
                result = extract_remain_year_rol(fragms_all, fragm_cat)
            else:
                result = extract_remain_year(fragms_year, fragm_cat, roles)
        else:
            pass
        result = sorted(result, key=lambda tup: tup[1])
        
        #Dictionary for saving output data without labels
        lab_exp_tmp = {} 
        
        for tup in result:
            if len(tup[0])==2:
                laboral_experience[tup[1]] = [("fecha inicio",  tup[0][0]), ("fecha fin",  tup[0][1]), ("empresa", tup[2]), ("puesto", tup[3]), ("distancia", tup[4])]
                lab_exp_tmp[tup[1]] = [tup[0][0], tup[0][1], tup[2],tup[3], round(tup[4], 3)]
            elif len(tup[0])==1 and tup[0][0][1]=="now":
                laboral_experience[tup[1]] = [("fecha inicio",  tup[0][0][0]), ("fecha fin",  tup[0][0][1]), ("empresa", tup[2]), ("puesto", tup[3]), ("distancia", tup[4])]
                lab_exp_tmp[tup[1]] = [tup[0][0][0], tup[0][0][1], tup[2],tup[3], round(tup[4], 3)]
            elif len(tup[0])==1 and len(tup[0][0].split("-"))==2 and len(tup[0])==4:
                segment_period = tup[0][0].split("-")
                laboral_experience[tup[1]] = [("fecha inicio",  segment_period[0]), ("fecha fin",  segment_period[1]), ("empresa", tup[2]), ("puesto", tup[3])]
                lab_exp_tmp[tup[1]] = [segment_period[0], segment_period[1], tup[2],tup[3]]
        
        return laboral_experience, lab_exp_tmp
    except IndexError:
        print("There is no enough data for extracting laboral experience!")
              

def extract_remain_year_rol(fragms_year_role, fragm_cat):
    """Function extracting relevant information from fragment where year is found and adjacent fragment with role.
       (period, position_fragm, fragment, position_rol, position_year, isThereMonth)
       In this prototype version, this function is not used, revision is required.
    """
    result = []
    num_fragm = []
    try:
        for p in fragms_year_role:
            fragm = p[2]
            orig_fragm = p[2]
            pos_year = p[4]
            pos_rol = p[3]
            if len(pos_year)==2 and p[5] == 1 and pos_year[1][1]>len(fragm)/2 and p[1] not in num_fragm and p[1] not in num_fragm and p[1]>0:
                fragm = fragm[0:pos_year[0][1]-1]
                result.append((p[0],p[1], fragm_cat[p[1]-1]," ".join(fragm)))
                num_fragm.append(p[1])
            elif len(pos_year)==2 and p[5] == 1 and pos_year[1][1]<=len(fragm)/2  and fragm[pos_rol-1]=="." and p[1] not in num_fragm:
                fragm = fragm[pos_year[1][1]+1:pos_rol-1]
                result.append((p[0],p[1]," ".join(fragm), orig_fragm[pos_rol]))
                num_fragm.append(p[1])
            elif len(pos_year)==2 and p[5] == 1 and pos_year[1][1]<=len(fragm)/2  and p[1] not in num_fragm:
                fragm = nltk.word_tokenize(fragm_cat[p[1]][1]) 
                pos_div = search_position(fragm,"-")
                if len(pos_div)==2:
                    rol = " ".join(fragm[pos_year[1][1]+2:pos_div[1]])
                    company = " ".join(fragm[pos_div[1]+1:])
                    result.append((p[0],p[1],company, rol))
                elif len(pos_div)==1:
                    rol = " ".join(fragm[pos_year[1][1]+1:pos_div[0]])
                    company = " ".join(fragm[pos_div[0]+1:])
                    result.append((p[0],p[1],company, rol))
                else:
                    pass
                num_fragm.append(p[1])
            elif len(pos_year)==2 and p[5] == 0 and pos_year[1][1]>len(fragm)/2 and p[1] not in num_fragm:
                fragm = fragm[0:pos_year[0][1]]
                result.append((p[0],p[1]," ".join(fragm)))
                num_fragm.append(p[1])
            elif len(pos_year)==2 and p[5] == 0 and pos_year[1][1]<=len(fragm)/2 and fragm[pos_rol-1]=="." and p[1] not in num_fragm:
                fragm = fragm[pos_year[1][1]+1:pos_rol-1]
                result.append((p[0],p[1]," ".join(fragm), orig_fragm[pos_rol]))
                num_fragm.append(p[1])
            elif len(pos_year)==1 and p[5] == 1 and pos_year[0][1]>len(fragm)/2 and p[1] not in num_fragm:
                fragm = fragm[0:pos_year[0][1]-1] 
                result.append((p[0],p[1]," ".join(fragm)))
                num_fragm.append(p[1])
            elif len(pos_year)==1 and p[5] == 0 and pos_year[0][1]>len(fragm)/2 and p[1] not in num_fragm:
                fragm = fragm[0:pos_year[0][1]] 
                result.append((p[0],p[1]," ".join(fragm)))
                num_fragm.append(p[1])
            elif len(pos_year)==1 and p[5] == 0 and pos_year[0][1]<=len(fragm)/2 and fragm[pos_rol-1]=="." and p[1] not in num_fragm:
                fragm = fragm[pos_year[0][1]+1:pos_rol-1] 
                result.append((p[0],p[1]," ".join(fragm), orig_fragm[pos_rol]))
                num_fragm.append(p[1])
        return(result)
    except ValueError:
        print("Problems with data about fragments with year and role!")


def extract_remain_year(period_year, fragm_cat, roles):
    """Function extracting relevant information from fragment where year is found and adjacent fragment with role.
       (period, position_fragm, fragment, position_year, isThereMonth)
    """
    result = []
    num_fragm = []
    try:
        for p in period_year:
            fragm = p[2]
            pos_year = p[3]
            
            #Period is a line, after rol and company are found. In this case, period has format: Nov 2012 - Feb 2015 (any format for month from 3 chars)
            if len(pos_year)==2 and p[4] == 1 and len(fragm)-2<=pos_year[1][1]<=len(fragm)-1 and p[1] not in num_fragm  and len(fragm)-5<=1:
                fragm_next = nltk.word_tokenize(fragm_cat[p[1]+1][1])
                if "-" in fragm_next:
                    pos_div = fragm_next.index("-")
                    rol = " ".join(fragm_next[0:pos_div])
                    company = " ".join(fragm_next[pos_div+1:])
                    distance = ((len(fragm) - pos_year[1][1]) +  find_role(fragm_next, roles))/(len(fragm_next)+len(fragm))
                    result.append((p[0],p[1],company, rol, distance))
                    num_fragm.append(p[1])
                else:
                    result.append(("",0,"", "", -1))
            #Period and candidate company.
            elif len(pos_year)==2 and p[4] == 1 and len(fragm)-2<=pos_year[1][1]<=len(fragm)-1 and p[1] not in num_fragm and len(fragm)-5>=2:
                fragm_next = nltk.word_tokenize(fragm_cat[p[1]+1][1])
                rol = fragm_next[0]
                company = " ".join(fragm[:pos_year[0][1]-1])
                distance = (((len(fragm) - pos_year[1][1])) + fragm_next.index(rol)) /(len(fragm_next)+len(fragm))
                result.append((p[0],p[1],company, rol, distance))
                num_fragm.append(p[1])
            elif len(pos_year)==2 and p[4] == 1 and pos_year[1][1]>=len(fragm)/2 and p[1] not in num_fragm:
                fragm_next = nltk.word_tokenize(fragm_cat[p[1]+1][1]) 
                if "-" in fragm_next:
                    pos_div = fragm.index("-")
                    rol = fragm[0:pos_div]
                    company = fragm[pos_div+1:]
                    distance = ((len(fragm) - pos_year[1][1]) +  find_role(fragm_next, roles))/(len(fragm_next)+len(fragm))
                    result.append((p[0],p[1], company, rol, distance))
                    num_fragm.append(p[1])
                else:
                    result.append(("",0,"", "", -1))
            elif len(pos_year)==2 and p[4] == 0 and pos_year[1][1]>len(fragm)/2 and p[1] not in num_fragm:
                fragm = fragm[0:pos_year[0][1]]
                post_sent = nltk.word_tokenize(fragm_cat[p[1]+1][1])
                result.append((p[0],p[1]," ".join(fragm), post_sent[0]))
                num_fragm.append(p[1])
            elif len(pos_year)==2 and p[4] == 0 and pos_year[1][1]<=len(fragm)/2 and p[1] not in num_fragm:
                fragm = fragm[pos_year[1][1]+1:]
                result.append((p[0],p[1]," ".join(fragm)))
                num_fragm.append(p[1])
            elif len(pos_year)==1 and p[4] == 1 and pos_year[0][1]>len(fragm)/2 and p[1] not in num_fragm:
                fragm_next = nltk.word_tokenize(fragm_cat[p[1]+1][1])
                if "-" in fragm_next and fragm_next.index("-")>0:
                    pos_div = fragm_next.index("-")
                    rol = fragm[0:pos_div]
                    company = fragm[pos_div+1:]
                    distance = ((len(fragm) - pos_year[0][1]) +  find_role(fragm_next, roles))/(len(fragm_next)+len(fragm))
                    result.append((p[0],p[1], company, rol, distance))
                    num_fragm.append(p[1])
                else:
                    result.append(("",0,"", "", -1))                    
            elif len(pos_year)==1 and p[4] == 0 and pos_year[0][1]>len(fragm)/2 and p[1] not in num_fragm:
                fragm_next = nltk.word_tokenize(fragm_cat[p[1]+1][1])
                if "-" in fragm_next and fragm_next.index("-")>0:
                    pos_div = fragm_next.index("-")
                    rol = fragm[0:pos_div]
                    company = fragm[pos_div+1:]
                    result.append((p[0],p[1], company, rol))
                    num_fragm.append(p[1])
                else:
                    result.append(("",0,"", "", -1))
            elif len(pos_year)==1 and p[4] == 1 and pos_year[0][1]==1 and p[1] not in num_fragm and search_current_word(fragm)!=-1:
                fragm_next = nltk.word_tokenize(fragm_cat[p[1]+1][1])
                if "-" in fragm_next and fragm_next.index("-")>0:
                    pos_div = fragm_next.index("-")
                    rol = " ".join(fragm_next[0:pos_div])
                    company = " ".join(fragm_next[pos_div+1:])
                    distance = (len(fragm) - search_current_word(fragm) +  find_role(fragm_next, roles))/(len(fragm_next)+len(fragm))                   
                    result.append((p[0],p[1],company, rol, distance))
                    num_fragm.append(p[1])
                else:
                    result.append(("",0,"", "", -1))
        return result
    except ValueError:
        print("Problems with data about fragments with only year!")



def extract_general_data(original_fragments, update_positions):
    """Function for extracting general information.
    """  
    st = StanfordNERTagger(r'/Users/olgaacosta/Documents/experimentos/NERStanford/classifiers/english.all.3class.distsim.crf.ser.gz', \
    r'/Users/olgaacosta/Documents/experimentos/NERStanford/stanford-ner.jar')
    general_information = []
    result = {}
    rut=[]
    email = []
    phone = []
    isThereNer = 0
    name = ""
    try:
        for p in update_positions:
           if p[0]=="informacion_personal":
                general_information = original_fragments[p[1]:p[2]+1]
                break
           else:
               continue

        for f in original_fragments:
            if f!='':
                ner = st.tag(nltk.word_tokenize(f))
                if isThereNer == 0:
                    for t in ner:
                        if t[1]=="PERSON" and ner.index(t)<=len(ner)-1:
                            isThereNer = 1
                            name = name + " " + t[0]
                            person_index = original_fragments.index(f)
                        else:
                            pass
                else:
                    break

        if isThereNer==1 and len(name.split())>1:
            relevant_information = general_information + original_fragments[person_index:update_positions[0][1]-1]
        else:
            relevant_information =  original_fragments[0:update_positions[0][1]-1]

        phone = re.findall(r"\b\+?[569]{0,3}\s*[29]{0,1}\s*[2-9]\d{6,7}\s","\n".join(relevant_information))
        email =re.findall("[\w\d._]+@[\w\d.]+", "\n".join(relevant_information))
        rut = re.findall(r"\d{2}\.?\d{3}\.?\d{3}\s?-\s?[\w|\d]\s|\d{8}-?[Kk\d]",  "\n".join(relevant_information))
        
        #Name from NER or fragment 0 (case of a most standard format)
        if name!="" and len(name.split())>1:
            result["nombre"] =  name.strip()
        else:
            result["nombre"] =  original_fragments[0]
        if phone!=[]:
            result["telefono"] =  ",".join([t.strip() for t in phone])
        else:
            result["telefono"] =  "No disponible"
        if rut!=[] and validate_rut(rut)!=None:
            result["rut"] = " ".join(validate_rut(rut))
        else:
            result["rut"] = "No disponible"
        if email!=[]:
            result["email"] =  ",".join(email)
        else:
            result["email"] = "No disponible"

        return result
    except ValueError:
        print("There is no enough information for this process")
            
        
            


def read_document(filein, dataresume):
    """Function reading input file and data resume.
    """
    text = ""
    resume_data = []
    try:
        resume_data = []
        with open(dataresume, encoding="utf-8") as doc:
            categories = doc.read().split("\n")
            for rc in range(len(categories)):
                segment_category = categories[rc].split(";")
                if len(segment_category)==2:
                    for syn in segment_category[1].split(","):
                        resume_data.append((segment_category[0], syn))

        #Reading resume in PDF or docx format.
        if filein.endswith("pdf"):
            filename = filein[:filein.index(".")] + ".txt"
            subprocess.call(["pdftotext", filein, filename])
            with open (filename, encoding="latin1") as pdf:
                text = pdf.read()
        elif filein.endswith("docx"):
            subprocess.call(["textutil", "-convert", "txt", filein])
            file_txt = filein[:filein.index(".")]+".txt"
            with open (file_txt, encoding="utf-8") as docx:
                text = docx.read()
        elif filein.endswith("txt"):
            with open (filein, encoding="utf-8") as docx:
                text = docx.read()
        
        if text == "" or resume_data == []:
            print("Invalid file format or data resume missing!")
            sys.exit(1)
        return text, resume_data
    except ValueError:
        pass


def process_resume(filein=arg1, dataresume=arg2):
    """Function calling main functions
    """
    try:
        document, resume_data = read_document(filein, dataresume)
        if document != "" and resume_data != []:
            info_cv, positions = delimit_resume(document, resume_data)
            
            #filename = open(r'/Users/olgaacosta/Documents/experimentos/analisis_cvs/resultados_first_100.txt',"a", encoding="utf-8")
            if info_cv["experiencia_profesional"] != []:
                laboral_experience, lab_exp_tmp = extract_laboral_experience(info_cv["experiencia_profesional"])
                #Personal data.
                original_fragments = [f.strip() for f in document.split("\n") if f!='']
                general_data = extract_general_data(original_fragments, positions)
                #print(json.loads(general_data))
                data = {}
                data["CV"] = [general_data, laboral_experience]
                data_string = json.dumps(data, indent=4)
                #json.dump(data_string, filename)
                #filename.close()
                #for fragm, exp_lab in lab_exp_tmp.items():
                #    filename.write(general_data["rut"]+","+general_data["nombre"]+","+exp_lab[0]+","+exp_lab[1]+","+exp_lab[2]+","+exp_lab[3]+","+str(exp_lab[4])+"\n")
                #filename.close()
                if data_string != []:
                    #print ('JSON:', data_string)
                    return data_string
                else:
                    return ""
            else:
                print("there is no data about laboral experience!")
                sys.exit(1)
    except ValueError:
        pass


#Main Function
if __name__ == "__main__":
    sys.stdout.write(process_resume())
    
 






                

