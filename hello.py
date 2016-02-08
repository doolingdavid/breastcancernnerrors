from flask import Flask, render_template, session, redirect, url_for
from flask import request
from flask import make_response
from flask import redirect
from flask import abort
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.moment import Moment
from datetime import datetime
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from wtforms import BooleanField, SelectField, RadioField
from wtforms import FloatField
import pickle
import os
import numpy as np
from sklearn.externals import joblib
import pandas as pd
from pandas import Series, DataFrame
import urllib2, json
from flask import make_response
from functools import wraps, update_wrapper
from datetime import datetime
import time
import datetime
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.autoreload
from flask import jsonify








yoblistlabel = [str(a) for a in range(1880,2020)]
yoblistchoices = zip(yoblistlabel, yoblistlabel)


yodlistlabel = [str(a) for a in range(1970,2020)]
yodlistchoices = zip(yodlistlabel, yodlistlabel)


monthlistlabel = [str(a) for a in range(1,13)]
monthlistchoices = zip(monthlistlabel, monthlistlabel)




class NameForm(Form):
            
    
    
    cs_tumor_size = FloatField('What is the tumor size (mm)?', validators=[Required()])
    address = StringField("What is the patient's address?", validators=[Required()])
    
    grade = SelectField('Grade',default='0',
                    choices = [('mo','moderately differentiated'),
                               ('po','poorly differentiated'),
                               ('un','undifferentiated; anaplastic'),
                               ('we','well differentiated'),
                               ('not','None of the above')],
                        validators=[Required()])


    hist = SelectField('Histology', default='0',
                choices = [('adenomas','adenomas and adenocarcinomas'),
                           ('adnexal','adnexal and skin appendage neoplasms'),
                           ('basal','basal cell neoplasms'),
                           ('complex','complex epithelial neoplasms'),
                           ('cystic','cystic, mucinous and serous neoplasms'),
                           ('ductal','ductal and lobular neoplasms'),
                           ('epithelial','epithelial neoplasms, NOS'),
                           ('nerve','nerve sheath tumors'),
                           ('unspecified','unspecified neoplasms'),
                           ('not','None of the above')],
                       validators=[Required()])


    laterality = SelectField('Laterality', default='0',
        choices = [('paired','Paired site, but no information concerning laterality; midline tumor'),
                   ('bilateral','bilateral involvement, lateral origin unknown; stated to be single primary'),
                   ('right','right: origin of primary'),
                   ('not','None of the above')],
                    validators=[Required()])


    maritalstatus = SelectField('Marital Status at Dx', default='0',
      choices = [('divorced','Divorced'),
                 ('married','Married including common law'),
                 ('separated','Separated'),
                ('single','Single ,never married'),
                 ('unknown','Unknown'),
                 ('unmarried','Unmarried or domestic partner'),
                 ('widowed','Widowed')],
                  validators=[Required()])

            


    monthofdiagnosis = SelectField('Month of Diagnosis', default='0',
        choices = [('jan','Jan'),
                   ('feb','Feb'),
                   ('mar','Mar'),
                   ('apr','Apr'),
                   ('may','May'),
                   ('jun','Jun'),
                   ('jul','Jul'),
                   ('aug','Aug'),
                   ('sep','Sep'),
                   ('oct','Oct'),
                   ('nov','Nov'),
                   ('dec','Dec')],
            validators=[Required()])


    raceethnicity = SelectField('Race_ethnicity', default='0',
        choices = [('americanindian','American Indian, Aleutian, Alaskan Native or Eskimo'),
                   ('asianindian','Asian Indian'),
                   ('black','Black'),
                   ('chinese','Chinese'),
                   ('japanese','Japanese'),
                   ('melanesian','Melanesian'),
                   ('other','Other'),
                   ('otherasian','Other Asian'),
                   ('pacific','Pacific Islander'),
                   ('thai','Thai'),
                   ('unknown','Unknown'),
                   ('vietnamese','Vietnamese'),
                   ('white','White')],
            validators=[Required()])


    


                   


    seerhistoric = SelectField('seer_historic_stage_a', default='0',
        choices = [('distant','Distant'),
                   ('in','In situ'),
                   ('localized','Localized'),
                   ('unstaged','Unstaged')],
            validators=[Required()])


    sex = SelectField('Gender', default='0',
        choices = [('male','Male'),
                   ('female','Female')],
            validators=[Required()])



    spanish = SelectField('spanish_hispanic_origin', default='0',
        choices = [('cuban','Cuban'),
                   ('mexican','Mexican'),
                   ('nonspanish','Non-Spanish/Non-hispanic'),
                   ('other','Other specified Spanish/Hispanic origin (excludes Dominican Republic)'),
                   ('surname','Spanish surname only'),
                   ('nos','Spanish, NOS; Hispanic, NOS; Latino NOS')],
            validators=[Required()])

    
    yob = SelectField('Year of Birth',
                      choices = yoblistchoices, 
                      validators=[Required()])


    yod = SelectField('Year of Diagnosis',
                      choices = yodlistchoices,
                      validators=[Required()])
    

    
    
    submit = SubmitField('Submit')




class LastNameForm(Form):
    lastname = StringField('What is your last name?', validators=[Required()])
    

    


app = Flask(__name__)

#manager = Manager(app)


app.config['SECRET_KEY'] = 'hard to guess string'




bootstrap = Bootstrap(app)
moment = Moment(app)


clf = joblib.load('BREASTPICKLENN/modelbreast.pkl')



# there is a difference in this function between the RF and NN models

def get_survival_function(document):
    """takes the input of the text area field and
    returns the survival function values at 6 months, 
    12 months and 60 months."""
    X = document
    print X
    A = []
    p_so_far = 1
    for i in range(108):
        thing = np.append(X, i)
        p_cur = clf.predict_proba(thing[None,...],verbose=0)[0][1]
        A.append(p_so_far * p_cur)
        p_so_far = p_so_far*(1 - p_cur)
    As = pd.Series(A)
    Asurv = 1 - As.cumsum()
    prob6 = Asurv.loc[6]
    prob12 = Asurv.loc[12]
    prob60 = Asurv.loc[60]
    return prob6, prob12, prob60, Asurv


def get_one_group(acdf,numberofsubjects):
    """Returns a pandas series"""
    import random
    a = list()
    for i in range(numberofsubjects):
        try:
            b = get_month_from_cdf(acdf)
            a.append(b)
        except:
            pass
    c = pd.Series(a)
    return c






def get_lat_lng_elevation(address):
    """takes an address like the values in 
    df_fips_codes_website['address'], queries two different 
    google maps apis and returns the corresonding lat, lng, and
    elevation of the address. In the case of county level addresses,
    the returned point corresponds to the middle of the county"""
    import re, json, urllib
    
    
    # first get the lat long and make sure the address is of the correct form
    
    prelatlng = "https://maps.googleapis.com/maps/api/geocode/json?address="
    newaddress = re.sub(r"\s+", '+', address) 
    newaddress = re.sub(r"\xf1a", "n", newaddress)
    print newaddress
    postlatlng = "&key=AIzaSyDEVzo20hSeLcu1bSDUohZrjBTrWkdke18"
    
    latlngurl = prelatlng + newaddress + postlatlng
    
    responselatlng = urllib2.urlopen(latlngurl)
    htmllatlng = responselatlng.read()
    thinglatlng = json.loads(htmllatlng)
    lat = thinglatlng["results"][0]["geometry"]["location"]["lat"]
    lng = thinglatlng["results"][0]["geometry"]["location"]["lng"]
    
    
    # now get the corresponding elevation
    
    preelevation = "https://maps.googleapis.com/maps/api/elevation/json?locations="
    middleurl = str(lat) + ',' + str(lng)
    postelevation = "&key=AIzaSyDEVzo20hSeLcu1bSDUohZrjBTrWkdke18"
    
    elevationurl = preelevation + middleurl + postelevation
    
    responseelevation = urllib2.urlopen(elevationurl)
    htmlelevation = responseelevation.read()
    thingelevation = json.loads(htmlelevation)
    
    elevation_meters = thingelevation["results"][0]["elevation"]
    
    # the returned elevation is in meters. lets use feet .
    # the metric system is for assholes
    
    elevation_feet = elevation_meters * 3.28084
    
    print address, lat, lng, elevation_feet
    return address, lat, lng, elevation_feet
    


def run_server():
    port = int(os.environ.get("PORT", 5000))
    http_server = tornado.httpserver.HTTPServer(
        tornado.wsgi.WSGIContainer(app)
    )
    # http_server.listen(5000)
    http_server.listen(port)
    # Reads args given at command line (this also enables logging to stderr)
    tornado.options.parse_command_line()

    # Start the I/O loop with autoreload
    io_loop = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.start(io_loop)
    try:
        io_loop.start()
    except KeyboardInterrupt:
        pass



@app.route('/')
def index():
    form = NameForm(request.form)
    return render_template('reviewform.html', form=form)







@app.route('/results', methods=['POST'])
def results():
    form = NameForm(request.form)
    session['labels'] = [str(a) for a in range(120)]
    if request.method == 'POST' and form.validate_on_submit():
                
        session['yob'] = form.yob.data
        session['yod'] = form.yod.data
                   
            
        yobgood = int(session['yob'])
        print yobgood, type(yobgood)
        print session['yob'], type(session['yob'])
        
        session['cs_tumor_size'] = form.cs_tumor_size.data
        
        print session['cs_tumor_size']
        session['address'] = form.address.data
        print session['address'], type(session['address'])
        newaddress, lat, lng, elevation_feet = get_lat_lng_elevation(str(session['address']))
        print newaddress, lat, lng, elevation_feet
        session['lat'] = lat
        session['lng'] = lng
        session['elevation'] = elevation_feet
                            
                        

        session['grade'] = form.grade.data

        if form.grade.data == 'mo':
            session['grade_mo'] = '1'
        else:
            session['grade_mo'] = '0'

        if form.grade.data == 'po':
            session['grade_po'] = '1'
        else:
            session['grade_po'] = '0'


        if form.grade.data == 'un':
            session['grade_un'] = '1'
        else:
            session['grade_un'] = '0'

        if form.grade.data == 'we':
            session['grade_we'] = '1'
        else:
            session['grade_we'] = '0'

        
        if form.hist.data == 'adenomas':
            session['hist_adenomas'] = '1'
        else:
            session['hist_adenomas'] = '0'

        if form.hist.data == 'adnexal':
            session['hist_adnexal'] = '1'
        else:
            session['hist_adnexal'] = '0'


        if form.hist.data == 'basal':
            session['hist_basal'] = '1'
        else:
            session['hist_basal'] = '0'
            
            
        if form.hist.data == 'complex':
            session['hist_complex'] = '1'
        else:
            session['hist_complex'] = '0'


        if form.hist.data == 'cystic':
            session['hist_cystic'] = '1'
        else:
            session['hist_cystic'] = '0'

        if form.hist.data == 'ductal':
            session['hist_ductal'] = '1'
        else:
            session['hist_ductal'] = '0'


        if form.hist.data == 'epithelial':
            session['hist_epithelial'] = '1'
        else:
            session['hist_epithelial'] = '0'


        if form.hist.data == 'nerve':
            session['hist_nerve'] = '1'
        else:
            session['hist_nerve'] = '0'


        if form.hist.data == 'unspecified':
            session['hist_unspecified'] = '1'
        else:
            session['hist_unspecified'] = '0'



        if form.laterality.data == 'bilateral':
            session['laterality_bilateral'] = '1'
        else:
            session['laterality_bilateral'] = '0'

        if form.laterality.data == 'paired':
            session['laterality_paired'] = '1'
        else:
            session['laterality_paired'] = '0'

        if form.laterality.data == 'right':
            session['laterality_right'] = '1'
        else:
            session['laterality_right'] = '0'
            

        if form.maritalstatus.data == 'divorced':
            session['maritalstatus_divorced'] = '1'
        else:
            session['maritalstatus_divorced'] = '0'


        if form.maritalstatus.data == 'married':
            session['maritalstatus_married'] = '1'
        else:
            session['maritalstatus_married'] = '0'


        if form.maritalstatus.data == 'separated':
            session['maritalstatus_separated'] = '1'
        else:
            session['maritalstatus_separated'] = '0'
            


        if form.maritalstatus.data == 'single':
            session['maritalstatus_single'] = '1'
        else:
            session['maritalstatus_single'] = '0'


        if form.maritalstatus.data == 'unknown':
            session['maritalstatus_unknown'] = '1'
        else:
            session['maritalstatus_unknown'] = '0'


        if form.maritalstatus.data == 'unmarried':
            session['maritalstatus_unmarried'] = '1'
        else:
            session['maritalstatus_unmarried'] = '0'


        if form.maritalstatus.data == 'widowed':
            session['maritalstatus_widowed'] = '1'
        else:
            session['maritalstatus_widowed'] = '0'



        if form.monthofdiagnosis.data == 'jan':
            session['monthofdiagnosis_jan'] = '1'
        else:
            session['monthofdiagnosis_jan'] = '0'


        if form.monthofdiagnosis.data == 'feb':
            session['monthofdiagnosis_feb'] = '1'
        else:
            session['monthofdiagnosis_feb'] = '0'


        if form.monthofdiagnosis.data == 'feb':
            session['monthofdiagnosis_feb'] = '1'
        else:
            session['monthofdiagnosis_feb'] = '0'


        if form.monthofdiagnosis.data == 'mar':
            session['monthofdiagnosis_mar'] = '1'
        else:
            session['monthofdiagnosis_mar'] = '0'


        if form.monthofdiagnosis.data == 'apr':
            session['monthofdiagnosis_apr'] = '1'
        else:
            session['monthofdiagnosis_apr'] = '0'


        if form.monthofdiagnosis.data == 'may':
            session['monthofdiagnosis_may'] = '1'
        else:
            session['monthofdiagnosis_may'] = '0'


        if form.monthofdiagnosis.data == 'jun':
            session['monthofdiagnosis_jun'] = '1'
        else:
            session['monthofdiagnosis_jun'] = '0'


        if form.monthofdiagnosis.data == 'jul':
            session['monthofdiagnosis_jul'] = '1'
        else:
            session['monthofdiagnosis_jul'] = '0'


        if form.monthofdiagnosis.data == 'aug':
            session['monthofdiagnosis_aug'] = '1'
        else:
            session['monthofdiagnosis_aug'] = '0'


        if form.monthofdiagnosis.data == 'sep':
            session['monthofdiagnosis_sep'] = '1'
        else:
            session['monthofdiagnosis_sep'] = '0'

        if form.monthofdiagnosis.data == 'oct':
            session['monthofdiagnosis_oct'] = '1'
        else:
            session['monthofdiagnosis_oct'] = '0'


        if form.monthofdiagnosis.data == 'nov':
            session['monthofdiagnosis_nov'] = '1'
        else:
            session['monthofdiagnosis_nov'] = '0'


        if form.monthofdiagnosis.data == 'dec':
            session['monthofdiagnosis_dec'] = '1'
        else:
            session['monthofdiagnosis_dec'] = '0'



        if form.raceethnicity.data == 'americanindian':
            session['raceethnicity_americanindian'] = '1'
        else:
            session['raceethnicity_americanindian'] = '0'


        if form.raceethnicity.data == 'asianindian':
            session['raceethnicity_asianindian'] = '1'
        else:
            session['raceethnicity_asianindian'] = '0'

        if form.raceethnicity.data == 'black':
            session['raceethnicity_black'] = '1'
        else:
            session['raceethnicity_black'] = '0'


        if form.raceethnicity.data == 'chinese':
            session['raceethnicity_chinese'] = '1'
        else:
            session['raceethnicity_chinese'] = '0'


        if form.raceethnicity.data == 'japanese':
            session['raceethnicity_japanese'] = '1'
        else:
            session['raceethnicity_japanese'] = '0'


        if form.raceethnicity.data == 'melanesian':
            session['raceethnicity_melanesian'] = '1'
        else:
            session['raceethnicity_melanesian'] = '0'


        if form.raceethnicity.data == 'other':
            session['raceethnicity_other'] = '1'
        else:
            session['raceethnicity_other'] = '0'


        if form.raceethnicity.data == 'otherasian':
            session['raceethnicity_otherasian'] = '1'
        else:
            session['raceethnicity_otherasian'] = '0'


        if form.raceethnicity.data == 'pacific':
            session['raceethnicity_pacific'] = '1'
        else:
            session['raceethnicity_pacific'] = '0'


        if form.raceethnicity.data == 'thai':
            session['raceethnicity_thai'] = '1'
        else:
            session['raceethnicity_thai'] = '0'


        if form.raceethnicity.data == 'unknown':
            session['raceethnicity_unknown'] = '1'
        else:
            session['raceethnicity_unknown'] = '0'


        if form.raceethnicity.data == 'vietnamese':
            session['raceethnicity_vietnamese'] = '1'
        else:
            session['raceethnicity_vietnamese'] = '0'



        if form.raceethnicity.data == 'white':
            session['raceethnicity_white'] = '1'
        else:
            session['raceethnicity_white'] = '0'
        

        



        

        
        


        



        if form.seerhistoric.data == 'distant':
            session['seerhistoric_distant'] = '1'
        else:
            session['seerhistoric_distant'] = '0'


        if form.seerhistoric.data == 'in':
            session['seerhistoric_in'] = '1'
        else:
            session['seerhistoric_in'] = '0'


        if form.seerhistoric.data == 'localized':
            session['seerhistoric_localized'] = '1'
        else:
            session['seerhistoric_localized'] = '0'


        if form.seerhistoric.data == 'unstaged':
            session['seerhistoric_unstaged'] = '1'
        else:
            session['seerhistoric_unstaged'] = '0'



        if form.sex.data == 'female':
            session['sex_female'] = '1'
        else:
            session['sex_female'] = '0'


        if form.spanish.data == 'cuban':
            session['spanish_cuban'] = '1'
        else:
            session['spanish_cuban'] = '0'


        if form.spanish.data == 'mexican':
            session['spanish_mexican'] = '1'
        else:
            session['spanish_mexican'] = '0'


        if form.spanish.data == 'nonspanish':
            session['spanish_nonspanish'] = '1'
        else:
            session['spanish_nonspanish'] = '0'


        if form.spanish.data == 'other':
            session['spanish_other'] = '1'
        else:
            session['spanish_other'] = '0'



        if form.spanish.data == 'surname':
            session['spanish_surname'] = '1'
        else:
            session['spanish_surname'] = '0'

        if form.spanish.data == 'nos':
            session['spanish_nos'] = '1'
        else:
            session['spanish_nos'] = '0'
        

                 
        session_data = np.array( [session['cs_tumor_size'],
                                  session['elevation'],
                                  session['grade_mo'],
                                  session['grade_po'],
                                  session['grade_un'],
                                  session['grade_we'],
                                  session['hist_adenomas'],
                                  session['hist_adnexal'],
                                  session['hist_basal'],
                                  session['hist_complex'],
                                  session['hist_cystic'],
                                  session['hist_ductal'],
                                  session['hist_epithelial'],
                                  session['hist_nerve'],
                                  session['hist_unspecified'],
                                  session['lat'],
                                  session['laterality_bilateral'],
                                  session['laterality_paired'],
                                  session['laterality_right'],
                                  session['lng'],
                                  session['maritalstatus_divorced'],
                                  session['maritalstatus_married'],
                                  session['maritalstatus_separated'],
                                  session['maritalstatus_single'],
                                  session['maritalstatus_unknown'],
                                  session['maritalstatus_unmarried'],
                                  session['maritalstatus_widowed'],
                                  session['monthofdiagnosis_apr'],
                                  session['monthofdiagnosis_aug'],
                                  session['monthofdiagnosis_dec'],
                                  session['monthofdiagnosis_feb'],
                                  session['monthofdiagnosis_jan'],
                                  session['monthofdiagnosis_jul'],
                                  session['monthofdiagnosis_jun'],
                                  session['monthofdiagnosis_mar'],
                                  session['monthofdiagnosis_may'],
                                  session['monthofdiagnosis_nov'],
                                  session['monthofdiagnosis_oct'],
                                  session['monthofdiagnosis_sep'],
                                  session['raceethnicity_americanindian'],
                                  session['raceethnicity_asianindian'],
                                  session['raceethnicity_black'],
                                  session['raceethnicity_chinese'],
                                  session['raceethnicity_japanese'],
                                  session['raceethnicity_melanesian'],
                                  session['raceethnicity_other'],
                                  session['raceethnicity_otherasian'],
                                  session['raceethnicity_pacific'],
                                  session['raceethnicity_thai'],
                                  session['raceethnicity_unknown'],
                                  session['raceethnicity_vietnamese'],
                                  session['raceethnicity_white'],
                                  session['seerhistoric_distant'],
                                  session['seerhistoric_in'],
                                  session['seerhistoric_localized'],
                                  session['seerhistoric_unstaged'],
                                  session['sex_female'],
                                  session['spanish_cuban'],
                                  session['spanish_mexican'],
                                  session['spanish_nonspanish'],
                                  session['spanish_other'],
                                  session['spanish_surname'],
                                  session['spanish_nos'],
                                  session['yob'],
                                  session['yod']]).astype('float')

        

        print session_data

        labels = [str(a) for a in range(120)]

        print labels

        session['labels'] = [str(a) for a in range(120)]

        print session['labels'], type(session['labels'])

        session_data_string = str(session_data)

        session['datax'] = session_data_string

        session_data_list = list(session_data)

        session['datas'] = session_data_list

        values = session_data_list

        session['values'] = session_data_list

        print values

        print session.get('datax')

        prob6, prob12, prob60, Asurv = get_survival_function(session_data)

        print prob6, prob12, prob60



        datacountscdfdict = {1: 0.015245722472745976, 2: 0.030702680859270963,
                             3: 0.045819824949716668, 4: 0.058735829590783994,
                             5: 0.073586632746464861, 6: 0.087727193409439491,
                             7: 0.10112383628910543, 8: 0.11447149692789507,
                             9: 0.12782221895673948, 10: 0.14050555795364442,
                             11: 0.15381648191177685, 12: 0.16713046725996406,
                             13: 0.17900559928241017, 14: 0.19185119195221781,
                             15: 0.20399572629948354, 16: 0.215258580310976,
                             17: 0.22812254132111226, 18: 0.23945274591380961,
                             19: 0.25174422698370419, 20: 0.26354282425478109,
                             21: 0.27542407905733673, 22: 0.28740635973169976,
                             23: 0.29985091030433275, 24: 0.31089946701199145,
                             25: 0.32215007546326485, 26: 0.33419970671883276,
                             27: 0.34547786768059907, 28: 0.35707135181800648,
                             29: 0.36840155641070382, 30: 0.37871537950521811,
                             31: 0.38991088293550569, 32: 0.4002798110510058,
                             33: 0.4106977214073822, 34: 0.42140646381896157,
                             35: 0.43196519811785733, 36: 0.44204635556820926,
                             37: 0.4525775373566121, 38: 0.46261889673625201,
                             39: 0.47357561174226764, 40: 0.48369656726333154,
                             41: 0.49348076987837092, 42: 0.50361703234970867,
                             43: 0.51399208324531831, 44: 0.52385282061172689,
                             45: 0.53389417999136679, 46: 0.54417432779527863,
                             47: 0.55368912808549842, 48: 0.56341822567955202,
                             49: 0.57296363987031951, 50: 0.58195494246117396,
                             51: 0.5922687655556883, 52: 0.60172539943486747,
                             53: 0.61060036920364069, 54: 0.61959167179449515,
                             55: 0.62942791804046561, 56: 0.63800287158387148,
                             57: 0.64713499811724517, 58: 0.65642631693346687,
                             59: 0.66509923495862533, 60: 0.67431401902347776,
                             61: 0.68188789801897443, 62: 0.69028222954914897,
                             63: 0.69914495375770314, 64: 0.70733111076415345,
                             65: 0.71604688825007867, 66: 0.72422386108636472,
                             67: 0.73229980805084338, 68: 0.73999614264853075,
                             69: 0.74850680700078653, 70: 0.75618477325814537,
                             71: 0.76445664918612921, 72: 0.77240707915836238,
                             73: 0.77920336507994792, 74: 0.78694868191851164,
                             75: 0.79485012964986856, 76: 0.80204439627857405,
                             77: 0.80895395363218603, 78: 0.81571656426316919,
                             79: 0.82254040269524764, 80: 0.82979895851510321,
                             81: 0.83686158537145361, 82: 0.84355378403117709,
                             83: 0.85082764680130651, 84: 0.85780149334606859,
                             85: 0.86434980667321792, 86: 0.87087669026998382,
                             87: 0.87745561749768086, 88: 0.88386922966242043,
                             89: 0.89055224415197953, 90: 0.89659236673003728,
                             91: 0.90284372522187406, 92: 0.90924815321644925,
                             93: 0.91531276691494523, 94: 0.92161310764765836,
                             95: 0.92822571016595778, 96: 0.93429644664456324,
                             97: 0.94026309586130663, 98: 0.94651445435314341,
                             99: 0.9524504896693391, 100: 0.95807732459000317,
                             101: 0.96405621936696562, 102: 0.96918098631864769,
                             103: 0.97483843513985946, 104: 0.9803183233378947,
                             105: 0.98532675746749554, 106: 0.99096889933843346,
                             107: 0.99567731724266706, 108: 0.99999999999999989}


        datacountscdf = pd.Series(datacountscdfdict)

        basecdf = -Asurv + 1

        print basecdf

        print datacountscdf


        def get_month_from_cdf(acdf):
            import random
            pval = random.uniform(0,100)/100.0
            #print(pval)
            if (pval <= acdf.max() + .001): 
                try:
                    return acdf[acdf <= pval].tail(1).index[0]
                except:
                    return 0
            else:
                return len(basecdf) 



        def get_one_group(acdf,numberofsubjects):
            """Returns a pandas series"""
            import random
            a = list()
            for i in range(numberofsubjects):
                try:
                    b = get_month_from_cdf(acdf)
                    a.append(b)
                except:
                    pass
            c = pd.Series(a)
            return c
            
        
        listofcurves = list()
        listofcurves.append(Asurv)


        for i in range(800):
            import random 
            numberofsubjects = get_month_from_cdf(datacountscdf) + 1
            samp1 = get_one_group(basecdf, numberofsubjects)
            samp1pmf = samp1.value_counts(normalize=True).sort_index()
            samp1cdf = samp1pmf.cumsum()
            samp1st = -samp1cdf + 1
            listofcurves.append(samp1st)
        
        
        dfhuh = pd.DataFrame.from_records(listofcurves)

        print dfhuh.shape
        
        upper = list(dfhuh.quantile(.975).values)
        lower = list(dfhuh.quantile(.025).values)
        print dfhuh.quantile(.975)
        print dfhuh.head()
        session['prob6'] = round(prob6,3)
        session['prob12'] = round(prob12,3)
        session['prob60'] = round(prob60,3)
        session['Asurv'] = [round(elem,6) for elem in Asurv]
        session['upper'] = [round(elem,6) for elem in dfhuh.quantile(.975)[:-1]]
        session['lower'] = [round(elem,6) for elem in dfhuh.quantile(.025)[:-1]]
        return render_template('results.html',
                               prob6 = session.get('prob6'),
                               prob12 = session.get('prob12'),
                               prob60 = session.get('prob60'),
                               values = session.get('Asurv'),
                               upper = session.get('upper'),
                               lower = session.get('lower'),
                                labels= ['0','','','','','','','','','',
                                    '10','','','','','','','','','',
                                    '20','','','','','','','','','',
                                    '30','','','','','','','','','',
                                    '40','','','','','','','','','',
                                    '50','','','','','','','','','',
                                    '60','','','','','','','','','',
                                    '70','','','','','','','','','',
                                    '80','','','','','','','','','',
                                    '90','','','','','','','','','',
                                         '100','','','','','','','107'])
                               
                            

    
    
    return render_template('reviewform.html',
                           form = form)



#@app.route('/user/<id>')
#def get_user(id):
#    user = str(id)
#    if user != 'Tom Brady':
#        abort(404)
#    return '<h1>Hello, %s</h1>' % 'Tom Brady'


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(505)
def internal_server_error(e):
    return render_template('500.html'), 500



        








if __name__ == '__main__':
   run_server()
   #app.run(debug=True)



